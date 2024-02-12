from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status
from fastapi_filter import FilterDepends, with_prefix
from pydantic import (
    BaseModel,
    Field,
    condecimal,
    conint,
    constr,
    root_validator,
    validator,
)

from src.infrastructure.sqlalchemy.filters import Filter
from src.modules.marketers.schemas import MarketerBaseFilter, MarketerBasicResponse
from src.modules.rates.models import ClientType, EnergyType, PriceType, Rate, RateType
from src.modules.users.schemas import RelatedUserFilter, UserMeDetailResponse
from src.services.common import order_client_types
from utils.i18n import trans as _


class RateTypeCreateRequest(BaseModel):
    name: str
    energy_type: EnergyType
    max_power: Optional[condecimal(max_digits=10, decimal_places=2, ge=Decimal("0"))]
    min_power: Optional[condecimal(max_digits=10, decimal_places=2, ge=Decimal("0"))]
    enable: Optional[bool] = Field(default=True)

    class Config:
        orm_mode = True

    @root_validator(pre=True)
    def validate_electricity_power(cls, values: dict):
        if values.get("energy_type") == EnergyType.electricity:
            if (
                values.get("max_power") is None and values.get("min_power") is not None
            ) or (
                values.get("max_power") is not None and values.get("min_power") is None
            ):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="value_error.power_range.invalid",
                )
            if (
                values.get("max_power") is not None
                and values.get("min_power") is not None
                and values.get("max_power") < values.get("min_power")
            ):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="value_error.power_range.invalid_range",
                )
        if values.get("energy_type") == EnergyType.gas and (
            values.get("max_power") is not None or values.get("min_power") is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="value_error.energy_type.invalid",
            )

        return values


class RateTypeInfo(BaseModel):
    id: int
    name: str
    energy_type: EnergyType
    max_power: Optional[Decimal]
    min_power: Optional[Decimal]
    enable: bool
    is_deleted: bool
    create_at: datetime
    user: UserMeDetailResponse

    class Config:
        orm_mode = True


class RateTypeBasicResponse(BaseModel):
    id: int
    name: str
    energy_type: EnergyType

    class Config:
        orm_mode = True


class RateTypeFilter(Filter):
    id: Optional[int]
    id__in: list[int] | None
    name__unaccent: Optional[str]
    energy_type: Optional[EnergyType]
    min_power__gte: Optional[Decimal]
    max_power__lte: Optional[Decimal]
    enable: Optional[bool]
    is_deleted: Optional[bool]
    create_at: Optional[datetime]
    create_at__gte: Optional[datetime]
    create_at__lt: Optional[datetime]
    user: Optional[RelatedUserFilter] = FilterDepends(
        with_prefix("user", RelatedUserFilter), use_cache=False
    )

    order_by: List[str] = ["-id"]

    class Constants(Filter.Constants):
        model = RateType


class RateTypeUpdatePartialRequest(BaseModel):
    max_power: Optional[condecimal(max_digits=10, decimal_places=2, ge=Decimal("0"))]
    min_power: Optional[condecimal(max_digits=10, decimal_places=2, ge=Decimal("0"))]
    enable: Optional[bool]
    is_deleted: Optional[bool]


class RateTypePowerRangesResponse(BaseModel):
    minimum_min_power: condecimal(decimal_places=2) | None
    maximum_min_power: condecimal(decimal_places=2) | None
    minimum_max_power: condecimal(decimal_places=2) | None
    maximum_max_power: condecimal(decimal_places=2) | None


rate_type_export_headers = {
    "id": _("Id"),
    "name": _("Name"),
    "energy_type": _("Energy type"),
    "max_power": _("Minimum power"),
    "min_power": _("Maximum power"),
    "enable": _("Enable"),
    "user.first_name": _("User first name"),
    "user.last_name": _("User last name"),
    "create_at": _("Date"),
}


class RateCreateRequest(BaseModel):
    name: constr(max_length=64)
    price_type: PriceType
    client_types: list[ClientType]
    rate_type_id: int
    marketer_id: int
    min_power: condecimal(decimal_places=2, ge=0) | None
    max_power: condecimal(decimal_places=2, ge=0) | None
    min_consumption: condecimal(decimal_places=2, ge=0) | None
    max_consumption: condecimal(decimal_places=2, ge=0) | None
    energy_price_1: condecimal(decimal_places=6, ge=0) | None
    energy_price_2: condecimal(decimal_places=6, ge=0) | None
    energy_price_3: condecimal(decimal_places=6, ge=0) | None
    energy_price_4: condecimal(decimal_places=6, ge=0) | None
    energy_price_5: condecimal(decimal_places=6, ge=0) | None
    energy_price_6: condecimal(decimal_places=6, ge=0) | None
    power_price_1: condecimal(decimal_places=6, ge=0) | None
    power_price_2: condecimal(decimal_places=6, ge=0) | None
    power_price_3: condecimal(decimal_places=6, ge=0) | None
    power_price_4: condecimal(decimal_places=6, ge=0) | None
    power_price_5: condecimal(decimal_places=6, ge=0) | None
    power_price_6: condecimal(decimal_places=6, ge=0) | None
    fixed_term_price: condecimal(decimal_places=6, ge=0) | None
    permanency: bool
    length: conint(ge=0)
    is_full_renewable: bool | None
    compensation_surplus: bool | None
    compensation_surplus_value: condecimal(decimal_places=6, ge=0) | None

    _order_client_types = validator("client_types", allow_reuse=True)(
        order_client_types
    )

    class Config:
        orm_mode = True


class RateCreateResponse(RateCreateRequest):
    id: int
    is_active: bool
    is_deleted: bool
    create_at: datetime


class RateUpdateRequest(BaseModel):
    name: constr(max_length=64)
    client_types: list[ClientType]
    rate_type_id: int
    min_power: condecimal(decimal_places=2, ge=0) | None
    max_power: condecimal(decimal_places=2, ge=0) | None
    min_consumption: condecimal(decimal_places=2, ge=0) | None
    max_consumption: condecimal(decimal_places=2, ge=0) | None
    energy_price_1: condecimal(decimal_places=6, ge=0) | None
    energy_price_2: condecimal(decimal_places=6, ge=0) | None
    energy_price_3: condecimal(decimal_places=6, ge=0) | None
    energy_price_4: condecimal(decimal_places=6, ge=0) | None
    energy_price_5: condecimal(decimal_places=6, ge=0) | None
    energy_price_6: condecimal(decimal_places=6, ge=0) | None
    power_price_1: condecimal(decimal_places=6, ge=0) | None
    power_price_2: condecimal(decimal_places=6, ge=0) | None
    power_price_3: condecimal(decimal_places=6, ge=0) | None
    power_price_4: condecimal(decimal_places=6, ge=0) | None
    power_price_5: condecimal(decimal_places=6, ge=0) | None
    power_price_6: condecimal(decimal_places=6, ge=0) | None
    fixed_term_price: condecimal(decimal_places=6, ge=0) | None
    permanency: bool
    length: conint(ge=0)
    is_full_renewable: bool | None
    compensation_surplus: bool | None
    compensation_surplus_value: condecimal(decimal_places=6, ge=0) | None

    _order_client_types = validator("client_types", allow_reuse=True)(
        order_client_types
    )

    class Config:
        orm_mode = True


class RatePartialUpdateRequest(BaseModel):
    is_active: bool | None
    is_deleted: bool | None

    class Config:
        orm_mode = True


class RateUpdateDetailListResponse(BaseModel):
    id: int
    name: constr(max_length=64)
    price_type: PriceType
    client_types: list[ClientType]
    rate_type: RateTypeBasicResponse
    marketer: MarketerBasicResponse
    min_power: condecimal(decimal_places=2, ge=0) | None
    max_power: condecimal(decimal_places=2, ge=0) | None
    min_consumption: condecimal(decimal_places=2, ge=0) | None
    max_consumption: condecimal(decimal_places=2, ge=0) | None
    energy_price_1: condecimal(decimal_places=6, ge=0) | None
    energy_price_2: condecimal(decimal_places=6, ge=0) | None
    energy_price_3: condecimal(decimal_places=6, ge=0) | None
    energy_price_4: condecimal(decimal_places=6, ge=0) | None
    energy_price_5: condecimal(decimal_places=6, ge=0) | None
    energy_price_6: condecimal(decimal_places=6, ge=0) | None
    power_price_1: condecimal(decimal_places=6, ge=0) | None
    power_price_2: condecimal(decimal_places=6, ge=0) | None
    power_price_3: condecimal(decimal_places=6, ge=0) | None
    power_price_4: condecimal(decimal_places=6, ge=0) | None
    power_price_5: condecimal(decimal_places=6, ge=0) | None
    power_price_6: condecimal(decimal_places=6, ge=0) | None
    fixed_term_price: condecimal(decimal_places=6, ge=0) | None
    permanency: bool
    length: conint(ge=0)
    is_full_renewable: bool | None
    compensation_surplus: bool | None
    compensation_surplus_value: condecimal(decimal_places=6, ge=0) | None
    is_active: bool
    create_at: datetime

    class Config:
        orm_mode = True


class RelatedRateTypeFilter(Filter):
    id: int | None
    id__in: list[int] | None
    name__unaccent: str | None
    energy_type: EnergyType | None
    order_by: List[str] = ["-id"]

    class Constants(Filter.Constants):
        model = RateType


class RateFilter(Filter):
    id: int | None
    id__in: list[int] | None
    name__unaccent: str | None
    price_type: PriceType | None
    client_types__contains: list[str] | None
    marketer_id: int | None
    min_power__gte: condecimal(decimal_places=2, ge=0) | None
    max_power__lte: condecimal(decimal_places=2, ge=0) | None
    min_consumption__gte: condecimal(decimal_places=2, ge=0) | None
    max_consumption__lte: condecimal(decimal_places=2, ge=0) | None
    energy_price_1__lte: condecimal(decimal_places=6, ge=0) | None
    energy_price_1__gte: condecimal(decimal_places=6, ge=0) | None
    energy_price_2__lte: condecimal(decimal_places=6, ge=0) | None
    energy_price_2__gte: condecimal(decimal_places=6, ge=0) | None
    energy_price_3__lte: condecimal(decimal_places=6, ge=0) | None
    energy_price_3__gte: condecimal(decimal_places=6, ge=0) | None
    energy_price_4__lte: condecimal(decimal_places=6, ge=0) | None
    energy_price_4__gte: condecimal(decimal_places=6, ge=0) | None
    energy_price_5__lte: condecimal(decimal_places=6, ge=0) | None
    energy_price_5__gte: condecimal(decimal_places=6, ge=0) | None
    energy_price_6__lte: condecimal(decimal_places=6, ge=0) | None
    energy_price_6__gte: condecimal(decimal_places=6, ge=0) | None
    power_price_1__lte: condecimal(decimal_places=6, ge=0) | None
    power_price_1__gte: condecimal(decimal_places=6, ge=0) | None
    power_price_2__lte: condecimal(decimal_places=6, ge=0) | None
    power_price_2__gte: condecimal(decimal_places=6, ge=0) | None
    power_price_3__lte: condecimal(decimal_places=6, ge=0) | None
    power_price_3__gte: condecimal(decimal_places=6, ge=0) | None
    power_price_4__lte: condecimal(decimal_places=6, ge=0) | None
    power_price_4__gte: condecimal(decimal_places=6, ge=0) | None
    power_price_5__lte: condecimal(decimal_places=6, ge=0) | None
    power_price_5__gte: condecimal(decimal_places=6, ge=0) | None
    power_price_6__lte: condecimal(decimal_places=6, ge=0) | None
    power_price_6__gte: condecimal(decimal_places=6, ge=0) | None
    fixed_term_price__lte: condecimal(decimal_places=6, ge=0) | None
    fixed_term_price__gte: condecimal(decimal_places=6, ge=0) | None
    permanency: bool | None
    length__lte: conint(ge=0) | None
    length__gte: conint(ge=0) | None
    is_full_renewable: bool | None
    compensation_surplus: bool | None
    compensation_surplus_value__lte: condecimal(decimal_places=6, ge=0) | None
    compensation_surplus_value__gte: condecimal(decimal_places=6, ge=0) | None
    is_active: bool | None
    create_at: datetime | None
    create_at__gt: datetime | None
    create_at__lte: datetime | None
    rate_type: RelatedRateTypeFilter = FilterDepends(
        with_prefix("rate_type", RelatedRateTypeFilter), use_cache=False
    )
    marketer: MarketerBaseFilter = FilterDepends(
        with_prefix("marketer", MarketerBaseFilter), use_cache=False
    )

    order_by: List[str] = ["-id"]

    class Constants(Filter.Constants):
        model = Rate


class RelatedRateIdResponse(BaseModel):
    id: int

    class Config:
        orm_mode = True


class RelatedRateResponseOtherCost(RelatedRateIdResponse):
    name: str
    marketer: MarketerBasicResponse
    rate_type: RateTypeBasicResponse


class RelatedRateResponse(BaseModel):
    id: int
    name: str
    rate_type: RateTypeBasicResponse
    marketer: MarketerBasicResponse
    marketer_id: int
    price_type: PriceType

    class Config:
        orm_mode = True


class RelatedRateFilter(Filter):
    id: int | None
    id__in: list[int] | None
    name__unaccent: str | None
    price_type: PriceType | None
    marketer_id: int | None
    marketer_id__in: list[int] | None
    rate_type: RelatedRateTypeFilter | None = FilterDepends(
        with_prefix("rate__rate_type", RelatedRateTypeFilter), use_cache=False
    )
    order_by: List[str] = ["-id"]

    class Constants(Filter.Constants):
        model = Rate


class RelatedRatesFilter(Filter):
    id: int | None
    id__in: list[int] | None
    name__unaccent: str | None
    price_type: PriceType | None
    marketer_id: int | None
    marketer_id__in: list[int] | None
    rate_type: RelatedRateTypeFilter | None = FilterDepends(
        with_prefix("rates__rate_type", RelatedRateTypeFilter), use_cache=False
    )
    order_by: List[str] = ["-id"]

    class Constants(Filter.Constants):
        model = Rate


class RateDeleteRequest(BaseModel):
    ids: list[int]


rate_export_headers = {
    "name": _("Name"),
    "price_type": _("Price type"),
    "client_types": _("Client types"),
    "rate_type.name": _("Rate type"),
    "rate_type.energy_type": _("energy type"),
    "min_power": _("Minimum power"),
    "max_power": _("Maximum power"),
    "min_consumption": _("Minimum consumption"),
    "max_consumption": _("Maximum consumption"),
    "energy_price_1": _("Energy price 1"),
    "energy_price_2": _("Energy price 2"),
    "energy_price_3": _("Energy price 3"),
    "energy_price_4": _("Energy price 4"),
    "energy_price_5": _("Energy price 5"),
    "energy_price_6": _("Energy price 6"),
    "power_price_1": _("Power price 1"),
    "power_price_2": _("Power price 2"),
    "power_price_3": _("Power price 3"),
    "power_price_4": _("Power price 4"),
    "power_price_5": _("Power price 5"),
    "power_price_6": _("Power price 6"),
    "fixed_term_price": _("Fixed term price"),
    "permanency": _("Permanency"),
    "length": _("Length"),
    "is_full_renewable": _("Is full renewable"),
    "compensation_surplus": _("Compensation surplus"),
    "compensation_surplus_value": _("Compensation surplus value"),
    "is_active": _("Status"),
    "create_at": _("Date"),
}
