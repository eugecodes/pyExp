from datetime import datetime
from decimal import Decimal
from typing import List

from fastapi import HTTPException, status
from fastapi_filter import FilterDepends, with_prefix
from pydantic import BaseModel, condecimal, root_validator

from src.infrastructure.sqlalchemy.filters import Filter
from src.modules.margins.models import Margin, MarginType
from src.modules.rates.schemas import RelatedRateFilter, RelatedRateResponse
from utils.i18n import trans as _


def validate_margin(type: MarginType, values: dict):
    if values.get("min_margin") > values.get("max_margin"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.margin_range.invalid",
        )
    min_consumption = values.get("min_consumption")
    max_consumption = values.get("max_consumption")

    if type == MarginType.consume_range:
        if min_consumption is None or max_consumption is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="value_error.consumption_range.missing",
            )
        if min_consumption > max_consumption:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="value_error.consumption_range.invalid",
            )


class MarginCreateRequest(BaseModel):
    type: MarginType
    min_consumption: condecimal(decimal_places=2, ge=0) | None
    max_consumption: condecimal(decimal_places=2, ge=0) | None
    min_margin: condecimal(decimal_places=4, ge=0)
    max_margin: condecimal(decimal_places=4, ge=0)
    rate_id: int

    class Config:
        orm_mode = True

    @root_validator(pre=True)
    def validate_margin(cls, values):
        margin_type = values.get("type")
        validate_margin(margin_type, values)
        if margin_type == MarginType.rate_type and not (
            values.get("min_consumption") is None
            or values.get("max_consumption") is None
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="value_error.type.invalid_consumption_range",
            )
        return values


class MarginCreateUpdateResponse(MarginCreateRequest):
    id: int
    create_at: datetime


class MarginUpdateRequest(BaseModel):
    min_consumption: condecimal(decimal_places=2, ge=0) | None
    max_consumption: condecimal(decimal_places=2, ge=0) | None
    min_margin: condecimal(decimal_places=4, ge=0)
    max_margin: condecimal(decimal_places=4, ge=0)

    class Config:
        orm_mode = True


class MarginListDetailPartialUpdateResponse(MarginUpdateRequest):
    id: int
    type: MarginType
    rate: RelatedRateResponse
    is_deleted: bool
    create_at: datetime


class MarginDeleteRequest(BaseModel):
    ids: list[int]


class MarginFilter(Filter):
    id: int | None
    id__in: list[int] | None
    rate: RelatedRateFilter | None = FilterDepends(
        with_prefix("rate", RelatedRateFilter), use_cache=False
    )
    min_consumption__gte: Decimal | None
    min_consumption__lte: Decimal | None
    max_consumption__gte: Decimal | None
    max_consumption__lte: Decimal | None
    min_margin__gte: Decimal | None
    min_margin__lte: Decimal | None
    max_margin__gte: Decimal | None
    max_margin__lte: Decimal | None
    create_at__gte: datetime | None
    create_at__lt: datetime | None
    order_by: List[str] = ["-id"]

    class Constants(Filter.Constants):
        model = Margin


class MarginPartialUpdateRequest(BaseModel):
    is_deleted: bool | None

    class Config:
        orm_mode = True


margin_export_headers = {
    "id": _("Id"),
    "type": _("Type"),
    "rate.name": _("Rate"),
    "rate.rate_type.name": _("Rate type"),
    "min_consumption": _("Minimum consumption"),
    "max_consumption": _("Maximum consumption"),
    "min_margin": _("Minimum margin"),
    "max_margin": _("Maximum margin"),
    "create_at": _("Date"),
}
