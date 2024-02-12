from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi_filter import FilterDepends, with_prefix
from pydantic import BaseModel, Field, condecimal, conlist, constr, validator

from src.infrastructure.sqlalchemy.filters import Filter
from src.modules.costs.models import EnergyCost, OtherCost, OtherCostType
from src.modules.rates.models import ClientType
from src.modules.rates.schemas import (
    RelatedRateIdResponse,
    RelatedRateResponseOtherCost,
    RelatedRatesFilter,
)
from src.modules.users.schemas import RelatedUserFilter, UserMeDetailResponse
from src.services.common import order_client_types
from utils.i18n import trans as _


class EnergyCostCreateRequest(BaseModel):
    concept: str
    amount: condecimal(max_digits=14, decimal_places=6, ge=0)
    is_active: Optional[bool] = Field(default=True)

    class Config:
        orm_mode = True


class CostInfo(BaseModel):
    id: int
    concept: str
    amount: Optional[Decimal]
    is_active: bool
    create_at: datetime
    user: UserMeDetailResponse
    is_protected: bool
    is_deleted: bool = False

    class Config:
        orm_mode = True


class EnergyCostFilter(Filter):
    id: Optional[int]
    id__in: list[int] | None
    concept__unaccent: Optional[str]
    amount: Optional[Decimal]
    amount__gte: Optional[Decimal]
    amount__lte: Optional[Decimal]
    is_active: Optional[bool]
    create_at__gte: Optional[datetime]
    create_at__lte: Optional[datetime]
    user: Optional[RelatedUserFilter] = FilterDepends(
        with_prefix("user", RelatedUserFilter), use_cache=False
    )
    order_by: List[str] = ["-id"]

    class Constants(Filter.Constants):
        model = EnergyCost


class EnergyCostUpdatePartialRequest(BaseModel):
    concept: Optional[str]
    amount: Optional[condecimal(max_digits=14, decimal_places=6, ge=0)]
    is_active: Optional[bool]
    is_deleted: Optional[bool] = False


class EnergyCostAmountRangeResponse(BaseModel):
    minimum_amount: condecimal(decimal_places=6) | None
    maximum_amount: condecimal(decimal_places=6) | None


energy_cost_export_headers = {
    "id": _("Id"),
    "concept": _("Concept"),
    "amount": _("Amount"),
    "is_active": _("Is active"),
    "user.first_name": _("User first name"),
    "user.last_name": _("User last name"),
    "create_at": _("Date"),
}


class OtherCostBase(BaseModel):
    name: constr(max_length=124)
    mandatory: bool
    client_types: conlist(ClientType, min_items=1, max_items=4)
    min_power: condecimal(ge=0, decimal_places=2) | None
    max_power: condecimal(ge=0, decimal_places=2) | None
    type: OtherCostType
    quantity: condecimal(ge=0, decimal_places=2)
    extra_fee: condecimal(ge=0, decimal_places=2) | None

    class Config:
        orm_mode = True


class OtherCostCreateUpdateRequest(OtherCostBase):
    rates: conlist(int, min_items=1, unique_items=True)

    _order_client_types = validator("client_types", allow_reuse=True)(
        order_client_types
    )


class OtherCostCreateResponse(OtherCostBase):
    id: int
    create_at: datetime
    is_active: bool
    is_deleted: bool
    rates: conlist(RelatedRateIdResponse, min_items=1, unique_items=True)


class OtherCostUpdateListDetailResponse(OtherCostBase):
    id: int
    create_at: datetime
    is_active: bool
    is_deleted: bool
    rates: conlist(RelatedRateResponseOtherCost, min_items=1, unique_items=True)


class OtherCostPartialUpdateRequest(BaseModel):
    is_active: bool | None
    is_deleted: bool | None

    class Config:
        orm_mode = True


class CostDeleteRequest(BaseModel):
    ids: list[int]


class OtherCostFilter(Filter):
    id: int | None
    id__in: list[int] | None
    name__unaccent: str | None
    mandatory: bool | None
    client_types: list[ClientType] | None
    client_types__contains: list[str] | None
    min_power__gte: condecimal(ge=0, decimal_places=2) | None
    min_power__lte: condecimal(ge=0, decimal_places=2) | None
    max_power__gte: condecimal(ge=0, decimal_places=2) | None
    max_power__lte: condecimal(ge=0, decimal_places=2) | None
    type: OtherCostType | None
    quantity__gte: condecimal(ge=0, decimal_places=2) | None
    quantity__lte: condecimal(ge=0, decimal_places=2) | None
    extra_fee__gte: condecimal(ge=0, decimal_places=2) | None
    extra_fee__lte: condecimal(ge=0, decimal_places=2) | None
    create_at__gte: datetime | None
    create_at__lt: datetime | None
    rates: RelatedRatesFilter | None = FilterDepends(
        with_prefix("rates", RelatedRatesFilter), use_cache=False
    )

    order_by: List[str] = ["-id"]

    class Constants(Filter.Constants):
        model = OtherCost


other_cost_export_headers = {
    "id": _("Id"),
    "is_active": _("Is active"),
    "rates:name": _("Rates"),
    "name": _("Name"),
    "mandatory": _("Mandatory"),
    "client_types": _("Client types"),
    "min_power": _("Minimum power"),
    "max_power": _("Maximum power"),
    "type": _("Type"),
    "quantity": _("Quantity"),
    "extra_fee": _("Extra fee"),
    "create_at": _("Date"),
}
