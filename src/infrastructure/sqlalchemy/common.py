import re
from decimal import Decimal

from sqlalchemy import TypeDecorator, cast
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Query, Session

from src.infrastructure.sqlalchemy.database import Base


def update_obj_db(db: Session, obj: Base) -> Base:
    db.commit()
    db.refresh(obj)
    return obj


class ArrayOfEnum(TypeDecorator):
    impl = ARRAY

    def bind_expression(self, bindvalue):
        return cast(bindvalue, self)

    def result_processor(self, dialect, coltype):
        super_rp = super(ArrayOfEnum, self).result_processor(dialect, coltype)

        def handle_raw_string(value):
            inner = re.match(r"^{(.*)}$", value).group(1)
            return inner.split(",") if inner else []

        def process(value):
            if value is None:
                return None
            return super_rp(handle_raw_string(value))

        return process


def is_overlapping(
    qs: Query, min_limit: Decimal, max_limit: Decimal, min_attr, max_attr
) -> bool:
    return (
        qs.filter(
            ~((min_attr > max_limit) | (max_attr < min_limit))
            | ((min_attr == min_limit) & (max_attr == max_limit))
        ).count()
        != 0
    )
