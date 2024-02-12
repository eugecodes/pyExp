from decimal import Decimal

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import false
from sqlalchemy.orm import Session

from src.modules.costs.models import EnergyCost, OtherCost
from src.modules.costs.schemas import (
    CostDeleteRequest,
    EnergyCostCreateRequest,
    EnergyCostFilter,
    EnergyCostUpdatePartialRequest,
    OtherCostCreateUpdateRequest,
    OtherCostFilter,
    OtherCostPartialUpdateRequest,
)
from src.modules.marketers.models import Marketer
from src.modules.rates.models import Rate
from src.modules.users.models import User
from src.services.costs import (
    delete_energy_costs,
    delete_other_costs,
    energy_cost_create,
    energy_cost_partial_update,
    get_energy_cost,
    get_energy_cost_amount_range,
    get_other_cost,
    list_energy_costs,
    list_other_costs,
    other_cost_create,
    other_cost_partial_update,
    other_cost_update,
    other_cost_validate_power_range,
)


def test_energy_cost_create_ok(db_session: Session, user_create: User):
    energy_cost = energy_cost_create(
        db_session,
        EnergyCostCreateRequest(concept="Concept", amount="28.36"),
        user_create,
    )
    assert db_session.query(EnergyCost).count() == 1
    assert energy_cost.concept == "Concept"
    assert energy_cost.amount == Decimal("28.36")


def test_energy_cost_create_unique_concept_error(
    db_session: Session, user_create: User, energy_cost: EnergyCost
):
    with pytest.raises(HTTPException) as exc:
        energy_cost_create(
            db_session,
            EnergyCostCreateRequest(concept="gas installation", amount="28.36"),
            user_create,
        )
    assert exc.value.status_code == 409
    assert exc.value.detail == ("value_error.already_exists")


def test_list_energy_costs_with_filters_ok(
    db_session: Session, energy_cost: EnergyCost, energy_cost_deleted: EnergyCost
):
    assert list_energy_costs(db_session, EnergyCostFilter()).count() == 1


def test_get_energy_cost_ok(db_session: Session, energy_cost: EnergyCost):
    assert get_energy_cost(db_session, energy_cost.id)


def test_get_energy_cost_not_exist(db_session: Session, energy_cost: EnergyCost):
    with pytest.raises(HTTPException) as exc:
        get_energy_cost(db_session, 1234)
    assert exc.value.detail == ("energy_cost_not_exist")


def test_get_energy_cost_deleted(db_session: Session, energy_cost_deleted: EnergyCost):
    with pytest.raises(HTTPException) as exc:
        get_energy_cost(db_session, 4)
    assert exc.value.detail == ("energy_cost_not_exist")


def test_energy_cost_partial_update_ok(
    db_session: Session, energy_cost: EnergyCost, user_create: User
):
    energy_cost_partial_update(
        db_session,
        energy_cost.id,
        EnergyCostUpdatePartialRequest(
            concept="New concept",
            amount=15.3,
            is_active=False,
        ),
        user_create,
    )

    energy_cost = db_session.query(EnergyCost).filter(EnergyCost.id == 1).first()
    assert energy_cost.id == 1
    assert energy_cost.concept == "New concept"
    assert energy_cost.amount == Decimal("15.3")
    assert energy_cost.is_active is False


def test_energy_cost_partial_update_not_exists(
    db_session: Session, user_create: User, energy_cost2: EnergyCost
):
    with pytest.raises(HTTPException) as exc:
        energy_cost_partial_update(
            db_session,
            1,
            EnergyCostUpdatePartialRequest(
                concept="New concept",
                amount=15.3,
            ),
            user_create,
        )

    assert exc.value.detail == ("energy_cost_not_exist")
    energy_cost = db_session.query(EnergyCost).filter(EnergyCost.id == 2).first()
    assert energy_cost.id == 2
    assert energy_cost.concept == "Installation check"
    assert energy_cost.amount == Decimal("26.32")
    assert energy_cost.is_active is True


def test_energy_cost_partial_update_invalid_amount_value(
    db_session: Session, energy_cost: EnergyCost, user_create: User
):
    with pytest.raises(ValidationError) as exc:
        energy_cost_partial_update(
            db_session,
            energy_cost.id,
            EnergyCostUpdatePartialRequest(
                amount=-2.6,
            ),
            user_create,
        )

    assert exc.value.errors()[0]["msg"] == (
        "ensure this value is greater than or equal to 0"
    )
    energy_cost = db_session.query(EnergyCost).filter(EnergyCost.id == 1).first()
    assert energy_cost.concept == "gas installation"
    assert energy_cost.amount == Decimal("56.28")


def test_energy_cost_partial_update_concept_already_exists_error(
    db_session: Session,
    energy_cost: EnergyCost,
    energy_cost2: EnergyCost,
    user_create: User,
):
    with pytest.raises(HTTPException) as exc:
        energy_cost_partial_update(
            db_session,
            2,
            EnergyCostUpdatePartialRequest(
                concept="gas installation",
                amount=2.6,
            ),
            user_create,
        )

    assert exc.value.status_code == 409
    assert exc.value.detail == ("value_error.already_exists")


def test_get_energy_cost_amount_range_ok(
    db_session: Session,
    energy_cost: EnergyCost,
    energy_cost2: EnergyCost,
    energy_cost_protected: EnergyCost,
):
    range_values = get_energy_cost_amount_range(db_session)
    assert range_values["minimum_amount"] == Decimal("21")
    assert range_values["maximum_amount"] == Decimal("56.28")


def test_get_energy_cost_amount_range_no_rate_types(
    db_session: Session, energy_cost_deleted: EnergyCost
):
    range_values = get_energy_cost_amount_range(db_session)
    assert not range_values["minimum_amount"]
    assert not range_values["maximum_amount"]


def test_other_cost_create_ok(db_session: Session, electricity_rate: Rate):
    other_cost_create(
        db_session,
        OtherCostCreateUpdateRequest(
            name="Other cost",
            mandatory=True,
            client_types=["particular", "company"],
            min_power=3.5,
            max_power=23.5,
            type="eur/month",
            quantity=32,
            extra_fee=17.1,
            rates=[1],
        ),
    )

    assert db_session.query(OtherCost).count() == 1


def test_delete_energy_costs_ok(
    db_session: Session,
    user_create: User,
    energy_cost: EnergyCost,
    energy_cost2: EnergyCost,
    energy_cost_protected: EnergyCost,
    energy_cost_deleted: EnergyCost,
):
    """
    other_cost: 1
    other_cost_2_rates: 2
    other_cost_disabled: 3
    energy_cost_deleted: 4
    """
    delete_energy_costs(db_session, CostDeleteRequest(ids=[1, 2, 3, 84]), user_create)

    assert (
        db_session.query(EnergyCost).filter(EnergyCost.is_deleted == false()).count()
        == 1
    )


def test_delete_energy_costs_superadmin_ok(
    db_session: Session,
    superadmin: User,
    energy_cost: EnergyCost,
    energy_cost2: EnergyCost,
    energy_cost_protected: EnergyCost,
    energy_cost_deleted: EnergyCost,
):
    """
    other_cost: 1
    other_cost_2_rates: 2
    other_cost_disabled: 3
    energy_cost_deleted: 4
    """
    delete_energy_costs(db_session, CostDeleteRequest(ids=[1, 2, 3, 84]), superadmin)

    assert (
        db_session.query(EnergyCost).filter(EnergyCost.is_deleted == false()).count()
        == 0
    )


def test_delete_energy_costs_empty_ok(
    db_session: Session,
    user_create: User,
    energy_cost: EnergyCost,
    energy_cost2: EnergyCost,
    energy_cost_protected: EnergyCost,
    energy_cost_deleted: EnergyCost,
):
    delete_energy_costs(db_session, CostDeleteRequest(ids=[]), user_create)

    assert (
        db_session.query(EnergyCost).filter(EnergyCost.is_deleted == false()).count()
        == 3
    )


def test_other_cost_create_same_rate_twice_error(
    db_session: Session, electricity_rate: Rate
):
    with pytest.raises(ValidationError) as exc:
        other_cost_create(
            db_session,
            OtherCostCreateUpdateRequest(
                name="Other cost",
                mandatory=True,
                client_types=["particular", "company"],
                min_power=3.5,
                max_power=23.5,
                type="eur/month",
                quantity=32,
                extra_fee=17.1,
                rates=[1, 1],
            ),
        )

    assert exc.value.errors()[0]["type"] == "value_error.list.unique_items"
    assert exc.value.errors()[0]["msg"] == "the list has duplicated items"


def test_other_cost_create_empty_rates_error(db_session: Session):
    with pytest.raises(ValidationError) as exc:
        other_cost_create(
            db_session,
            OtherCostCreateUpdateRequest(
                name="Other cost",
                mandatory=True,
                client_types=["particular", "company"],
                min_power=3.5,
                max_power=23.5,
                type="eur/month",
                quantity=32,
                extra_fee=17.1,
                rates=[],
            ),
        )

    assert exc.value.errors()[0]["type"] == "value_error.list.min_items"
    assert exc.value.errors()[0]["msg"] == "ensure this value has at least 1 items"


def test_other_cost_create_different_energy_type_rates_error(
    db_session: Session, electricity_rate: Rate, gas_rate: Rate
):
    with pytest.raises(HTTPException) as exc:
        other_cost_create(
            db_session,
            OtherCostCreateUpdateRequest(
                name="Other cost",
                mandatory=True,
                client_types=["particular", "company"],
                min_power=3.5,
                max_power=23.5,
                type="eur/month",
                quantity=32,
                extra_fee=17.1,
                rates=[1, 2],
            ),
        )

    assert exc.value.detail == ("value_error.rate.invalid")


def test_other_cost_create_different_marketer_rates_error(
    db_session: Session, electricity_rate: Rate, gas_rate: Rate, marketer2: Marketer
):
    gas_rate.rate_type_id = 1
    gas_rate.marketer_id = 2

    with pytest.raises(HTTPException) as exc:
        other_cost_create(
            db_session,
            OtherCostCreateUpdateRequest(
                name="Other cost",
                mandatory=True,
                client_types=["particular", "company"],
                min_power=3.5,
                max_power=23.5,
                type="eur/month",
                quantity=32,
                extra_fee=17.1,
                rates=[1, 2],
            ),
        )

    assert exc.value.detail == ("value_error.rate.invalid")


def test_other_cost_create_rate_does_not_exist_error(
    db_session: Session, electricity_rate: Rate
):
    with pytest.raises(HTTPException) as exc:
        other_cost_create(
            db_session,
            OtherCostCreateUpdateRequest(
                name="Other cost",
                mandatory=True,
                client_types=["particular", "company"],
                min_power=3.5,
                max_power=23.5,
                type="eur/month",
                quantity=32,
                extra_fee=17.1,
                rates=[1, 1234],
            ),
        )

    assert exc.value.detail == ("value_error.rate.invalid")


def test_other_cost_create_power_range_missing_error(
    db_session: Session, electricity_rate: Rate
):
    with pytest.raises(HTTPException) as exc:
        other_cost_create(
            db_session,
            OtherCostCreateUpdateRequest(
                name="Other cost",
                mandatory=True,
                client_types=["particular", "company"],
                max_power=23.5,
                type="eur/month",
                quantity=32,
                extra_fee=17.1,
                rates=[1],
            ),
        )

    assert exc.value.detail == ("value_error.power_range.invalid")


def test_other_cost_create_power_range_invalid_error(
    db_session: Session, electricity_rate: Rate
):
    with pytest.raises(HTTPException) as exc:
        other_cost_create(
            db_session,
            OtherCostCreateUpdateRequest(
                name="Other cost",
                mandatory=True,
                client_types=["particular", "company"],
                min_power=23.5,
                max_power=3.5,
                type="eur/month",
                quantity=32,
                extra_fee=17.1,
                rates=[1],
            ),
        )

    assert exc.value.detail == ("value_error.power_range.invalid")


def test_other_cost_create_power_range_gas_rate_error(
    db_session: Session, gas_rate: Rate
):
    with pytest.raises(HTTPException) as exc:
        other_cost_create(
            db_session,
            OtherCostCreateUpdateRequest(
                name="Other cost",
                mandatory=True,
                client_types=["particular", "company"],
                min_power=3.5,
                max_power=23.5,
                type="eur/month",
                quantity=32,
                extra_fee=17.1,
                rates=[2],
            ),
        )

    assert exc.value.detail == ("value_error.rate.invalid")


def other_cost_validate_power_range_ok():
    assert other_cost_validate_power_range(3.5, 17.2, "luz") is None


def other_cost_validate_power_range_invalid_error():
    with pytest.raises(HTTPException) as exc:
        other_cost_validate_power_range(None, 3.5, "luz")

    assert exc.value.detail == ("value_error.power_range.invalid")


def other_cost_validate_power_range_power_range_invalid_error():
    with pytest.raises(HTTPException) as exc:
        other_cost_validate_power_range(None, 3.5, "gas")

    assert exc.value.detail == ("value_error.rate.invalid")


def test_get_other_cost_ok(db_session: Session, other_cost: OtherCost):
    assert get_other_cost(db_session, 1)


def test_get_other_cost_not_exist(db_session: Session, other_cost: OtherCost):
    with pytest.raises(HTTPException) as exc:
        get_other_cost(db_session, 1234)
    assert exc.value.detail == ("other_cost_not_exist")


def test_get_other_cost_deleted(db_session: Session, other_cost: OtherCost):
    other_cost.is_deleted = True

    with pytest.raises(HTTPException) as exc:
        get_other_cost(db_session, 1)

    assert exc.value.detail == ("other_cost_not_exist")


def test_other_cost_update_ok(
    db_session: Session, other_cost: OtherCost, electricity_rate_2: Rate
):
    other_cost = other_cost_update(
        db_session,
        1,
        OtherCostCreateUpdateRequest(
            name="Other cost modified",
            mandatory=False,
            client_types=["company"],
            min_power=28.2,
            max_power=32.8,
            type="percentage",
            quantity=23,
            extra_fee=71.1,
            rates=[4],
        ),
    )

    assert (
        db_session.query(OtherCost).filter(OtherCost.type == "percentage").count() == 1
    )
    assert other_cost.id == 1
    assert other_cost.name == "Other cost modified"
    assert other_cost.mandatory is False
    assert other_cost.client_types == ["company"]
    assert other_cost.min_power == Decimal("28.2")
    assert other_cost.max_power == Decimal("32.8")
    assert other_cost.type == "percentage"
    assert other_cost.quantity == 23
    assert other_cost.extra_fee == Decimal("71.1")
    assert other_cost.rates == [electricity_rate_2]
    assert other_cost.is_active is True
    assert other_cost.is_deleted is False
    assert other_cost.create_at


def test_other_cost_update_invalid_rate_error(
    db_session: Session, other_cost: OtherCost, gas_rate: Rate
):
    with pytest.raises(HTTPException) as exc:
        other_cost_update(
            db_session,
            1,
            OtherCostCreateUpdateRequest(
                name="Other cost modified",
                mandatory=False,
                client_types=["company"],
                min_power=None,
                max_power=None,
                type="percentage",
                quantity=23,
                extra_fee=71.1,
                rates=[2],
            ),
        )

    assert exc.value.detail == ("value_error.rate.invalid")
    assert db_session.query(OtherCost).filter(OtherCost.id == 1).count() == 1
    other_cost = db_session.query(OtherCost).filter(OtherCost.id == 1).first()
    assert other_cost.id == 1
    assert other_cost.name == "Other cost"


def test_list_other_costs_ok(
    db_session: Session, other_cost: OtherCost, other_cost_2_rates: OtherCost
):
    assert list_other_costs(db_session, OtherCostFilter()).count() == 2


def test_list_other_costs_empty_ok(db_session: Session, other_cost: OtherCost):
    other_cost.is_deleted = True
    assert list_other_costs(db_session, OtherCostFilter()).count() == 0


def test_other_cost_partial_update_is_active_ok(
    db_session: Session, other_cost: OtherCost
):
    other_cost_partial_update(
        db_session,
        1,
        OtherCostPartialUpdateRequest(
            is_active=False,
        ),
    )

    other_cost = db_session.query(OtherCost).filter(OtherCost.id == 1).first()
    assert other_cost.is_active is False


def test_other_cost_partial_update_is_active_not_exists(
    db_session: Session, other_cost: OtherCost
):
    with pytest.raises(HTTPException) as exc:
        other_cost_partial_update(
            db_session,
            2,
            OtherCostPartialUpdateRequest(
                is_active=False,
            ),
        )

    assert exc.value.detail == ("other_cost_not_exist")

    other_cost = db_session.query(OtherCost).filter(OtherCost.id == 1).first()
    assert other_cost.is_active is True


def test_other_cost_partial_update_is_deleted_ok(
    db_session: Session, other_cost: OtherCost
):
    other_cost_partial_update(
        db_session,
        1,
        OtherCostPartialUpdateRequest(
            is_deleted=True,
        ),
    )

    other_cost = db_session.query(OtherCost).filter(OtherCost.id == 1).first()
    assert other_cost.is_deleted is True


def test_other_cost_partial_update_is_deleted_not_exists(
    db_session: Session, other_cost: OtherCost
):
    with pytest.raises(HTTPException) as exc:
        other_cost_partial_update(
            db_session,
            2,
            OtherCostPartialUpdateRequest(
                is_deleted=True,
            ),
        )

    assert exc.value.detail == ("other_cost_not_exist")

    other_cost = db_session.query(OtherCost).filter(OtherCost.id == 1).first()
    assert other_cost.is_deleted is False


def test_delete_other_costs_ok(
    db_session: Session,
    other_cost: OtherCost,
    other_cost_2_rates: OtherCost,
    other_cost_disabled: OtherCost,
):
    """
    other_cost: 1
    other_cost_2_rates: 2
    other_cost_disabled: 3
    """
    delete_other_costs(db_session, CostDeleteRequest(ids=[1, 2, 84]))

    assert (
        db_session.query(OtherCost).filter(OtherCost.is_deleted == false()).count() == 1
    )


def test_delete_other_costs_empty_ok(
    db_session: Session,
    other_cost: OtherCost,
    other_cost_2_rates: OtherCost,
    other_cost_disabled: OtherCost,
):
    delete_other_costs(db_session, CostDeleteRequest(ids=[]))

    assert (
        db_session.query(OtherCost).filter(OtherCost.is_deleted == false()).count() == 3
    )
