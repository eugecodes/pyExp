from sqlalchemy import Enum
from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.common import (
    ArrayOfEnum,
    is_overlapping,
    update_obj_db,
)
from src.modules.commissions.models import Commission
from src.modules.rates.models import ClientType
from src.modules.users.models import User


def test_update_obj_db(db_session: Session, user_create):
    user_create.first_name = "Another name"
    update_obj_db(db_session, user_create)

    user_from_db = db_session.query(User).filter(User.id == user_create.id).first()

    assert user_from_db.first_name == "Another name"


class TestArrayOfEnum:
    def test_result_processor_ok(self):
        array_column = ArrayOfEnum(Enum(ClientType))
        process = array_column.result_processor(
            array_column._default_dialect(), Enum(ClientType)
        )
        assert process(None) is None


def test_is_overlapping_ok(db_session: Session, commission: Commission):
    assert is_overlapping(
        db_session.query(Commission),
        5,
        10,
        Commission.min_consumption,
        Commission.max_consumption,
    )


def test_is_overlapping_false_ok(db_session: Session, commission: Commission):
    assert (
        is_overlapping(
            db_session.query(Commission),
            26,
            55,
            Commission.min_consumption,
            Commission.max_consumption,
        )
        is False
    )
