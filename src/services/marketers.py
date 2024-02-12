from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import false

from src.infrastructure.sqlalchemy.common import update_obj_db
from src.infrastructure.sqlalchemy.marketers import (
    create_marketer_db,
    get_marketer_by,
    get_marketer_queryset,
)
from src.modules.marketers.models import Address, Marketer
from src.modules.marketers.schemas import (
    AddressUpdateRequest,
    MarketerCreateRequest,
    MarketerDeleteRequest,
    MarketerFilter,
    MarketerPartialUpdateRequest,
    MarketerUpdateRequest,
)
from src.modules.users.models import User
from src.services.common import update_from_dict


def marketer_create(
    db: Session, marketer_data: MarketerCreateRequest, current_user: User
) -> Marketer:
    marketer = Marketer(**marketer_data.dict())
    marketer.user_id = current_user.id
    try:
        marketer = create_marketer_db(db, marketer)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="value_error.already_exists"
        )
    return marketer


def list_marketer(db: Session, marketer_filter: MarketerFilter):
    return marketer_filter.sort(
        marketer_filter.filter(
            get_marketer_queryset(db, None, Marketer.is_deleted == false()),
            model_class_without_alias=Marketer,
        ),
        model_class_without_alias=Marketer,
    )


def get_marketer(db: Session, marketer_id: int) -> Marketer:
    marketer = get_marketer_by(
        db,
        Marketer.id == marketer_id,
        Marketer.is_deleted == false(),
    )

    if not marketer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="marketer_not_exist"
        )

    return marketer


def create_update_marketer_address(
    db: Session, marketer: Marketer, address_data_request: AddressUpdateRequest
):
    if marketer.address:
        update_from_dict(marketer.address, address_data_request)
        return marketer
    marketer.address = Address(**address_data_request)
    return marketer


def marketer_partial_update(
    db: Session,
    marketer_id: int,
    marketer_data: MarketerPartialUpdateRequest,
) -> Marketer:
    marketer = get_marketer(db, marketer_id)
    marketer_data_request = marketer_data.dict(exclude_unset=True)
    update_from_dict(marketer, marketer_data_request)
    marketer = update_obj_db(db, marketer)
    return marketer


def marketer_update(
    db: Session,
    marketer_id: int,
    marketer_data: MarketerUpdateRequest,
) -> Marketer:
    marketer = get_marketer(db, marketer_id)
    marketer_data_request = marketer_data.dict()
    address_data_request = marketer_data_request.pop("address", None)
    if address_data_request:
        marketer = create_update_marketer_address(db, marketer, address_data_request)
    update_from_dict(marketer, marketer_data_request)
    try:
        marketer = update_obj_db(db, marketer)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="value_error.already_exists"
        )
    return marketer


def delete_marketers(db: Session, marketers_data: MarketerDeleteRequest):
    db.query(Marketer).filter(Marketer.id.in_(marketers_data.ids)).update(
        {"is_deleted": True}
    )
    db.commit()
