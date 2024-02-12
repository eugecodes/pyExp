from sqlalchemy.orm import Session, joinedload

from src.modules.margins.models import Margin


def create_margin_db(db: Session, margin: Margin) -> Margin:
    db.add(margin)
    db.commit()
    db.refresh(margin)
    return margin


def get_margin_queryset(db: Session, join_list: list = None, *filters):
    queryset = db.query(Margin).filter(*filters)
    if join_list:
        queryset = queryset.options(joinedload(*join_list))
    return queryset


def get_margin_by(db: Session, *filters) -> Margin:
    return db.query(Margin).filter(*filters).first()
