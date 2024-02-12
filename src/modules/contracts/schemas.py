from datetime import date, datetime
from typing import List

from pydantic import BaseModel, condecimal, constr, validator

from src.infrastructure.sqlalchemy.filters import Filter
from src.modules.contracts.models import Contract, ContractStatusEnum
from src.modules.rates.schemas import RelatedRateResponse
from src.modules.supply_points.schemas import SupplyPointRelatedResponse
from src.modules.users.schemas import BaseUserResponsible
from src.services.common import empty_string_to_none
from utils.i18n import trans as _
from utils.regex import EMAIL_REGEX, PHONE_REGEX


class ContractCreateRequest(BaseModel):
    supply_point_id: int
    rate_id: int
    power_1: condecimal(decimal_places=2, ge=0) | None
    power_2: condecimal(decimal_places=2, ge=0) | None
    power_3: condecimal(decimal_places=2, ge=0) | None
    power_4: condecimal(decimal_places=2, ge=0) | None
    power_5: condecimal(decimal_places=2, ge=0) | None
    power_6: condecimal(decimal_places=2, ge=0) | None
    start_date: date | None
    end_date: date | None
    expected_end_date: date | None
    preferred_start_date: date | None
    period: int | None
    signature_first_name: constr(max_length=64)
    signature_last_name: constr(max_length=64)
    signature_dni: constr(max_length=64)
    signature_email: constr(
        strip_whitespace=True,
        to_lower=True,
        max_length=256,
        regex=EMAIL_REGEX,
    )
    signature_phone: constr(
        strip_whitespace=True,
        to_lower=True,
        max_length=50,
        regex=PHONE_REGEX,
    )

    _empty_string_to_none = validator(
        "signature_first_name",
        "signature_last_name",
        "signature_dni",
        "signature_email",
        "signature_phone",
        allow_reuse=True,
        pre=True,
    )(empty_string_to_none)

    class Config:
        orm_mode = True


class ContractCreateResponse(ContractCreateRequest):
    id: int
    is_active: bool
    create_at: datetime
    status: ContractStatusEnum

    supply_point: SupplyPointRelatedResponse
    rate: RelatedRateResponse


class ContractPartialUpdateRequest(BaseModel):
    is_active: bool | None
    status: ContractStatusEnum
    status_message: constr(max_length=256) | None

    class Config:
        orm_mode = True


class ContractUpdateRequest(BaseModel):
    rate_id: int
    status: ContractStatusEnum
    power_1: condecimal(decimal_places=2, ge=0) | None
    power_2: condecimal(decimal_places=2, ge=0) | None
    power_3: condecimal(decimal_places=2, ge=0) | None
    power_4: condecimal(decimal_places=2, ge=0) | None
    power_5: condecimal(decimal_places=2, ge=0) | None
    power_6: condecimal(decimal_places=2, ge=0) | None
    start_date: date | None
    end_date: date | None
    expected_end_date: date | None
    preferred_start_date: date | None
    period: int | None
    signature_first_name: constr(max_length=64)
    signature_last_name: constr(max_length=64)
    signature_dni: constr(max_length=64)
    signature_email: constr(
        strip_whitespace=True,
        to_lower=True,
        max_length=256,
        regex=EMAIL_REGEX,
    )
    signature_phone: constr(
        strip_whitespace=True,
        to_lower=True,
        max_length=50,
        regex=PHONE_REGEX,
    )

    _empty_string_to_none = validator(
        "signature_first_name",
        "signature_last_name",
        "signature_dni",
        "signature_email",
        "signature_phone",
        allow_reuse=True,
        pre=True,
    )(empty_string_to_none)

    class Config:
        orm_mode = True


class ContractUpdateDetailResponse(ContractCreateResponse):
    user: BaseUserResponsible
    status_message: constr(max_length=256) | None


class ContractListResponse(BaseModel):
    id: int
    is_active: bool
    create_at: datetime
    status: ContractStatusEnum

    supply_point: SupplyPointRelatedResponse
    rate: RelatedRateResponse
    user: BaseUserResponsible

    start_date: date | None
    end_date: date | None
    expected_end_date: date
    preferred_start_date: date

    class Config:
        orm_mode = True


class ContractDeleteRequest(BaseModel):
    ids: list[int]


class ContractBaseFilter(Filter):
    id: int | None
    order_by: List[str] = ["-create_at"]

    class Constants(Filter.Constants):
        model = Contract


class ContractFilter(ContractBaseFilter):
    id__in: list[int] | None
    is_active: bool | None
    create_at__gte: datetime | None
    create_at__lt: datetime | None


client_export_headers = {
    "id": _("Id"),
    "is_active": _("Is active"),
    "create_at": _("Date"),
}
