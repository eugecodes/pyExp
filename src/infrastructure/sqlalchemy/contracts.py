from typing import List

from sqlalchemy.orm import Session

from src.modules.contracts.models import Contract


def create_contract_db(db: Session, contract: Contract) -> Contract:
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


def get_contract_queryset(db: Session, join_list: List = None, *filters):
    queryset = db.query(Contract).filter(*filters)
    if join_list:
        queryset = queryset.join(*join_list)
    return queryset


def get_contract_by(db: Session, *filters) -> Contract:
    return db.query(Contract).filter(*filters).first()
