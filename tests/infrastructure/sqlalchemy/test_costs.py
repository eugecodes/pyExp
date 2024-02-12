from decimal import Decimal

from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.costs import (
    create_energy_cost_db,
    create_other_cost_db,
    get_energy_cost_by,
    get_energy_costs_queryset,
    get_other_cost_by,
    get_other_cost_queryset,
)
from src.modules.costs.models import EnergyCost, OtherCost
from src.modules.rates.models import Rate
from src.modules.users.models import User


def test_create_energy_cost_db(db_session: Session, user_create: User):
    create_energy_cost_db(
        db_session, EnergyCost(concept="IVA", amount=21.0, user=user_create)
    )

    assert db_session.query(EnergyCost).count() == 1


def test_get_energy_costs_queryset_ok(db_session: Session, energy_cost: EnergyCost):
    assert get_energy_costs_queryset(db_session).count() == 1


def test_get_energy_costs_queryset_with_join_list(
    db_session: Session, energy_cost: EnergyCost
):
    result = get_energy_costs_queryset(db_session, [EnergyCost.user])
    assert result.count() == 1
    assert result.first().user.first_name == "John"


def test_get_energy_cost_by_one_field(energy_cost: EnergyCost, db_session: Session):
    energy_cost = get_energy_cost_by(db_session, EnergyCost.id == 1)
    assert energy_cost.id == 1


def test_get_energy_cost_by_multiple_fields(
    energy_cost: EnergyCost, db_session: Session
):
    energy_cost = get_energy_cost_by(
        db_session,
        EnergyCost.id == 1,
        EnergyCost.concept == "gas installation",
        EnergyCost.amount == 56.28,
    )
    assert energy_cost.id == 1
    assert energy_cost.concept == "gas installation"
    assert energy_cost.amount == Decimal("56.28")


def test_get_energy_cost_by_without_fields(
    energy_cost: EnergyCost, db_session: Session
):
    energy_cost = get_energy_cost_by(db_session)
    assert energy_cost.id == 1
    assert energy_cost.concept == "gas installation"
    assert energy_cost.amount == Decimal("56.28")


def test_get_energy_cost_by_none(energy_cost: EnergyCost, db_session: Session):
    energy_cost = get_energy_cost_by(db_session, EnergyCost.id == 1234)
    assert energy_cost is None


def test_create_other_cost_db(db_session: Session, electricity_rate: Rate):
    create_other_cost_db(
        db_session,
        OtherCost(
            name="Other cost",
            mandatory=True,
            client_types=["particular", "company"],
            min_power=3.5,
            max_power=23.5,
            type="eur/month",
            quantity=32,
            extra_fee=17.1,
            rates=[electricity_rate],
        ),
    )

    assert db_session.query(OtherCost).count() == 1


def test_get_other_cost_queryset_ok(db_session: Session, other_cost: OtherCost):
    assert get_other_cost_queryset(db_session).count() == 1


def test_get_other_cost_queryset_with_join_list(
    db_session: Session, other_cost: OtherCost
):
    result = get_other_cost_queryset(db_session, [OtherCost.rates])
    assert result.count() == 1
    assert result.first().rates[0].name == "Electricity rate"


def test_get_other_cost_by_multiple_filters(other_cost: OtherCost, db_session: Session):
    other_cost = get_other_cost_by(
        db_session,
        OtherCost.id == 1,
        OtherCost.min_power >= 3,
    )
    assert other_cost.id == 1
    assert other_cost.min_power == 3.5


def test_get_other_cost_by_without_filters(other_cost: OtherCost, db_session: Session):
    other_cost = get_other_cost_by(db_session)
    assert other_cost.id == 1
    assert other_cost.min_power == 3.5


def test_get_other_cost_by_none(other_cost: OtherCost, db_session: Session):
    other_cost = get_other_cost_by(db_session, OtherCost.id == 1234)
    assert other_cost is None
