from typing import List

from sqlalchemy.orm import Session

from src.modules.marketers.models import Address, Marketer


def create_marketer_db(db: Session, marketer: Marketer) -> Marketer:
    db.add(marketer)
    db.commit()
    db.refresh(marketer)
    return marketer


def get_marketer_queryset(db: Session, join_list: List = None, *filters):
    queryset = db.query(Marketer).filter(*filters)
    if join_list:
        queryset = queryset.join(*join_list)
    return queryset


def get_marketer_by(db: Session, *filters) -> Marketer:
    return db.query(Marketer).filter(*filters).first()


def create_address_db(db: Session, address: Address) -> Address:
    db.add(address)
    db.commit()
    db.refresh(address)
    return address
