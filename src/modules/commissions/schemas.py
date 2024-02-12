from datetime import datetime

from fastapi_filter import FilterDepends, with_prefix
from pydantic import BaseModel, condecimal, conint, conlist, constr

from src.infrastructure.sqlalchemy.filters import Filter
from src.modules.commissions.models import Commission, RangeType
from src.modules.rates.schemas import (
    RateTypeBasicResponse,
    RelatedRateIdResponse,
    RelatedRateResponse,
    RelatedRatesFilter,
    RelatedRateTypeFilter,
)
from utils.i18n import trans as _


class CommissionBase(BaseModel):
    name: constr(max_length=124)
    range_type: RangeType | None
    min_consumption: condecimal(decimal_places=2, ge=0) | None
    max_consumption: condecimal(decimal_places=2, ge=0) | None
    min_power: condecimal(decimal_places=2, ge=0) | None
    max_power: condecimal(decimal_places=2, ge=0) | None
    percentage_Test_commission: conint(ge=0) | None
    rate_type_segmentation: bool | None
    Test_commission: condecimal(decimal_places=2, ge=0) | None

    class Config:
        orm_mode = True


class CommissionCreateRequest(CommissionBase):
    rate_type_id: conint(gt=0) | None
    rates: conlist(int, min_items=1, unique_items=True)


class CommissionCreateResponse(CommissionBase):
    id: int
    rate_type_id: conint(gt=0) | None
    rates: conlist(RelatedRateIdResponse)


class CommissionUpdateRequest(BaseModel):
    name: constr(max_length=124)
    percentage_Test_commission: conint(ge=0) | None
    rates: conlist(int, min_items=1, unique_items=True)
    min_consumption: condecimal(decimal_places=2, ge=0) | None
    max_consumption: condecimal(decimal_places=2, ge=0) | None
    min_power: condecimal(decimal_places=2, ge=0) | None
    max_power: condecimal(decimal_places=2, ge=0) | None
    Test_commission: condecimal(decimal_places=2, ge=0) | None

    class Config:
        orm_mode = True


class CommissionUpdateDetailListResponse(CommissionBase):
    id: int
    rates: conlist(RelatedRateResponse)
    rate_type: RateTypeBasicResponse | None
    create_at: datetime


class CommissionPartialUpdateRequest(BaseModel):
    is_deleted: bool | None

    class Config:
        orm_mode = True


class CommissionDeleteRequest(BaseModel):
    ids: list[int]


class CommissionFilter(Filter):
    id: int | None
    id__in: list[int] | None
    name__unaccent: constr(max_length=124) | None
    range_type: RangeType | None
    min_consumption__gte: condecimal(decimal_places=2, ge=0) | None
    min_consumption__lte: condecimal(decimal_places=2, ge=0) | None
    max_consumption__gte: condecimal(decimal_places=2, ge=0) | None
    max_consumption__lte: condecimal(decimal_places=2, ge=0) | None
    min_power__gte: condecimal(decimal_places=2, ge=0) | None
    min_power__lte: condecimal(decimal_places=2, ge=0) | None
    max_power__gte: condecimal(decimal_places=2, ge=0) | None
    max_power__lte: condecimal(decimal_places=2, ge=0) | None
    percentage_Test_commission__gte: conint(ge=0) | None
    percentage_Test_commission__lte: conint(ge=0) | None
    rate_type_segmentation: bool | None
    Test_commission__gte: condecimal(decimal_places=2, ge=0) | None
    Test_commission__lte: condecimal(decimal_places=2, ge=0) | None
    create_at__gte: datetime | None
    create_at__lt: datetime | None
    rates: RelatedRatesFilter | None = FilterDepends(
        with_prefix("rates", RelatedRatesFilter), use_cache=False
    )
    rate_type: RelatedRateTypeFilter | None = FilterDepends(
        with_prefix("rate_type", RelatedRateTypeFilter), use_cache=False
    )

    order_by: list[str] = ["-id"]

    class Constants(Filter.Constants):
        model = Commission


commission_export_headers = {
    "id": _("Id"),
    "name": _("Name"),
    "range_type": _("Range type"),
    "min_consumption": _("Minimum consumption"),
    "max_consumption": _("Maximum consumption"),
    "min_power": _("Minimum power"),
    "max_power": _("Maximum power"),
    "percentage_Test_commission": _("Percentage Test commission"),
    "rate_type_segmentation": _("Rate type segmentation"),
    "Test_commission": _("Test commission"),
    "rates:name": _("Rates"),
    "rate_type.name": _("Rate type"),
    "create_at": _("Date"),
}
