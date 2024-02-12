from datetime import datetime
from typing import List

from pydantic import BaseModel, constr, validator

from src.infrastructure.sqlalchemy.filters import Filter
from src.modules.clients.models import Client, InvoiceNotificationType
from src.modules.contacts.schemas import ContactInlineCreateRequest
from src.modules.rates.models import ClientType
from src.modules.users.schemas import BaseUserResponsible
from src.services.common import empty_string_to_none
from utils.i18n import trans as _


class ClientBasicResponse(BaseModel):
    id: int
    fiscal_name: constr(max_length=64)
    cif: constr(max_length=9)
    alias: constr(max_length=64) | None

    class Config:
        orm_mode = True


class ClientCreateRequest(BaseModel):
    alias: constr(max_length=64) | None
    client_type: ClientType
    fiscal_name: constr(max_length=64)
    cif: constr(max_length=9)
    main_contact: ContactInlineCreateRequest
    invoice_notification_type: InvoiceNotificationType
    invoice_email: constr(
        strip_whitespace=True,
        to_lower=True,
        max_length=256,
        regex=(r"^(?:\w+[+\-\.])*\w+@(?:\w+[\-\.])*\w+\.\w+$"),  # noqa F722
    ) | None
    invoice_postal: constr(max_length=256) | None
    bank_account_holder: constr(max_length=64)
    bank_account_number: constr(max_length=64)
    fiscal_address: constr(max_length=256)
    is_renewable: bool

    _empty_string_to_none = validator(
        "fiscal_name",
        "cif",
        "invoice_email",
        "invoice_postal",
        "bank_account_holder",
        "bank_account_number",
        "fiscal_address",
        allow_reuse=True,
        pre=True,
    )(empty_string_to_none)

    class Config:
        orm_mode = True


class ClientCreateResponse(BaseModel):
    id: int
    is_active: bool
    create_at: datetime
    alias: constr(max_length=64) | None
    client_type: ClientType
    fiscal_name: constr(max_length=64)
    cif: constr(max_length=9)
    invoice_notification_type: InvoiceNotificationType
    invoice_email: constr(
        strip_whitespace=True,
        to_lower=True,
        max_length=256,
        regex=(r"^(?:\w+[+\-\.])*\w+@(?:\w+[\-\.])*\w+\.\w+$"),  # noqa F722
    ) | None
    invoice_postal: constr(max_length=256) | None
    bank_account_holder: constr(max_length=64)
    bank_account_number: constr(max_length=64)
    fiscal_address: constr(max_length=256)
    is_renewable: bool

    class Config:
        orm_mode = True


class ClientPartialUpdateRequest(BaseModel):
    is_active: bool | None

    class Config:
        orm_mode = True


class ClientUpdateRequest(BaseModel):
    alias: constr(max_length=64)
    client_type: ClientType
    fiscal_name: constr(max_length=64)
    cif: constr(max_length=9)
    invoice_notification_type: InvoiceNotificationType
    invoice_email: constr(
        strip_whitespace=True,
        to_lower=True,
        max_length=256,
        regex=(r"^(?:\w+[+\-\.])*\w+@(?:\w+[\-\.])*\w+\.\w+$"),  # noqa F722
    ) | None
    invoice_postal: constr(max_length=256) | None
    bank_account_holder: constr(max_length=64)
    bank_account_number: constr(max_length=64)
    fiscal_address: constr(max_length=256)
    is_renewable: bool

    _empty_string_to_none = validator(
        "fiscal_name",
        "cif",
        "invoice_email",
        "invoice_postal",
        "bank_account_holder",
        "bank_account_number",
        "fiscal_address",
        allow_reuse=True,
        pre=True,
    )(empty_string_to_none)

    class Config:
        orm_mode = True


class ClientUpdateDetailResponse(ClientCreateResponse):
    alias: constr(max_length=64)
    client_type: ClientType
    fiscal_name: constr(max_length=64)
    cif: constr(max_length=9)
    invoice_notification_type: InvoiceNotificationType
    invoice_email: constr(
        strip_whitespace=True,
        to_lower=True,
        max_length=256,
        regex=(r"^(?:\w+[+\-\.])*\w+@(?:\w+[\-\.])*\w+\.\w+$"),  # noqa F722
    ) | None
    invoice_postal: constr(max_length=256) | None
    bank_account_holder: constr(max_length=64)
    bank_account_number: constr(max_length=64)
    fiscal_address: constr(max_length=256)
    is_renewable: bool


class ClientListResponse(BaseModel):
    id: int
    is_active: bool
    alias: constr(max_length=64)
    client_type: ClientType
    fiscal_name: constr(max_length=64)
    cif: constr(max_length=9)
    invoice_notification_type: InvoiceNotificationType
    invoice_email: constr(
        strip_whitespace=True,
        to_lower=True,
        max_length=256,
        regex=(r"^(?:\w+[+\-\.])*\w+@(?:\w+[\-\.])*\w+\.\w+$"),  # noqa F722
    ) | None
    invoice_postal: constr(max_length=256) | None
    bank_account_holder: constr(max_length=64)
    bank_account_number: constr(max_length=64)
    fiscal_address: constr(max_length=256)
    is_renewable: bool
    create_at: datetime
    user: BaseUserResponsible

    class Config:
        orm_mode = True


class ClientDeleteRequest(BaseModel):
    ids: list[int]


class ClientBaseFilter(Filter):
    id: int | None
    name__unaccent: str | None
    order_by: List[str] = ["-create_at"]

    class Constants(Filter.Constants):
        model = Client


class ClientFilter(ClientBaseFilter):
    id__in: list[int] | None
    fiscal_name__unaccent: str | None
    is_active: bool | None
    create_at__gte: datetime | None
    create_at__lt: datetime | None


client_export_headers = {
    "id": _("Id"),
    "alias": _("Alias"),
    "fiscal_name": _("Fiscal Name"),
    "is_active": _("Is active"),
    "cif": _("Cif"),
    "invoice_notification_type": _("Invoice notification type"),
    "invoice_email": _("Invoice email"),
    "invoice_postal": _("Invoice postal"),
    "create_at": _("Date"),
}
