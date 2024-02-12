from typing import List

from sqlalchemy.orm import Session, joinedload

from src.modules.rates.models import Rate, RateType


def create_rate_type_db(db: Session, rate_type: RateType) -> RateType:
    db.add(rate_type)
    db.commit()
    db.refresh(rate_type)
    return rate_type


def get_rate_types_queryset(db: Session, join_list: List = None, *filters):
    queryset = db.query(RateType).filter(*filters)
    if join_list:
        queryset = queryset.options(joinedload(*join_list))
    return queryset


def get_rate_type_by(db: Session, *filters) -> RateType:
    return db.query(RateType).filter(*filters).first()


def create_rate_db(db: Session, rate: Rate) -> Rate:
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


def get_rate_by(db: Session, *filters) -> Rate:
    return db.query(Rate).filter(*filters).first()


def get_rate_queryset(db: Session, join_list: List = None, *filters):
    queryset = db.query(Rate).filter(*filters)
    if join_list:
        queryset = queryset.join(*join_list)
    return queryset
