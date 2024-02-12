from typing import List

from sqlalchemy.orm import Session

from src.modules.costs.models import EnergyCost, OtherCost


def create_energy_cost_db(db: Session, energy_cost: EnergyCost) -> EnergyCost:
    db.add(energy_cost)
    db.commit()
    db.refresh(energy_cost)
    return energy_cost


def get_energy_costs_queryset(db: Session, join_list: List = None, *filters):
    queryset = db.query(EnergyCost).filter(*filters)
    if join_list:
        queryset = queryset.join(*join_list)
    return queryset


def get_energy_cost_by(db: Session, *filters) -> EnergyCost:
    return db.query(EnergyCost).filter(*filters).first()


def create_other_cost_db(db: Session, other_cost: OtherCost) -> OtherCost:
    db.add(other_cost)
    db.commit()
    db.refresh(other_cost)
    return other_cost


def get_other_cost_queryset(db: Session, join_list: list = None, *filters):
    queryset = db.query(OtherCost).filter(*filters)
    if join_list:
        queryset = queryset.join(*join_list)
    return queryset


def get_other_cost_by(db: Session, *filters) -> OtherCost:
    return db.query(OtherCost).filter(*filters).first()
