from typing import List

from sqlalchemy.orm import Session

from src.modules.clients.models import Client


def create_client_db(db: Session, client: Client) -> Client:
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def get_client_queryset(db: Session, join_list: List = None, *filters):
    queryset = db.query(Client).filter(*filters)
    if join_list:
        queryset = queryset.join(*join_list)
    return queryset


def get_client_by(db: Session, *filters) -> Client:
    return db.query(Client).filter(*filters).first()


# def create_address_db(db: Session, address: Address) -> Address:
#     db.add(address)
#     db.commit()
#     db.refresh(address)
#     return address
