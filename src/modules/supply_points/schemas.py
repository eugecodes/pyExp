from datetime import datetime
from typing import List

from pydantic import BaseModel, condecimal, conint, constr, validator

from src.infrastructure.sqlalchemy.filters import Filter
from src.modules.clients.schemas import ClientBasicResponse
from src.modules.rates.models import EnergyType
from src.modules.supply_points.models import CounterType, OwnerType, SupplyPoint
from src.modules.users.schemas import BaseUserResponsible
from src.services.common import empty_string_to_none
from utils.i18n import trans as _


class SupplyPointBasicResponse(BaseModel):
    id: int

    class Config:
        orm_mode = True


class SupplyPointCreateRequest(BaseModel):
    client_id: int
    energy_type: EnergyType
    cups: constr(min_length=20, max_length=22)
    alias: constr(max_length=64) | None

    # Address
    supply_address: constr(max_length=256)
    supply_postal_code: constr(max_length=10)
    supply_city: constr(max_length=256)
    supply_province: constr(max_length=256)

    # Finance Information
    bank_account_holder: constr(max_length=64) | None
    bank_account_number: constr(max_length=64) | None
    fiscal_address: constr(max_length=256) | None

    # Technical information
    is_renewable: bool
    max_available_power: conint(gt=0) | None
    voltage: conint(gt=0) | None

    # Counter
    counter_type: CounterType | None
    counter_property: OwnerType | None
    counter_price: condecimal(decimal_places=6, ge=0) | None

    _empty_string_to_none = validator(
        "supply_address",
        "supply_postal_code",
        "supply_city",
        "supply_province",
        "bank_account_holder",
        "bank_account_number",
        "fiscal_address",
        allow_reuse=True,
        pre=True,
    )(empty_string_to_none)

    class Config:
        orm_mode = True


class SupplyPointCreateResponse(SupplyPointCreateRequest):
    id: int
    is_active: bool
    create_at: datetime


class SupplyPointListResponse(BaseModel):
    id: int
    is_active: bool
    create_at: datetime

    energy_type: EnergyType
    cups: constr(min_length=20, max_length=22)
    alias: constr(max_length=64) | None

    # Address
    supply_address: constr(max_length=256)
    supply_postal_code: constr(max_length=10)
    supply_city: constr(max_length=256)
    supply_province: constr(max_length=256)

    # Finance Information
    bank_account_holder: constr(max_length=64) | None
    bank_account_number: constr(max_length=64) | None
    fiscal_address: constr(max_length=256) | None

    # Technical information
    is_renewable: bool
    max_available_power: conint(gt=0) | None
    voltage: conint(gt=0) | None

    # Counter
    counter_type: CounterType | None
    counter_property: OwnerType | None
    counter_price: condecimal(decimal_places=6, ge=0) | None

    user: BaseUserResponsible | None
    client: ClientBasicResponse | None

    class Config:
        orm_mode = True


class SupplyPointBaseFilter(Filter):
    id: int | None
    order_by: List[str] = ["-create_at"]
    client_id: int | None

    class Constants(Filter.Constants):
        model = SupplyPoint


class SupplyPointFilter(SupplyPointBaseFilter):
    id__in: list[int] | None
    is_active: bool | None
    create_at__gte: datetime | None
    create_at__lt: datetime | None


class SupplyPointUpdateRequest(BaseModel):
    energy_type: EnergyType
    cups: constr(min_length=20, max_length=22)
    alias: constr(max_length=64) | None

    # Address
    supply_address: constr(max_length=256)
    supply_postal_code: constr(max_length=10)
    supply_city: constr(max_length=256)
    supply_province: constr(max_length=256)

    # Finance Information
    bank_account_holder: constr(max_length=64) | None
    bank_account_number: constr(max_length=64) | None
    fiscal_address: constr(max_length=256) | None

    # Technical information
    is_renewable: bool
    max_available_power: conint(gt=0) | None
    voltage: conint(gt=0) | None

    # Counter
    counter_type: CounterType | None
    counter_property: OwnerType | None
    counter_price: condecimal(decimal_places=6, ge=0) | None

    _empty_string_to_none = validator(
        "supply_address",
        "supply_postal_code",
        "supply_city",
        "supply_province",
        "bank_account_holder",
        "bank_account_number",
        "fiscal_address",
        allow_reuse=True,
        pre=True,
    )(empty_string_to_none)

    class Config:
        orm_mode = True


class SupplyPointPartialUpdateRequest(BaseModel):
    is_active: bool | None

    class Config:
        orm_mode = True


class SupplyPointUpdateDetailResponse(SupplyPointCreateResponse):
    user: BaseUserResponsible | None
    client: ClientBasicResponse | None


class SupplyPointDeleteRequest(BaseModel):
    ids: list[int]


class SupplyPointRelatedResponse(BaseModel):
    id: int
    is_active: bool

    energy_type: EnergyType
    cups: constr(min_length=20, max_length=22)
    alias: constr(max_length=64) | None

    # Address
    supply_address: constr(max_length=256)
    supply_postal_code: constr(max_length=10)
    supply_city: constr(max_length=256)
    supply_province: constr(max_length=256)

    # Finance Information
    bank_account_holder: constr(max_length=64) | None
    bank_account_number: constr(max_length=64) | None
    fiscal_address: constr(max_length=256) | None

    # Technical information
    is_renewable: bool
    max_available_power: conint(gt=0) | None
    voltage: conint(gt=0) | None

    # Counter
    counter_type: CounterType | None
    counter_property: OwnerType | None
    counter_price: condecimal(decimal_places=6, ge=0) | None

    client: ClientBasicResponse | None

    class Config:
        orm_mode = True


supply_point_export_headers = {
    "id": _("Id"),
    "is_active": _("Is active"),
    "cups": _("Cups"),
    "alias": _("Alias"),
    "supply_address": _("Supply Address"),
    "create_at": _("Date"),
}
