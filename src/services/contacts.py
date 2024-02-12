from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.common import update_obj_db
from src.infrastructure.sqlalchemy.contacts import (
    create_contact_db,
    get_contact_by,
    get_contact_queryset,
)
from src.modules.contacts.models import Contact
from src.modules.contacts.schemas import (
    ContactDeleteRequest,
    ContactFilter,
    ContactInlineCreateRequest,
    ContactPartialUpdateRequest,
    ContactUpdateRequest,
)
from src.modules.users.models import User
from src.services.common import update_from_dict


def contact_create(
    db: Session, contact_data: ContactInlineCreateRequest, current_user: User
) -> Contact:
    contact = Contact(**contact_data.dict())
    contact.user_id = current_user.id
    try:
        contact = create_contact_db(db, contact)
        if contact.is_main_contact:
            set_contacts_not_main(db, contact.id, contact.client_id)
        return contact
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="value_error.already_exists"
        )
    return contact


def list_contact(db: Session, contact_filter: ContactFilter):
    return contact_filter.sort(
        contact_filter.filter(
            get_contact_queryset(
                db,
                None,
            ),
            model_class_without_alias=Contact,
        ),
        model_class_without_alias=Contact,
    )


def get_contact(db: Session, contact_id: int) -> Contact:
    contact = get_contact_by(db, Contact.id == contact_id)

    if not contact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="contact_not_exist"
        )

    return contact


def contact_partial_update(
    db: Session,
    contact_id: int,
    contact_data: ContactPartialUpdateRequest,
) -> Contact:
    contact = get_contact(db, contact_id)
    contact_data_request = contact_data.dict(exclude_unset=True)
    update_from_dict(contact, contact_data_request)
    if contact.is_main_contact:
        set_contacts_not_main(db, contact_id, contact.client_id)
    contact = update_obj_db(db, contact)
    return contact


def contact_update(
    db: Session,
    contact_id: int,
    contact_data: ContactUpdateRequest,
) -> Contact:
    contact = get_contact(db, contact_id)
    contact_data_request = contact_data.dict()
    update_from_dict(contact, contact_data_request)
    try:
        if contact.is_main_contact:
            set_contacts_not_main(db, contact_id, contact.client_id)
        contact = update_obj_db(db, contact)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="value_error.already_exists"
        )
    return contact


def delete_contacts(db: Session, contacts_data: ContactDeleteRequest):
    db.query(Contact).filter(Contact.id.in_(contacts_data.ids)).delete()
    db.commit()


def set_contacts_not_main(db: Session, contact_id: int, client_id: int):
    db.query(Contact).filter(Contact.client_id == client_id).filter(
        Contact.id != contact_id
    ).update({"is_main_contact": False})
    db.commit()
