from datetime import datetime
from typing import List

from fastapi_filter import FilterDepends, with_prefix
from pydantic import BaseModel, condecimal, constr, validator

from src.infrastructure.sqlalchemy.filters import Filter
from src.modules.marketers.models import Marketer
from src.modules.users.schemas import BaseUserResponsible, RelatedUserFilter
from src.services.common import empty_string_to_none
from utils.i18n import trans as _


class MarketerBasicResponse(BaseModel):
    id: int
    name: constr(max_length=64)

    class Config:
        orm_mode = True


class MarketerCreateRequest(BaseModel):
    name: constr(max_length=64)
    fiscal_name: constr(max_length=64) | None
    cif: constr(max_length=9) | None
    email: constr(
        strip_whitespace=True,
        to_lower=True,
        max_length=256,
        regex=(r"^(?:\w+[+\-\.])*\w+@(?:\w+[\-\.])*\w+\.\w+$"),  # noqa F722
    ) | None

    _empty_string_to_none = validator(
        "fiscal_name", "cif", "email", allow_reuse=True, pre=True
    )(empty_string_to_none)

    class Config:
        orm_mode = True


class MarketerCreateResponse(MarketerCreateRequest):
    id: int
    is_active: bool
    create_at: datetime


class AddressUpdateRequest(BaseModel):
    type: constr(max_length=16) | None
    name: constr(max_length=128) | None
    number: int | None
    subdivision: constr(max_length=64) | None
    others: constr(max_length=64) | None
    postal_code: constr(max_length=16) | None
    city: constr(max_length=64) | None
    province: constr(max_length=64) | None

    class Config:
        orm_mode = True


class AddressUpdateResponse(AddressUpdateRequest):
    id: int


class MarketerPartialUpdateRequest(BaseModel):
    is_active: bool | None
    is_deleted: bool | None

    class Config:
        orm_mode = True


class MarketerUpdateRequest(BaseModel):
    name: constr(max_length=64)
    fiscal_name: constr(max_length=64) | None
    cif: constr(max_length=9) | None
    email: constr(
        strip_whitespace=True,
        to_lower=True,
        max_length=256,
        regex=(r"^(?:\w+[+\-\.])*\w+@(?:\w+[\-\.])*\w+\.\w+$"),  # noqa F722
    ) | None
    fee: condecimal(max_digits=14, decimal_places=6) | None
    max_consume: condecimal(max_digits=12, decimal_places=2) | None
    consume_range_datetime: datetime | None
    surplus_price: condecimal(max_digits=14, decimal_places=6) | None
    address: AddressUpdateRequest | None

    _empty_string_to_none = validator(
        "fiscal_name", "cif", "email", allow_reuse=True, pre=True
    )(empty_string_to_none)

    class Config:
        orm_mode = True


class MarketerUpdateDetailResponse(MarketerCreateResponse):
    fee: condecimal(max_digits=14, decimal_places=6) | None
    max_consume: condecimal(max_digits=12, decimal_places=2) | None
    consume_range_datetime: datetime | None
    surplus_price: condecimal(max_digits=14, decimal_places=6) | None
    is_deleted: bool
    address: AddressUpdateResponse | None
    user: BaseUserResponsible


class MarketerListResponse(BaseModel):
    id: int
    name: constr(max_length=64)
    fiscal_name: constr(max_length=64) | None
    is_active: bool
    create_at: datetime
    user: BaseUserResponsible

    class Config:
        orm_mode = True


class MarketerDeleteRequest(BaseModel):
    ids: list[int]


class MarketerBaseFilter(Filter):
    id: int | None
    name__unaccent: str | None
    order_by: List[str] = ["-create_at"]

    class Constants(Filter.Constants):
        model = Marketer


class MarketerFilter(MarketerBaseFilter):
    id__in: list[int] | None
    fiscal_name__unaccent: str | None
    is_active: bool | None
    create_at__gte: datetime | None
    create_at__lt: datetime | None
    user: RelatedUserFilter | None = FilterDepends(
        with_prefix("user", RelatedUserFilter), use_cache=False
    )


marketer_export_headers = {
    "id": _("Id"),
    "name": _("Name"),
    "fiscal_name": _("Fiscal Name"),
    "is_active": _("Is active"),
    "user.first_name": _("User first name"),
    "user.last_name": _("User last name"),
    "create_at": _("Date"),
}
