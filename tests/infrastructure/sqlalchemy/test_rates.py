from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import true

from src.infrastructure.sqlalchemy.rates import (
    create_rate_db,
    create_rate_type_db,
    get_rate_by,
    get_rate_queryset,
    get_rate_type_by,
    get_rate_types_queryset,
)
from src.modules.marketers.models import Marketer
from src.modules.rates.models import ClientType, PriceType, Rate, RateType
from src.modules.users.models import User


def test_create_rate_type_db(db_session: Session, user_create: User) -> None:
    create_rate_type_db(db_session, RateType(name="name", energy_type="gas", user_id=1))

    assert db_session.query(RateType).count() == 1


def test_get_rate_types_queryset(db_session: Session, gas_rate_type: RateType) -> None:
    assert get_rate_types_queryset(db_session).count() == 1


def test_get_rate_types_queryset_with_join_list(
    db_session: Session, gas_rate_type: RateType
) -> None:
    assert get_rate_types_queryset(db_session, [RateType.user]).count() == 1


def test_get_rate_types_queryset_with_join_list_and_filter(
    db_session: Session, gas_rate_type: RateType, disable_rate_type: RateType
) -> None:
    assert (
        get_rate_types_queryset(
            db_session, [RateType.user], RateType.enable == true()
        ).count()
        == 1
    )


def test_get_rate_type_by_one_filter(
    electricity_rate_type: RateType, db_session: Session
) -> None:
    rate_type = get_rate_type_by(db_session, RateType.id == 1)
    assert rate_type.id == 1


def test_get_rate_type_by_multiple_filters(
    electricity_rate_type: RateType, gas_rate_type: RateType, db_session: Session
) -> None:
    rate_type = get_rate_type_by(
        db_session,
        RateType.id == 1,
        RateType.name == "Electricity rate type",
        RateType.energy_type == "electricity",
    )
    assert rate_type.id == 1
    assert rate_type.name == "Electricity rate type"
    assert rate_type.energy_type == "electricity"


def test_get_rate_type_by_without_filters(
    electricity_rate_type: RateType, gas_rate_type: RateType, db_session: Session
) -> None:
    rate_type = get_rate_type_by(db_session)
    assert rate_type.id == 1
    assert rate_type.name == "Electricity rate type"
    assert rate_type.energy_type == "electricity"


def test_get_rate_type_by_none(electricity_rate_type: RateType, db_session: Session):
    rate_type = get_rate_type_by(db_session, RateType.id == 1234)
    assert rate_type is None


def test_create_rate_db(
    db_session: Session, gas_rate_type: RateType, marketer: Marketer
) -> None:
    create_rate_db(
        db_session,
        Rate(
            name="gas rate",
            price_type=PriceType.fixed_fixed,
            client_types=[ClientType.particular],
            energy_price_1=22.5,
            fixed_term_price=22.5,
            permanency=True,
            length=12,
            rate_type=gas_rate_type,
            marketer=marketer,
        ),
    )

    assert db_session.query(Rate).count() == 1


def test_get_rate_by_one_filter(electricity_rate: Rate, db_session: Session) -> None:
    rate = get_rate_by(db_session, Rate.id == 1)
    assert rate.id == 1


def test_get_rate_by_multiple_filters(
    electricity_rate: Rate, db_session: Session
) -> None:
    rate = get_rate_by(
        db_session,
        Rate.id == 1,
        Rate.name == "Electricity rate",
        Rate.min_power == 10.5,
    )
    assert rate.id == 1
    assert rate.name == "Electricity rate"
    assert rate.min_power == Decimal("10.5")


def test_get_rate_by_without_filters(
    electricity_rate: Rate, db_session: Session
) -> None:
    rate = get_rate_by(db_session)
    assert rate.id == 1
    assert rate.name == "Electricity rate"
    assert rate.min_power == Decimal("10.5")


def test_get_rate_by_none(electricity_rate: Rate, db_session: Session) -> None:
    rate = get_rate_by(db_session, Rate.id == 1234)
    assert rate is None


def test_get_marketer_queryset_ok(db_session: Session, electricity_rate: Rate) -> None:
    assert get_rate_queryset(db_session).count() == 1


def test_get_rate_queryset_with_join_list(
    db_session: Session, electricity_rate: Rate
) -> None:
    result = get_rate_queryset(db_session, [Rate.rate_type])
    assert result.count() == 1
    assert result.first().rate_type.name == "Electricity rate type"
