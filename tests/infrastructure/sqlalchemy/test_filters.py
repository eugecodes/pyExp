from typing import List

import pytest
from fastapi_filter import FilterDepends, with_prefix
from sqlalchemy.orm import Session, aliased

from src.infrastructure.sqlalchemy.filters import Filter
from src.modules.rates.models import RateType
from src.modules.users.models import User


class DummyUserFilter(Filter):
    first_name: str | None
    search: str | None

    class Constants(Filter.Constants):
        model = aliased(User)
        search_model_fields = ["first_name"]


class DummyRateTypeFilter(Filter):
    order_by: List[str] | None
    name__unaccent: str | None
    name: str | None
    name__ilike: str | None
    user: DummyUserFilter | None = FilterDepends(
        with_prefix("user", DummyUserFilter), use_cache=False
    )

    class Constants(Filter.Constants):
        model = RateType
        allowed_order_fields = ["name"]
        search_model_fields = ["name"]


class TestFilter:
    def test_filter_unaccent(
        self, rate_type_with_accent: RateType, db_session: Session
    ):
        rate_type_filter = DummyRateTypeFilter(name__unaccent="test")

        rate_types = rate_type_filter.filter(db_session.query(RateType))

        assert rate_types.first() == rate_type_with_accent

    def test_filter_unaccent_with_accented_search(
        self, gas_rate_type: RateType, db_session: Session
    ):
        rate_type_filter = DummyRateTypeFilter(name__unaccent="gás")

        rate_types = rate_type_filter.filter(db_session.query(RateType))

        assert rate_types.first() == gas_rate_type

    def test_filter_relationship_value(
        self, gas_rate_type: RateType, db_session: Session
    ):
        rate_type_filter = DummyRateTypeFilter(user=DummyUserFilter(first_name="John"))

        rate_types = rate_type_filter.filter(db_session.query(RateType))

        assert rate_types.first() == gas_rate_type

    def test_get_order_by_ok(self):
        dummy_rate_type_filter = DummyRateTypeFilter(order_by="name")

        dummy_rate_type_field = dummy_rate_type_filter.get_order_by("name")

        assert dummy_rate_type_field == RateType.name

    def test_get_order_by_relationship_value_ok(self):
        dummy_rate_type_filter = DummyRateTypeFilter(order_by="user__first_name")

        dummy_rate_type_user_field = dummy_rate_type_filter.get_order_by(
            "user__first_name"
        )

        assert dummy_rate_type_user_field == DummyUserFilter.Constants.model.first_name

    def test_get_order_by_relationship_value_error(self):
        dummy_rate_type_filter = DummyRateTypeFilter(order_by="user__first_name")
        with pytest.raises(ValueError) as exc:
            dummy_rate_type_filter.get_order_by("invalid_field__first_name")

        assert (
            exc.value.args[0]
            == "invalid_field__first_name is not a valid ordering field."
        )

    def test_validate_field_name_direct_not_valid_field(self):
        with pytest.raises(ValueError) as exc:
            DummyRateTypeFilter(order_by="not_valid_field")

        assert exc.value.errors()[0]["type"] == "value_error"
        assert (
            exc.value.errors()[0]["msg"]
            == "not_valid_field is not a valid ordering field."
        )

    def test_validate_field_name_not_valid_field_foreign_key(self):
        with pytest.raises(ValueError) as exc:
            DummyRateTypeFilter(order_by="not_valid_foreign_key_field__not_valid_field")

        assert exc.value.errors()[0]["type"] == "value_error"
        assert (
            exc.value.errors()[0]["msg"]
            == "not_valid_foreign_key_field__not_valid_field is not a valid ordering field."
        )

    def test_validate_field_name_not_valid_field_in_foreign_key(self):
        with pytest.raises(ValueError) as exc:
            DummyRateTypeFilter(order_by="user__not_valid_field")

        assert exc.value.errors()[0]["type"] == "value_error"
        assert (
            exc.value.errors()[0]["msg"]
            == "user__not_valid_field is not a valid ordering field."
        )

    def test_validate_order_by_duplicate_fields(self):
        with pytest.raises(ValueError) as exc:
            DummyRateTypeFilter(order_by="user__first_name,user__first_name")

        assert exc.value.errors()[0]["type"] == "value_error"
        assert exc.value.errors()[0]["msg"] == (
            "Field names can appear at most once for order_by. "
            "The following was ambiguous: user__first_name, user__first_name."
        )

    def test_sort_by_name_ok(
        self,
        electricity_rate_type: RateType,
        gas_rate_type: RateType,
        disable_rate_type: RateType,
        db_session: Session,
    ):
        rate_type_filter = DummyRateTypeFilter(order_by="name")

        rate_types = rate_type_filter.sort(db_session.query(RateType))

        response = rate_types.all()
        assert rate_types.count() == 3
        assert response[0].name == "Disable rate type"
        assert response[1].name == "Electricity rate type"
        assert response[2].name == "Gas rate type"

    def test_sort_by_name_desc(
        self,
        electricity_rate_type: RateType,
        gas_rate_type: RateType,
        disable_rate_type: RateType,
        db_session: Session,
    ):
        rate_type_filter = DummyRateTypeFilter(order_by="-+name")

        rate_types = rate_type_filter.sort(db_session.query(RateType))

        response = rate_types.all()
        assert rate_types.count() == 3
        assert response[0].name == "Gas rate type"
        assert response[1].name == "Electricity rate type"
        assert response[2].name == "Disable rate type"

    def test_sort_by_foreign_key_error(
        self,
        electricity_rate_type: RateType,
        gas_rate_type: RateType,
        disable_rate_type: RateType,
        db_session: Session,
    ):
        rate_type_filter = DummyRateTypeFilter(order_by="user")

        with pytest.raises(ValueError) as exc:
            rate_type_filter.sort(db_session.query(RateType))

        assert exc.value.args[0] == "user is not a valid ordering field."

    def test_filter_search_foreign_key_name_ok(
        self,
        electricity_rate_type: RateType,
        gas_rate_type: RateType,
        disable_rate_type: RateType,
        superadmin: User,
        user_create2: User,
        db_session: Session,
    ):
        gas_rate_type.user = superadmin
        disable_rate_type.user = user_create2

        rate_type_filter = DummyRateTypeFilter(user=DummyUserFilter(search="john"))

        rate_types = rate_type_filter.filter(db_session.query(RateType))

        response = rate_types.all()
        assert rate_types.count() == 2
        assert response[0].name == "Electricity rate type"
        assert response[0].user.first_name == "John"
        assert response[1].user.first_name == "Johnathan"
