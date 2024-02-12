# -*- coding: utf-8 -*-
import logging
import unicodedata
from collections import defaultdict
from typing import Union

from fastapi_filter.contrib.sqlalchemy import Filter as SQLAlchemyFilter
from fastapi_filter.contrib.sqlalchemy.filter import _orm_operator_transformer
from pydantic import validator
from sqlalchemy import inspect, or_
from sqlalchemy.orm import InstrumentedAttribute, Query, aliased
from sqlalchemy.orm.util import AliasedClass
from sqlalchemy.sql.selectable import Select

from src.infrastructure.sqlalchemy.database import unaccent

logger = logging.getLogger(__name__)

# Add unaccent to the _orm_operator_transformer
_orm_operator_transformer["unaccent"] = lambda value: ("unaccent", value)
_orm_operator_transformer["contains"] = lambda value: ("contains", value)


class Filter(SQLAlchemyFilter):
    """
    Custom Base Filter class from fastapi_filter.contrib.sqlalchemy import Filter.
    Override the method filter due to we need add the unaccent filter.
    """

    def get_model_field(
        self, field_name: str, model_class_without_alias=None
    ) -> InstrumentedAttribute:
        """
        Create the alias to the field only if it is needed
        """
        return (
            getattr(self.Constants.model, field_name)
            if not inspect(self.Constants.model).class_ == model_class_without_alias
            else getattr(model_class_without_alias, field_name)
        )

    def get_order_by(
        self, field_name: str, model_class_without_alias=None
    ) -> InstrumentedAttribute:
        """
        Return the order by field.
        """
        if "__" in field_name:
            filter_schema = self
            related_list = field_name.split("__")
            for related_field in related_list:
                if related_field == related_list[-1] and hasattr(
                    filter_schema.Constants.model, related_field
                ):
                    continue
                if filter_schema.__fields__.get(related_field) is None:
                    raise ValueError(f"{field_name} is not a valid ordering field.")
                filter_schema = filter_schema.__fields__.get(related_field).type_
            return getattr(filter_schema.Constants.model, related_field)
        order_by_field = self.get_model_field(field_name, model_class_without_alias)
        return order_by_field

    @classmethod
    def validate_field_name(cls, field_name: str):
        """
        Validate the field name and return the field name and the model.
        """
        if "__" not in field_name and not hasattr(cls.Constants.model, field_name):
            raise ValueError(f"{field_name} is not a valid ordering field.")

        if "__" in field_name:
            filter_schema = cls
            related_list = field_name.split("__")
            for related_field in related_list:
                if related_field == related_list[-1] and hasattr(
                    filter_schema.Constants.model, related_field
                ):
                    continue
                if filter_schema.__fields__.get(related_field) is None:
                    raise ValueError(f"{field_name} is not a valid ordering field.")
                filter_schema = filter_schema.__fields__.get(related_field).type_
        return field_name

    @validator("*", allow_reuse=True, check_fields=False)
    def validate_order_by(cls, value, values, field):
        # TODO --> To be change. value here can be a filter
        if field.name != cls.Constants.ordering_field_name:
            return value

        if not value:
            return None
        field_name_usages = defaultdict(list)
        duplicated_field_names = set()

        for field_name_with_direction in value:
            field_name = field_name_with_direction.replace("-", "").replace("+", "")
            field_name = cls.validate_field_name(field_name)

            field_name_usages[field_name].append(field_name_with_direction)
            if len(field_name_usages[field_name]) > 1:
                duplicated_field_names.add(field_name)

        if duplicated_field_names:
            ambiguous_field_names = ", ".join(
                [
                    field_name_with_direction
                    for field_name in sorted(duplicated_field_names)
                    for field_name_with_direction in field_name_usages[field_name]
                ]
            )
            raise ValueError(
                f"Field names can appear at most once for {cls.Constants.ordering_field_name}. "
                f"The following was ambiguous: {ambiguous_field_names}."
            )

        return value

    @validator("*", pre=True)
    def split_str(cls, value, field):
        if (
            field.name == cls.Constants.ordering_field_name
            or field.name.endswith("__contains")
            or field.name.endswith("__in")
            or field.name.endswith("__not_in")
        ) and isinstance(value, str):
            return [field.type_(v) for v in value.split(",")]
        return value

    def filter(self, query: Union[Query, Select], model_class_without_alias=None):
        """
        Applies all the filters to the query. We had to add the model_class parameter in order
        to specify which is the class model that initiates the call to the filter method,
        otherwise when the alias was previously created that caused the query to be incorrect.
        """
        for field_name, value in self.filtering_fields:
            field_value = getattr(self, field_name)
            if isinstance(field_value, Filter):
                field_value.Constants.model = (
                    aliased(inspect(field_value.Constants.model).class_)
                    if type(field_value.Constants.model) == AliasedClass
                    else aliased(field_value.Constants.model)
                )

                query = field_value.filter(
                    query.outerjoin(
                        field_value.Constants.model,
                        self.get_model_field(field_name, model_class_without_alias),
                    )
                )
            else:
                if "__" in field_name:
                    field_name, operator = field_name.split("__")
                    operator, value = _orm_operator_transformer[operator](value)
                else:
                    operator = "__eq__"

                if field_name == self.Constants.search_field_name and hasattr(
                    self.Constants, "search_model_fields"
                ):

                    def search_filter(field):
                        return getattr(self.Constants.model, field).ilike(
                            "%" + value + "%"
                        )

                    query = query.filter(
                        or_(
                            *list(
                                map(search_filter, self.Constants.search_model_fields)
                            )
                        )
                    )
                # Start customization
                elif operator == "unaccent":
                    model_field = self.get_model_field(
                        field_name, model_class_without_alias
                    )
                    field_ascii = unicodedata.normalize("NFD", value).encode(
                        "ascii", "ignore"
                    )
                    value = field_ascii.decode("UTF-8")
                    query = query.filter(unaccent(model_field).ilike("%" + value + "%"))
                # End customization
                else:
                    model_field = self.get_model_field(
                        field_name, model_class_without_alias
                    )
                    query = query.filter(getattr(model_field, operator)(value))
        return query

    def sort(self, query: Union[Query, Select], model_class_without_alias=None):
        if not self.ordering_values:
            return query

        for field_name in self.ordering_values:
            direction = Filter.Direction.asc
            if field_name.startswith("-"):
                direction = Filter.Direction.desc
            field_name = field_name.replace("-", "").replace("+", "")

        order_by_field = self.get_order_by(field_name, model_class_without_alias)
        try:
            query = query.order_by(getattr(order_by_field, direction)())
        except NotImplementedError:
            raise ValueError(f"{field_name} is not a valid ordering field.")
        return query
