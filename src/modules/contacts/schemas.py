from datetime import datetime
from typing import List

from pydantic import BaseModel, constr, validator

from src.infrastructure.sqlalchemy.filters import Filter
from src.modules.contacts.models import Contact
from src.modules.users.schemas import BaseUserResponsible
from src.services.common import empty_string_to_none
from utils.i18n import trans as _


class ContactInlineCreateRequest(BaseModel):
    name: constr(max_length=128)
    email: constr(
        strip_whitespace=True,
        to_lower=True,
        max_length=256,
        regex=(r"^(?:\w+[+\-\.])*\w+@(?:\w+[\-\.])*\w+\.\w+$"),  # noqa F722
    ) | None
    phone: constr(max_length=30)

    class Config:
        orm_mode = True


class ContactCreateRequest(BaseModel):
    name: constr(max_length=128)
    email: constr(
        strip_whitespace=True,
        to_lower=True,
        max_length=256,
        regex=(r"^(?:\w+[+\-\.])*\w+@(?:\w+[\-\.])*\w+\.\w+$"),  # noqa F722
    ) | None
    phone: constr(max_length=30)
    is_main_contact: bool
    client_id: int

    class Config:
        orm_mode = True


class ContactInlineCreateResponse(ContactInlineCreateRequest):
    id: int
    is_active: bool
    create_at: datetime


class ContactCreateResponse(ContactCreateRequest):
    id: int
    client_id: int
    is_active: bool
    create_at: datetime


class ContactListResponse(BaseModel):
    id: int
    client_id: int
    is_active: bool
    name: constr(max_length=128)
    email: constr(
        strip_whitespace=True,
        to_lower=True,
        max_length=256,
        regex=(r"^(?:\w+[+\-\.])*\w+@(?:\w+[\-\.])*\w+\.\w+$"),  # noqa F722
    ) | None
    phone: constr(max_length=30)
    is_main_contact: bool
    create_at: datetime
    user: BaseUserResponsible

    class Config:
        orm_mode = True


class ContactPartialUpdateRequest(BaseModel):
    is_active: bool | None

    class Config:
        orm_mode = True


class ContactUpdateRequest(BaseModel):
    name: constr(max_length=128)
    email: constr(
        strip_whitespace=True,
        to_lower=True,
        max_length=256,
        regex=(r"^(?:\w+[+\-\.])*\w+@(?:\w+[\-\.])*\w+\.\w+$"),  # noqa F722
    ) | None
    phone: constr(max_length=30)
    is_main_contact: bool

    _empty_string_to_none = validator(
        "name",
        "email",
        "phone",
        allow_reuse=True,
        pre=True,
    )(empty_string_to_none)

    class Config:
        orm_mode = True


class ContactUpdateDetailResponse(ContactCreateResponse):
    name: constr(max_length=128)
    email: constr(
        strip_whitespace=True,
        to_lower=True,
        max_length=256,
        regex=(r"^(?:\w+[+\-\.])*\w+@(?:\w+[\-\.])*\w+\.\w+$"),  # noqa F722
    ) | None
    phone: constr(max_length=30)
    is_main_contact: bool


class ContactDeleteRequest(BaseModel):
    ids: list[int]


class ContactBaseFilter(Filter):
    id: int | None
    name__unaccent: str | None
    order_by: List[str] = ["-create_at"]

    class Constants(Filter.Constants):
        model = Contact


class ContactFilter(ContactBaseFilter):
    id__in: list[int] | None
    name__unaccent: str | None
    email__unaccent: str | None
    phone__unaccent: str | None
    is_active: bool | None
    create_at__gte: datetime | None
    create_at__lt: datetime | None
    client_id: int


contact_export_headers = {
    "id": _("Id"),
    "name": _("name"),
    "email": _("Email"),
    "phone": _("Phone"),
    "is_active": _("Is active"),
    "is_main_contact": _("Is main contact"),
    "create_at": _("Date"),
}
