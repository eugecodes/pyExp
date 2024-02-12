from sqlalchemy.orm import Session

from src.modules.commissions.models import Commission


def create_commission_db(db: Session, commission: Commission) -> Commission:
    db.add(commission)
    db.commit()
    db.refresh(commission)
    return commission


def get_commission_queryset(db: Session, join_list: list = None, *filters):
    queryset = db.query(Commission).filter(*filters)
    if join_list:
        queryset = queryset.join(*join_list)
    return queryset


def get_commission_by(db: Session, *filters) -> Commission:
    return db.query(Commission).filter(*filters).first()
