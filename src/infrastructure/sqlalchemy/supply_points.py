from typing import List

from sqlalchemy.orm import Session

from src.modules.supply_points.models import SupplyPoint


def create_supply_point_db(db: Session, supply_point: SupplyPoint) -> SupplyPoint:
    db.add(supply_point)
    db.commit()
    db.refresh(supply_point)
    return supply_point


def get_supply_point_queryset(db: Session, join_list: List = None, *filters):
    queryset = db.query(SupplyPoint).filter(*filters)
    if join_list:
        queryset = queryset.join(*join_list)
    return queryset


def get_supply_point_by(db: Session, *filters) -> SupplyPoint:
    return db.query(SupplyPoint).filter(*filters).first()
