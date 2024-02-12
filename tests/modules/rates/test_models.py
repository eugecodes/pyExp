import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.modules.rates.models import HistoricalRate, Rate, RateType
from src.modules.users.models import User


def test_rate__str__ok(electricity_rate: Rate) -> None:
    assert electricity_rate.__str__() == "Rate: Electricity rate"


def test_historical_rate__str__ok(historical_electricity_rate: HistoricalRate) -> None:
    assert (
        historical_electricity_rate.__str__()
        == "HistoricalRate: 1.energy_price_3 = 23.560000"
    )


def test_rate_type_constraint_error(
    db_session: Session, electricity_rate_type: RateType, user_create: User
) -> None:
    rate_type = RateType(
        id=2,
        name="Electricity rate type",
        energy_type="electricity",
        max_power=26.4,
        min_power=15.2,
        user=user_create,
    )
    db_session.add(rate_type)
    with pytest.raises(IntegrityError) as exc:
        db_session.commit()
    assert exc.value.args[0] == (
        "(psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint"
        ' "rate_type_name_energy_type_key"\nDETAIL:  Key (name, energy_type)=(Electricity rate type,'
        " electricity) already exists.\n"
    )


def test_historical_rate_constraint_error(
    db_session: Session, historical_electricity_rate: HistoricalRate
) -> None:
    historical_rate = HistoricalRate(
        id=2,
        price_name="energy_price_3",
        price=23.56,
        rate_id=1,
    )
    historical_rate.modified_at = historical_electricity_rate.modified_at
    db_session.add(historical_rate)
    with pytest.raises(IntegrityError) as exc:
        db_session.commit()
    assert exc.value.args[0].startswith(
        "(psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "
        '"historical_rate_price_name_price_modified_at_key"\nDETAIL:  Key (price_name, price, '
        "modified_at)=(energy_price_3, 23.560000"
    )
