from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.margins import (
    create_margin_db,
    get_margin_by,
    get_margin_queryset,
)
from src.modules.margins.models import Margin, MarginType
from src.modules.rates.models import Rate


def test_create_margin_db(db_session: Session, electricity_rate: Rate):
    create_margin_db(
        db_session,
        Margin(
            id=1,
            type=MarginType.consume_range,
            min_consumption=12.5,
            max_consumption=21.5,
            min_margin=16.32,
            max_margin=61.23,
            rate_id=1,
        ),
    )

    assert db_session.query(Margin).count() == 1


def test_get_margin_queryset_with_join_list(db_session: Session, margin: Rate):
    result = get_margin_queryset(db_session, [Margin.rate])
    assert result.count() == 1
    assert result.first().rate.name == "Gas rate name"


def test_get_margin_by_multiple_filters(
    margin: Margin, margin_rate_type: Margin, db_session: Session
):
    margin = get_margin_by(
        db_session,
        Margin.id == 1,
        Margin.type == "consume_range",
    )
    assert margin.id == 1
    assert margin.type == "consume_range"
    assert margin.rate_id == 2


def test_get_margin_by_without_filters(
    margin: Margin, margin_rate_type: Margin, db_session: Session
):
    margin = get_margin_by(db_session)
    assert margin.id == 1
    assert margin.type == "consume_range"
    assert margin.rate_id == 2


def test_get_margin_by_none(margin: Margin, db_session: Session):
    margin = get_margin_by(db_session, Margin.id == 1234)
    assert margin is None
