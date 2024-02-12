from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.common import update_obj_db
from src.infrastructure.sqlalchemy.supply_points import (
    create_supply_point_db,
    get_supply_point_by,
    get_supply_point_queryset,
)
from src.modules.supply_points.models import SupplyPoint
from src.modules.supply_points.schemas import (
    SupplyPointCreateRequest,
    SupplyPointDeleteRequest,
    SupplyPointFilter,
    SupplyPointPartialUpdateRequest,
    SupplyPointUpdateRequest,
)
from src.modules.users.models import User
from src.services.common import update_from_dict


def supply_point_create(
    db: Session, supply_point_data: SupplyPointCreateRequest, current_user: User
) -> SupplyPoint:
    supply_point = SupplyPoint(**supply_point_data.dict())
    supply_point.user_id = current_user.id
    try:
        supply_point = create_supply_point_db(db, supply_point)
        return supply_point
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="value_error.already_exists"
        )


def list_supply_point(db: Session, supply_point_filter: SupplyPointFilter):
    return supply_point_filter.sort(
        supply_point_filter.filter(
            get_supply_point_queryset(db, None),
            model_class_without_alias=SupplyPoint,
        ),
        model_class_without_alias=SupplyPoint,
    )


def get_supply_point(db: Session, supply_point_id: int) -> SupplyPoint:
    supply_point = get_supply_point_by(db, SupplyPoint.id == supply_point_id)

    if not supply_point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="supply_point_not_exist"
        )

    return supply_point


def supply_point_partial_update(
    db: Session,
    supply_point_id: int,
    supply_point_data: SupplyPointPartialUpdateRequest,
) -> SupplyPoint:
    supply_point = get_supply_point(db, supply_point_id)
    supply_point_data_request = supply_point_data.dict(exclude_unset=True)
    update_from_dict(supply_point, supply_point_data_request)
    supply_point = update_obj_db(db, supply_point)
    return supply_point


def supply_point_update(
    db: Session,
    supply_point_id: int,
    supply_point_data: SupplyPointUpdateRequest,
) -> SupplyPoint:
    supply_point = get_supply_point(db, supply_point_id)
    supply_point_data_request = supply_point_data.dict()
    update_from_dict(supply_point, supply_point_data_request)
    try:
        supply_point = update_obj_db(db, supply_point)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="value_error.already_exists"
        )
    return supply_point


def delete_supply_points(db: Session, supply_points_data: SupplyPointDeleteRequest):
    db.query(SupplyPoint).filter(SupplyPoint.id.in_(supply_points_data.ids)).delete()
    db.commit()
