from sqlalchemy.orm import Session

from src.modules.costs.models import EnergyCost, OtherCost


def test_energy_cost__str__(energy_cost: EnergyCost) -> None:
    assert energy_cost.__str__() == "EnergyCost: gas installation"


def test_energy_cost_create_at_distinct(
    db_session: Session, energy_cost: EnergyCost
) -> None:
    energy_cost_2 = EnergyCost(
        id=2,
        concept="electricity installation",
        amount=200.0,
        is_active=True,
        is_deleted=False,
        user_id=1,
    )
    db_session.add(energy_cost_2)
    db_session.commit()

    assert energy_cost_2.create_at != energy_cost.create_at


def test_other_cost__str__(other_cost: OtherCost) -> None:
    assert other_cost.__str__() == "OtherCost: Other cost"
    assert other_cost.client_types[0].name == "particular"
    assert other_cost.client_types[1].name == "company"
    assert other_cost.rates[0].name == "Electricity rate"
