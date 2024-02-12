from fastapi import HTTPException, status
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql.expression import false

from src.infrastructure.sqlalchemy.common import is_overlapping, update_obj_db
from src.infrastructure.sqlalchemy.margins import (
    create_margin_db,
    get_margin_by,
    get_margin_queryset,
)
from src.infrastructure.sqlalchemy.rates import get_rate_by
from src.modules.margins.models import Margin, MarginType
from src.modules.margins.schemas import (
    MarginCreateRequest,
    MarginDeleteRequest,
    MarginFilter,
    MarginPartialUpdateRequest,
    MarginUpdateRequest,
    validate_margin,
)
from src.modules.rates.models import PriceType, Rate
from src.services.common import update_from_dict


def check_consumption_range_overlap(
    margin_qs: Query, min_consumption: float, max_consumption: float
):
    if is_overlapping(
        margin_qs,
        min_consumption,
        max_consumption,
        Margin.min_consumption,
        Margin.max_consumption,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.consumption_range.overlap",
        )


def margin_create(db: Session, margin_data: MarginCreateRequest) -> Margin:
    if not get_rate_by(
        db,
        Rate.id == margin_data.rate_id,
        Rate.is_deleted == false(),
        Rate.price_type == PriceType.fixed_base,
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="rate_not_exist"
        )
    margin_qs = get_margin_queryset(
        db, None, Margin.rate_id == margin_data.rate_id, Margin.is_deleted == false()
    )
    if margin_qs.filter(Margin.type != margin_data.type).count() > 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.type.already_exist_other_type",
        )
    if margin_data.type == MarginType.consume_range:
        check_consumption_range_overlap(
            margin_qs, margin_data.min_consumption, margin_data.max_consumption
        )
    margin = Margin(**margin_data.dict())
    return create_margin_db(db, margin)


def get_margin(db: Session, margin_id: int) -> Margin:
    margin = get_margin_by(
        db,
        Margin.id == margin_id,
        Margin.is_deleted == false(),
    )

    if not margin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="margin_not_exist"
        )

    return margin


def margin_update(
    db: Session,
    margin_id: int,
    margin_data: MarginUpdateRequest,
) -> Margin:
    margin = get_margin(db, margin_id)
    margin_data_request = margin_data.dict(exclude_unset=True)
    validate_margin(margin.type, margin_data_request)
    if margin.type == MarginType.rate_type:
        margin_data_request.pop("min_consumption", None)
        margin_data_request.pop("max_consumption", None)
    if margin.type == MarginType.consume_range:
        margin_qs = get_margin_queryset(
            db,
            None,
            Margin.rate_id == margin.rate_id,
            Margin.is_deleted == false(),
            Margin.id != margin_id,
        )
        check_consumption_range_overlap(
            margin_qs,
            margin_data_request.get("min_consumption"),
            margin_data_request.get("max_consumption"),
        )

    update_from_dict(margin, margin_data_request)
    margin = update_obj_db(db, margin)
    return margin


def list_margins(db: Session, margin_filter: MarginFilter):
    return margin_filter.sort(
        margin_filter.filter(
            get_margin_queryset(db, None, Margin.is_deleted == false())
        )
    )


def margin_partial_update(
    db: Session,
    margin_id: int,
    margin_data: MarginPartialUpdateRequest,
) -> Margin:
    margin = update_obj_db(
        db,
        update_from_dict(
            get_margin(db, margin_id), margin_data.dict(exclude_unset=True)
        ),
    )
    return margin


def delete_margins(db: Session, margins_data: MarginDeleteRequest):
    db.query(Margin).filter(Margin.id.in_(margins_data.ids)).update(
        {"is_deleted": True}
    )
    db.commit()
