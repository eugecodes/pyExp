from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import false

from src.infrastructure.sqlalchemy.margins import get_margin_queryset
from src.modules.margins.models import Margin
from src.modules.margins.schemas import (
    MarginCreateRequest,
    MarginDeleteRequest,
    MarginFilter,
    MarginPartialUpdateRequest,
    MarginUpdateRequest,
)
from src.modules.rates.models import Rate
from src.services.margins import (
    check_consumption_range_overlap,
    delete_margins,
    get_margin,
    list_margins,
    margin_create,
    margin_partial_update,
    margin_update,
)


def test_check_consumption_range_overlap_ok(db_session: Session, margin: Margin):
    margin_qs = get_margin_queryset(
        db_session,
        None,
        Margin.rate_id == 2,
        Margin.is_deleted == false(),
    )

    assert check_consumption_range_overlap(margin_qs, 2.3, 7.2) is None


def test_check_consumption_range_overlap_error(db_session: Session, margin: Margin):
    margin_qs = get_margin_queryset(
        db_session,
        None,
        Margin.rate_id == 2,
        Margin.is_deleted == false(),
    )

    with pytest.raises(HTTPException) as exc:
        check_consumption_range_overlap(margin_qs, 7.2, 17.5)

    assert exc.value.detail == ("value_error.consumption_range.overlap")


def test_check_consumption_range_overlap_same_range_error(
    db_session: Session, margin: Margin
):
    margin_qs = get_margin_queryset(
        db_session,
        None,
        Margin.rate_id == 2,
        Margin.is_deleted == false(),
    )

    with pytest.raises(HTTPException) as exc:
        check_consumption_range_overlap(margin_qs, 12.5, 21.5)

    assert exc.value.detail == ("value_error.consumption_range.overlap")


def test_margin_create_ok(db_session: Session, gas_rate: Rate):
    margin_create(
        db_session,
        MarginCreateRequest(
            type="rate_type",
            rate_id=2,
            min_margin=28.3,
            max_margin=38.2,
        ),
    )

    assert db_session.query(Margin).count() == 1


def test_margin_create_margin_with_other_type_exists_error(
    db_session: Session, margin: Margin
):
    with pytest.raises(HTTPException) as exc:
        margin_create(
            db_session,
            MarginCreateRequest(
                type="rate_type",
                rate_id=2,
                min_margin=28.3,
                max_margin=38.2,
            ),
        )

    assert db_session.query(Margin).count() == 1
    assert exc.value.detail == ("value_error.type.already_exist_other_type")


def test_margin_create_rate_invalid_price_type_error(
    db_session: Session, electricity_rate: Rate
):
    with pytest.raises(HTTPException) as exc:
        margin_create(
            db_session,
            MarginCreateRequest(
                type="rate_type",
                rate_id=1,
                min_margin=28.3,
                max_margin=38.2,
            ),
        )

    assert db_session.query(Margin).count() == 0
    assert exc.value.detail == ("rate_not_exist")


def test_margin_create_consumption_range_overlap_error(
    db_session: Session, margin: Margin
):
    with pytest.raises(HTTPException) as exc:
        margin_create(
            db_session,
            MarginCreateRequest(
                type="consume_range",
                rate_id=2,
                min_consumption=3.24,
                max_consumption=18.56,
                min_margin=28.3,
                max_margin=38.2,
            ),
        )

    assert db_session.query(Margin).count() == 1
    assert exc.value.detail == ("value_error.consumption_range.overlap")


def test_margin_create_consumption_range_including_range_overlap_error(
    db_session: Session, margin: Margin
):
    with pytest.raises(HTTPException) as exc:
        margin_create(
            db_session,
            MarginCreateRequest(
                type="consume_range",
                rate_id=2,
                min_consumption=3.24,
                max_consumption=180.56,
                min_margin=28.3,
                max_margin=38.2,
            ),
        )

    assert db_session.query(Margin).count() == 1
    assert exc.value.detail == ("value_error.consumption_range.overlap")


def test_margin_create_consumption_range_existing_overlap_error(
    db_session: Session, margin: Margin
):
    with pytest.raises(HTTPException) as exc:
        margin_create(
            db_session,
            MarginCreateRequest(
                type="consume_range",
                rate_id=2,
                min_consumption=12.5,
                max_consumption=21.5,
                min_margin=28.3,
                max_margin=38.2,
            ),
        )

    assert db_session.query(Margin).count() == 1
    assert exc.value.detail == ("value_error.consumption_range.overlap")


def test_get_margin_ok(db_session: Session, margin: Margin):
    assert get_margin(db_session, 1)


def test_get_margin_not_exist(db_session: Session, margin: Margin):
    with pytest.raises(HTTPException) as exc:
        get_margin(db_session, 1234)
    assert exc.value.detail == ("margin_not_exist")


def test_get_margin_deleted(db_session: Session, margin: Margin):
    margin.is_deleted = True

    with pytest.raises(HTTPException) as exc:
        get_margin(db_session, 1)

    assert exc.value.detail == ("margin_not_exist")


def test_margin_update_ok(db_session: Session, margin: Margin):
    margin = margin_update(
        db_session,
        1,
        MarginUpdateRequest(
            min_consumption=2.6,
            max_consumption=6.2,
            min_margin=5.8,
            max_margin=8.5,
        ),
    )

    assert margin.id == 1
    assert margin.type == "consume_range"
    assert margin.min_consumption == Decimal("2.6")
    assert margin.max_consumption == Decimal("6.2")
    assert margin.min_margin == Decimal("5.8")
    assert margin.max_margin == Decimal("8.5")
    assert margin.create_at
    assert margin.rate_id == 2


def test_margin_update_rate_type_margin_ok(
    db_session: Session, margin_rate_type: Margin
):
    margin = margin_update(
        db_session,
        2,
        MarginUpdateRequest(
            min_margin=5.8,
            max_margin=8.5,
        ),
    )

    assert margin.id == 2
    assert margin.type == "rate_type"
    assert margin.min_consumption is None
    assert margin.max_consumption is None
    assert margin.min_margin == Decimal("5.8")
    assert margin.max_margin == Decimal("8.5")
    assert margin.create_at
    assert margin.rate_id == 1


def test_margin_update_not_found_error(db_session: Session):
    with pytest.raises(HTTPException) as exc:
        margin_update(
            db_session,
            1,
            MarginUpdateRequest(
                min_consumption=2.6,
                max_consumption=6.2,
                min_margin=5.8,
                max_margin=8.5,
            ),
        )

    assert exc.value.detail == ("margin_not_exist")


def test_margin_update_rate_type_margin_consumption_range_ok(
    db_session: Session, margin_rate_type: Margin
):
    margin = margin_update(
        db_session,
        2,
        MarginUpdateRequest(
            min_consumption=2.6,
            max_consumption=6.2,
            min_margin=5.8,
            max_margin=8.5,
        ),
    )

    assert margin.id == 2
    assert margin.min_consumption is None
    assert margin.max_consumption is None
    assert margin.min_margin == Decimal("5.8")
    assert margin.max_margin == Decimal("8.5")


def test_margin_update_consumption_range_overlap_error(
    db_session: Session, margin: Margin, margin_consume_range: Margin
):
    with pytest.raises(HTTPException) as exc:
        margin_update(
            db_session,
            3,
            MarginUpdateRequest(
                min_consumption=9.3,
                max_consumption=18.3,
                min_margin=5.8,
                max_margin=8.5,
            ),
        )

    assert exc.value.detail == ("value_error.consumption_range.overlap")


def test_list_margins_ok(
    db_session: Session, margin: Margin, margin_consume_range: Margin
):
    assert list_margins(db_session, MarginFilter()).count() == 2


def test_list_margins_empty_ok(db_session: Session, margin: Margin):
    margin.is_deleted = True
    assert list_margins(db_session, MarginFilter()).count() == 0


def test_margin_partial_update_ok(db_session: Session, margin: Margin):
    margin_partial_update(
        db_session,
        1,
        MarginPartialUpdateRequest(
            is_deleted=True,
        ),
    )

    margin = db_session.query(Margin).filter(Margin.id == 1).first()
    assert margin.is_deleted is True


def test_margin_partial_update_not_exists(db_session: Session, margin: Margin):
    with pytest.raises(HTTPException) as exc:
        margin_partial_update(
            db_session,
            2,
            MarginPartialUpdateRequest(
                is_deleted=True,
            ),
        )

    assert exc.value.detail == ("margin_not_exist")

    margin = db_session.query(Margin).filter(Margin.id == 1).first()
    assert margin.is_deleted is False


def test_delete_margins_ok(
    db_session: Session,
    margin: Margin,
    margin_consume_range: Margin,
    margin_rate_type: Margin,
):
    delete_margins(db_session, MarginDeleteRequest(ids=[1, 2, 6, 84]))

    assert db_session.query(Margin).filter(Margin.is_deleted == false()).count() == 1


def test_delete_margins_empty_ok(
    db_session: Session,
    margin: Margin,
    margin_consume_range: Margin,
    margin_rate_type: Margin,
):
    delete_margins(db_session, MarginDeleteRequest(ids=[]))

    assert db_session.query(Margin).filter(Margin.is_deleted == false()).count() == 3
