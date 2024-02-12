from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.marketers import (
    create_address_db,
    create_marketer_db,
    get_marketer_by,
    get_marketer_queryset,
)
from src.modules.marketers.models import Address, Marketer
from src.modules.users.models import User


def test_create_marketer_db_ok(db_session: Session, user_create: User):
    create_marketer_db(
        db_session,
        Marketer(
            name="Electrical services",
            fiscal_name="Electrical services Inc.",
            cif="QWERTY123",
            email="electricalservices@test.com",
            user=user_create,
        ),
    )
    assert db_session.query(Marketer).count() == 1


def test_get_marketer_queryset_ok(db_session: Session, marketer: Marketer):
    assert get_marketer_queryset(db_session).count() == 1


def test_get_marketer_queryset_with_join_list(db_session: Session, marketer: Marketer):
    result = get_marketer_queryset(db_session, [Marketer.user])
    assert result.count() == 1
    assert result.first().user.first_name == "John"


def test_get_marketer_by_one_field(marketer: Marketer, db_session: Session):
    marketer = get_marketer_by(db_session, Marketer.id == 1)
    assert marketer.id == 1


def test_get_marketer_by_multiple_fields(marketer: Marketer, db_session: Session):
    marketer = get_marketer_by(
        db_session,
        Marketer.id == 1,
        Marketer.name == "Marketer",
        Marketer.fiscal_name == "Marketer official",
    )
    assert marketer.id == 1
    assert marketer.name == "Marketer"
    assert marketer.fiscal_name == "Marketer official"


def test_get_marketer_by_without_fields(marketer: Marketer, db_session: Session):
    marketer = get_marketer_by(db_session)
    assert marketer.id == 1
    assert marketer.name == "Marketer"
    assert marketer.fiscal_name == "Marketer official"


def test_get_marketer_by_none(marketer: Marketer, db_session: Session):
    marketer = get_marketer_by(db_session, Marketer.id == 1234)
    assert marketer is None


def test_create_address_db_ok(db_session: Session):
    create_address_db(
        db_session,
        Address(
            type="Avenue",
            name="Fifth",
            postal_code="10021",
            city="New York",
            province="New York State",
        ),
    )
    assert db_session.query(Address).count() == 1
