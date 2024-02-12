from typing import List

from sqlalchemy.orm import Session

from src.modules.contacts.models import Contact


def create_contact_db(db: Session, contact: Contact) -> Contact:
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def get_contact_queryset(db: Session, join_list: List = None, *filters):
    queryset = db.query(Contact).filter(*filters)
    if join_list:
        queryset = queryset.join(*join_list)
    return queryset


def get_contact_by(db: Session, *filters) -> Contact:
    return db.query(Contact).filter(*filters).first()
