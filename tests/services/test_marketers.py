import datetime
from decimal import Decimal

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import false
from sqlalchemy.orm import Session

from src.modules.marketers.models import Marketer
from src.modules.marketers.schemas import (
    AddressUpdateRequest,
    MarketerCreateRequest,
    MarketerDeleteRequest,
    MarketerPartialUpdateRequest,
    MarketerUpdateRequest,
)
from src.modules.users.models import User
from src.services.marketers import (
    create_update_marketer_address,
    delete_marketers,
    get_marketer,
    marketer_create,
    marketer_partial_update,
    marketer_update,
)


def test_marketer_create_ok(db_session: Session, user_create: User):
    marketer = marketer_create(
        db_session,
        MarketerCreateRequest(
            name="Electrical marketer",
            fiscal_name="Electrical marketer Inc.",
            cif="QWERTY123",
            email="elecmarketer@test.com",
        ),
        user_create,
    )

    assert db_session.query(Marketer).count() == 1
    assert marketer.name == "Electrical marketer"
    assert marketer.fiscal_name == "Electrical marketer Inc."
    assert marketer.cif == "QWERTY123"
    assert marketer.email == "elecmarketer@test.com"


def test_marketer_create_only_mandatory_field_ok(
    db_session: Session, user_create: User
):
    marketer = marketer_create(
        db_session,
        MarketerCreateRequest(
            name="Electrical marketer",
        ),
        user_create,
    )

    assert db_session.query(Marketer).count() == 1
    assert marketer.name == "Electrical marketer"
    assert not marketer.fiscal_name
    assert not marketer.cif
    assert not marketer.email


def test_marketer_create_already_exists_error(
    db_session: Session, user_create: User, marketer: Marketer
):
    with pytest.raises(HTTPException) as exc:
        marketer_create(
            db_session,
            MarketerCreateRequest(
                name="Marketer 2",
                fiscal_name="Marketer official",
                cif="QWERTY123",
                email="elecmarketer@test.com",
            ),
            user_create,
        )

    assert exc.value.detail == ("value_error.already_exists")
    assert exc.value.status_code == 409


def test_get_marketer_ok(db_session: Session, marketer: Marketer):
    assert get_marketer(db_session, marketer.id)


def test_get_marketer_not_exist(db_session: Session, marketer: Marketer):
    with pytest.raises(HTTPException) as exc:
        get_marketer(db_session, 1234)

    assert exc.value.detail == ("marketer_not_exist")


def test_get_marketer_deleted(db_session: Session, marketer_deleted: Marketer):
    with pytest.raises(HTTPException) as exc:
        get_marketer(db_session, 4)

    assert exc.value.detail == ("marketer_not_exist")


def test_create_update_marketer_address_ok(db_session: Session, marketer: Marketer):
    updated_marketer = create_update_marketer_address(
        db_session,
        marketer,
        {
            "type": "Street",
            "name": "Main",
            "number": 6,
            "postal_code": "999999",
            "city": "Miami",
            "province": "Florida",
        },
    )

    assert updated_marketer.address.type == "Street"
    assert updated_marketer.address.name == "Main"
    assert updated_marketer.address.number == 6
    assert updated_marketer.address.postal_code == "999999"
    assert updated_marketer.address.city == "Miami"
    assert updated_marketer.address.province == "Florida"


def test_create_update_marketer_address_no_address_ok(
    db_session: Session, marketer: Marketer
):
    marketer.address = None

    updated_marketer = create_update_marketer_address(
        db_session,
        marketer,
        {
            "type": "Street",
            "name": "Main",
            "number": 6,
            "postal_code": "999999",
            "city": "Miami",
            "province": "Florida",
        },
    )

    assert updated_marketer.address.type == "Street"
    assert updated_marketer.address.name == "Main"
    assert updated_marketer.address.number == 6
    assert updated_marketer.address.postal_code == "999999"
    assert updated_marketer.address.city == "Miami"
    assert updated_marketer.address.province == "Florida"


def test_marketer_update_ok(db_session: Session, marketer: Marketer):
    marketer_update(
        db_session,
        1,
        MarketerUpdateRequest(
            name="Updated name",
            fiscal_name="Fiscal name Updated",
            cif="NEWCIF123",
            email="updated_email@test.com",
            fee=4.15,
            max_consume=8.15,
            consume_range_datetime=datetime.datetime(1998, 2, 2),
            surplus_price=5.11,
            address=AddressUpdateRequest(
                type="square",
                name="Main",
                number=3,
                postal_code="A1AB2B",
                city="Madrid",
                province="Madrid",
            ),
        ),
    )

    marketer = db_session.query(Marketer).filter(Marketer.id == 1).first()
    assert marketer.id == 1
    assert marketer.name == "Updated name"
    assert marketer.fiscal_name == "Fiscal name Updated"
    assert marketer.cif == "NEWCIF123"
    assert marketer.email == "updated_email@test.com"
    assert marketer.fee == Decimal("4.15")
    assert marketer.max_consume == Decimal("8.15")
    assert marketer.consume_range_datetime == datetime.datetime(1998, 2, 2)
    assert marketer.surplus_price == Decimal("5.11")
    assert marketer.address.id == 1
    assert marketer.address.type == "square"
    assert marketer.address.name == "Main"
    assert marketer.address.number == 3
    assert marketer.address.postal_code == "A1AB2B"
    assert marketer.address.city == "Madrid"
    assert marketer.address.province == "Madrid"


def test_marketer_update_no_address_ok(
    db_session: Session, marketer_disabled: Marketer
):
    marketer = marketer_update(
        db_session,
        3,
        MarketerUpdateRequest(
            name="Updated name",
            fiscal_name="Fiscal name Updated",
            cif="NEWCIF123",
            email="updated_email@test.com",
            fee=4.15,
            max_consume=8.15,
            consume_range_datetime=datetime.datetime(1998, 2, 2),
            surplus_price=5.11,
        ),
    )

    assert marketer.id == 3
    assert marketer.name == "Updated name"
    assert marketer.fiscal_name == "Fiscal name Updated"
    assert marketer.cif == "NEWCIF123"
    assert marketer.email == "updated_email@test.com"
    assert marketer.fee == Decimal("4.15")
    assert marketer.max_consume == Decimal("8.15")
    assert marketer.consume_range_datetime == datetime.datetime(1998, 2, 2)
    assert marketer.surplus_price == Decimal("5.11")
    assert not marketer.is_active


def test_marketer_update_empty_address_ok(
    db_session: Session, marketer_disabled: Marketer, user_create: User
):
    marketer = marketer_update(
        db_session,
        3,
        MarketerUpdateRequest(
            name="Disabled marketer",
            address=AddressUpdateRequest(),
        ),
    )
    marketer = db_session.query(Marketer).filter(Marketer.id == 3).first()
    assert marketer.id == 3
    assert marketer.name == "Disabled marketer"
    assert marketer.address
    assert not marketer.address.name
    assert not marketer.address.city


def test_marketer_update_already_exists_error(
    db_session: Session, marketer: Marketer, marketer2: Marketer
):
    with pytest.raises(HTTPException) as exc:
        marketer_update(
            db_session,
            2,
            MarketerUpdateRequest(
                name="Marketer",
                fiscal_name="Marketer official",
                cif="QWERTY123",
                email="marketer@test.com",
            ),
        )

    assert exc.value.status_code == 409
    assert exc.value.detail == "value_error.already_exists"


def test_marketer_update_not_exists(db_session: Session, marketer2: Marketer):
    with pytest.raises(HTTPException) as exc:
        marketer_update(
            db_session,
            1,
            MarketerUpdateRequest(
                name="Updated name",
                fiscal_name="Fiscal name Updated",
                cif="NEWCIF123",
                email="updated_email@test.com",
            ),
        )

    assert exc.value.detail == ("marketer_not_exist")
    marketer = db_session.query(Marketer).filter(Marketer.id == 2).first()
    assert marketer.id == 2
    assert marketer.name == "Marketer secondary"
    assert marketer.cif == "ABCDEF123"


def test_marketer_update_invalid_cif_value(db_session: Session, marketer: Marketer):
    with pytest.raises(ValidationError) as exc:
        marketer_update(
            db_session,
            1,
            MarketerUpdateRequest(
                name="Updated name",
                fiscal_name="Fiscal name Updated",
                cif="TOOLONGCIF1234",
                email="updated_email@test.com",
            ),
        )

    assert exc.value.errors()[0]["type"] == "value_error.any_str.max_length"
    assert exc.value.errors()[0]["msg"] == (
        "ensure this value has at most 9 characters"
    )
    marketer = db_session.query(Marketer).filter(Marketer.id == 1).first()
    assert marketer.cif == "QWERTY123"


def test_marketer_update_invalid_fee_value(db_session: Session, marketer: Marketer):
    with pytest.raises(ValidationError) as exc:
        marketer_update(
            db_session,
            1,
            MarketerUpdateRequest(
                name="Updated name",
                fiscal_name="Fiscal name Updated",
                cif="NEWCIF123",
                email="updated_email@test.com",
                fee="23.36521547",
            ),
        )

    assert exc.value.errors()[0]["type"] == "value_error.decimal.max_places"
    assert exc.value.errors()[0]["msg"] == (
        "ensure that there are no more than 6 decimal places"
    )
    marketer = db_session.query(Marketer).filter(Marketer.id == 1).first()
    assert marketer.fee == Decimal("15.4")


def test_marketer_partial_update_ok(db_session: Session, marketer: Marketer):
    marketer = marketer_partial_update(
        db_session, 1, MarketerPartialUpdateRequest(is_active=False, is_deleted=True)
    )

    assert marketer.id == 1
    assert not marketer.is_active
    assert marketer.is_deleted


def test_marketer_partial_update_not_used_field_ok(
    db_session: Session, marketer: Marketer
):
    marketer = marketer_partial_update(
        db_session,
        1,
        MarketerPartialUpdateRequest(is_active=False, name="Name updated"),
    )

    assert marketer.id == 1
    assert marketer.name == "Marketer"
    assert not marketer.is_active
    assert not marketer.is_deleted


def test_delete_marketers_ok(
    db_session: Session,
    marketer: Marketer,
    marketer2: Marketer,
    marketer_disabled: Marketer,
    marketer_deleted: Marketer,
):
    delete_marketers(db_session, MarketerDeleteRequest(ids=[1, 3, 4, 84]))

    assert (
        db_session.query(Marketer).filter(Marketer.is_deleted == false()).count() == 1
    )


def test_delete_marketers_empty_ok(
    db_session: Session,
    marketer: Marketer,
    marketer2: Marketer,
    marketer_disabled: Marketer,
    marketer_deleted: Marketer,
):
    delete_marketers(db_session, MarketerDeleteRequest(ids=[]))

    assert (
        db_session.query(Marketer).filter(Marketer.is_deleted == false()).count() == 3
    )
