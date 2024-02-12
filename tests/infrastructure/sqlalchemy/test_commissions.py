from decimal import Decimal

from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.commissions import (
    create_commission_db,
    get_commission_by,
    get_commission_queryset,
)
from src.modules.commissions.models import Commission, RangeType
from src.modules.rates.models import Rate


def test_create_commission_db(db_session: Session, electricity_rate: Rate):
    create_commission_db(
        db_session,
        Commission(
            name="Commission name",
            range_type=RangeType.power,
            min_consumption=3.5,
            max_consumption=11.5,
            percentage_Test_commission=12,
            rate_type_segmentation=True,
            rate_type_id=1,
            rates=[electricity_rate],
        ),
    )

    assert db_session.query(Commission).count() == 1


def test_get_commission_queryset_ok(db_session: Session, commission: Commission):
    assert get_commission_queryset(db_session).count() == 1


def test_get_commission_queryset_with_join_list(
    db_session: Session, commission: Commission
):
    result = get_commission_queryset(db_session, [Commission.rates])
    assert result.count() == 1
    assert result.first().rates[0].name == "Electricity rate"


def test_get_commission_by_multiple_filters(
    commission: Commission, db_session: Session
):
    commission = get_commission_by(
        db_session,
        Commission.id == 1,
        Commission.Test_commission >= 3,
    )
    assert commission.id == 1
    assert commission.Test_commission == Decimal("12")


def test_get_commission_by_without_filters(commission: Commission, db_session: Session):
    commission = get_commission_by(db_session)
    assert commission.id == 1


def test_get_commission_by_none(commission: Commission, db_session: Session):
    commission = get_commission_by(db_session, Commission.id == 1234)
    assert commission is None
