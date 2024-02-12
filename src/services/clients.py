from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.clients import (
    create_client_db,
    get_client_by,
    get_client_queryset,
)
from src.infrastructure.sqlalchemy.common import update_obj_db
from src.infrastructure.sqlalchemy.contacts import create_contact_db
from src.modules.clients.models import Client
from src.modules.clients.schemas import (  # AddressUpdateRequest,
    ClientCreateRequest,
    ClientDeleteRequest,
    ClientFilter,
    ClientPartialUpdateRequest,
    ClientUpdateRequest,
)
from src.modules.contacts.models import Contact
from src.modules.users.models import User
from src.services.common import update_from_dict


def client_create(
    db: Session, client_data: ClientCreateRequest, current_user: User
) -> Client:
    contact_data = client_data.main_contact
    del client_data.main_contact
    client = Client(**client_data.dict())
    client.user_id = current_user.id
    try:
        client = create_client_db(db, client)

        if contact_data:
            contact = Contact(**contact_data.dict())
            contact.is_main_contact = True
            contact.client_id = client.id
            contact.user_id = current_user.id
            create_contact_db(db, contact)
        return client
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="value_error.already_exists"
        )


def list_client(db: Session, client_filter: ClientFilter):
    return client_filter.sort(
        client_filter.filter(
            get_client_queryset(
                db,
                None,
            ),
            model_class_without_alias=Client,
        ),
        model_class_without_alias=Client,
    )


def get_client(db: Session, client_id: int) -> Client:
    client = get_client_by(db, Client.id == client_id)

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="client_not_exist"
        )

    return client


def client_partial_update(
    db: Session,
    client_id: int,
    client_data: ClientPartialUpdateRequest,
) -> Client:
    client = get_client(db, client_id)
    client_data_request = client_data.dict(exclude_unset=True)
    update_from_dict(client, client_data_request)
    client = update_obj_db(db, client)
    return client


def client_update(
    db: Session,
    client_id: int,
    client_data: ClientUpdateRequest,
) -> Client:
    client = get_client(db, client_id)
    client_data_request = client_data.dict()
    update_from_dict(client, client_data_request)
    try:
        client = update_obj_db(db, client)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="value_error.already_exists"
        )
    return client


def delete_clients(db: Session, clients_data: ClientDeleteRequest):
    db.query(Client).filter(Client.id.in_(clients_data.ids)).delete()
    db.commit()
