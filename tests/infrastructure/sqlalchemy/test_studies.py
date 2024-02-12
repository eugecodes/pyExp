from typing import Any, List

import pytest
from sqlalchemy import true
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import false

from src.infrastructure.sqlalchemy.studies import (
    create_saving_study_db,
    delete_study_suggested_rates,
    finish_study_db,
    get_candidate_rates,
    get_other_costs_rate_study,
    get_saving_studies_queryset,
)
from src.modules.costs.models import OtherCost
from src.modules.rates.models import ClientType, EnergyType, PriceType, Rate, RateType
from src.modules.saving_studies.models import (
    SavingStudy,
    SavingStudyStatusEnum,
    SuggestedRate,
)
from src.modules.users.models import User


def test_create_saving_studies_db(
    db_session: Session, user_create: User, electricity_rate_type: RateType
):
    create_saving_study_db(
        db_session,
        SavingStudy(
            cups="test_cups",
            energy_type=EnergyType.electricity,
            is_existing_client=False,
            is_from_sips=False,
            is_compare_conditions=False,
            analyzed_days=100,
            user_creator_id=1,
            current_rate_type_id=1,
            energy_price_1=99.50,
            client_type=ClientType.particular,
        ),
    )

    assert db_session.query(SavingStudy).count() == 1


def test_create_saving_studies_db_current_rate_type_id_null(
    db_session: Session, user_create: User, electricity_rate_type: RateType
):
    create_saving_study_db(
        db_session,
        SavingStudy(
            cups="test_cups",
            energy_type=EnergyType.electricity,
            is_existing_client=False,
            is_from_sips=False,
            is_compare_conditions=False,
            analyzed_days=100,
            user_creator_id=1,
            energy_price_1=99.50,
            client_type=ClientType.particular,
        ),
    )

    assert db_session.query(SavingStudy).count() == 1


def test_get_saving_studies_types_queryset(
    db_session: Session, saving_study: SavingStudy
) -> None:
    assert get_saving_studies_queryset(db_session).count() == 1


def test_get_saving_studies_queryset_with_join_list(
    db_session: Session, saving_study: SavingStudy
) -> None:
    assert (
        get_saving_studies_queryset(db_session, [SavingStudy.user_creator]).count() == 1
    )


def test_get_saving_studies_queryset_with_join_list_and_filter(
    db_session: Session, saving_study: SavingStudy
) -> None:
    assert (
        get_saving_studies_queryset(
            db_session, [SavingStudy.user_creator], SavingStudy.is_deleted == false()
        ).count()
        == 1
    )


@pytest.mark.parametrize(
    "energy_type, price_type, expected",
    [
        (EnergyType.electricity, PriceType.fixed_base, 1),
        (EnergyType.electricity, PriceType.fixed_fixed, 1),
        (EnergyType.gas, PriceType.fixed_fixed, 1),
        (EnergyType.gas, PriceType.fixed_base, 1),
    ],
)
def test_get_candidate_rates_in_range(
    db_session: Session,
    saving_study: SavingStudy,
    energy_type: EnergyType,
    price_type: PriceType,
    expected: int,
) -> None:
    saving_study.annual_consumption = 1000.12
    saving_study.power_2 = 200
    saving_study.current_rate_type.energy_type = energy_type
    electricity_rate = db_session.query(Rate).first()
    electricity_rate.min_consumption = 100
    electricity_rate.max_consumption = 10000
    electricity_rate.min_power = 100
    electricity_rate.max_power = 10000
    electricity_rate.energy_type = energy_type
    electricity_rate.price_type = price_type
    electricity_rate.price_type = PriceType.fixed_base
    db_session.add_all([saving_study, saving_study.current_rate_type, electricity_rate])
    db_session.commit()

    candidate_rates = get_candidate_rates(db_session, saving_study.id)

    assert candidate_rates.count() == expected


@pytest.mark.parametrize(
    "energy_type, price_type, expected",
    [
        # (EnergyType.electricity, PriceType.fixed_base, 1), # Don't see range
        (EnergyType.electricity, PriceType.fixed_fixed, 0),
        # (EnergyType.gas, PriceType.fixed_fixed, 0),
        # (EnergyType.gas, PriceType.fixed_base, 0),
    ],
)
def test_get_candidate_rates_out_of_range(
    db_session: Session,
    saving_study: SavingStudy,
    energy_type: EnergyType,
    price_type: PriceType,
    expected: int,
) -> None:
    saving_study.annual_consumption = 10
    saving_study.power_2 = 1
    saving_study.current_rate_type.energy_type = energy_type
    electricity_rate = db_session.query(Rate).first()
    electricity_rate.min_consumption = 100
    electricity_rate.max_consumption = 10000
    electricity_rate.min_power = 100
    electricity_rate.max_power = 10000
    electricity_rate.energy_type = energy_type
    electricity_rate.price_type = price_type
    db_session.add_all([saving_study, saving_study.current_rate_type, electricity_rate])
    db_session.commit()

    candidate_rates = get_candidate_rates(db_session, saving_study.id)

    assert candidate_rates.count() == expected


@pytest.mark.parametrize(
    "is_deleted, is_active, expected",
    [
        (True, True, 0),
        (False, False, 0),
        (True, False, 0),
        (False, True, 1),
    ],
)
def test_get_candidate_rates_rate(
    db_session: Session,
    saving_study: SavingStudy,
    is_deleted: bool,
    is_active: bool,
    expected: int,
) -> None:
    rate = saving_study.current_rate_type.rate
    rate.is_deleted = is_deleted
    rate.is_active = is_active
    db_session.add(rate)
    db_session.commit()

    assert get_candidate_rates(db_session, saving_study.id).count() == expected


def test_get_candidate_rates_rate_without_power_range(
    db_session: Session,
    saving_study: SavingStudy,
) -> None:
    rate = saving_study.current_rate_type.rate
    rate.min_power = None
    rate.max_power = None
    db_session.add(rate)
    db_session.commit()

    assert get_candidate_rates(db_session, saving_study.id).count() == 1


def test_get_candidate_rates_rate_type_energy_type_no_same(
    db_session: Session, saving_study: SavingStudy, gas_rate_active: Rate
) -> None:
    rates = get_candidate_rates(db_session, saving_study.id)

    assert rates.count() == 1
    assert (
        rates.first().rate_type.energy_type == "electricity"
    )  # gas_rate_active is not suggested because it is not electricity


@pytest.mark.parametrize(
    "is_deleted, enable, expected",
    [
        (True, True, 0),
        (False, False, 0),
        (True, False, 0),
        (False, True, 1),
    ],
)
def test_get_candidate_rates_rate_type(
    db_session: Session,
    saving_study: SavingStudy,
    is_deleted: bool,
    enable: bool,
    expected: int,
) -> None:
    rate_type = saving_study.current_rate_type
    rate_type.enable = enable
    rate_type.is_deleted = is_deleted
    db_session.add(rate_type)
    db_session.add(saving_study)
    db_session.commit()

    assert get_candidate_rates(db_session, saving_study.id).count() == expected


@pytest.mark.parametrize(
    "is_deleted, is_active, expected",
    [
        (True, True, 0),
        (False, False, 0),
        (True, False, 0),
        (False, True, 1),
    ],
)
def test_get_candidate_rates_marketer(
    db_session: Session,
    saving_study: SavingStudy,
    is_deleted: bool,
    is_active: bool,
    expected: int,
) -> None:
    marketer = saving_study.current_rate_type.rate.marketer
    marketer.is_deleted = is_deleted
    marketer.is_active = is_active
    db_session.add(marketer)
    db_session.add(saving_study)
    db_session.commit()

    assert get_candidate_rates(db_session, saving_study.id).count() == expected


def test_get_candidate_rates_client_type_not_in_list(
    db_session: Session, saving_study: SavingStudy
) -> None:
    saving_study.client_type = ClientType.company
    db_session.add(saving_study)
    db_session.commit()

    assert get_candidate_rates(db_session, saving_study.id).count() == 0


@pytest.mark.parametrize(
    "power_6, power_2, expected",
    [
        # valid values are in [2.5, 23.39]
        (5.5, None, 1),  # Ok
        (1.1, None, 0),  # p6 too low
        (1000.23, None, 0),  # p6 too high
        (None, 5, 1),  # No 06 but p2 ok
        (None, 1, 0),  # not p6 and p2 too low
        (None, 1000.23, 0),  # not p6 and p2 too high
        (None, None, 0),  # not p6 and not p2, defualt value is 0. 0 is out of range
    ],
)
def test_get_candidate_rates_power(
    db_session: Session,
    saving_study: SavingStudy,
    power_6: int | None,
    power_2: int | None,
    expected: int,
) -> None:
    saving_study.power_6 = power_6
    saving_study.power_2 = power_2
    db_session.add(saving_study)
    db_session.commit()

    assert get_candidate_rates(db_session, saving_study.id).count() == expected


def test_study_no_selected_suggested_rates_ok(
    db_session: Session, suggested_rates: List[SuggestedRate]
):
    delete_study_suggested_rates(db_session, suggested_rates[0].saving_study_id)

    assert (
        db_session.query(SuggestedRate)
        .filter(SuggestedRate.saving_study_id == suggested_rates[0].saving_study_id)
        .count()
        == 0
    )


def test_get_other_costs_by_rate_study(
    db_session: Session,
    saving_study: SavingStudy,
    electricity_rate: Rate,
    other_cost: OtherCost,
):
    other_cost.rate = electricity_rate
    db_session.add(other_cost)
    db_session.add(electricity_rate)
    db_session.commit()

    assert (
        get_other_costs_rate_study(
            db_session, saving_study, electricity_rate.id
        ).count()
        == 1
    )


@pytest.mark.parametrize(
    "field, value, expected",
    [
        ("is_deleted", True, 0),
        ("is_active", False, 0),
        ("rates", [], 0),
        ("mandatory", False, 0),
        ("min_power", 2000, 0),
        ("max_power", 1, 0),
    ],
)
def test_get_other_costs_by_rate_study_filter_other_costs(
    db_session: Session,
    saving_study: SavingStudy,
    electricity_rate: Rate,
    other_cost: OtherCost,
    field: str,
    value: Any,
    expected: int,
):
    other_cost.rate = electricity_rate
    setattr(other_cost, field, value)
    db_session.add(other_cost)
    db_session.add(electricity_rate)
    db_session.add(saving_study)
    db_session.commit()

    assert (
        get_other_costs_rate_study(
            db_session, saving_study, electricity_rate.id
        ).count()
        == expected
    )


def test_get_other_cost_by_rate_study_fields(
    db_session: Session,
    saving_study: SavingStudy,
    electricity_rate: Rate,
    other_cost: OtherCost,
):
    other_cost.rate = electricity_rate
    saving_study.client_type = ClientType.community_owners
    db_session.add(other_cost)
    db_session.add(electricity_rate)
    db_session.add(saving_study)
    db_session.commit()

    assert (
        get_other_costs_rate_study(
            db_session, saving_study, electricity_rate.id
        ).count()
        == 0
    )


@pytest.mark.parametrize(
    "power_2, power_6, expected",
    # Aceptance tange 3.5-23.5
    [
        (0, 0, 0),
        (0, 5.75, 1),
        (5.75, 0, 1),
        (5.75, 5.75, 1),
        (3.5, 0, 1),
        (0, 3.5, 1),
        (23.5, 0, 1),
        (0, 23.5, 1),
        (100, 5.75, 0),
        (0, 100, 0),
    ],
)
def test_get_other_cost_by_rate_power_p2(
    db_session: Session,
    saving_study: SavingStudy,
    electricity_rate: Rate,
    other_cost: OtherCost,
    power_2: int,
    power_6: int,
    expected: int,
):
    other_cost.rate = electricity_rate
    saving_study.power_6 = 0
    saving_study.power_2 = 5.75
    db_session.add(other_cost)
    db_session.add(electricity_rate)
    db_session.add(saving_study)
    db_session.commit()

    assert (
        get_other_costs_rate_study(
            db_session, saving_study, electricity_rate.id
        ).count()
        == 1
    )


def test_finish_saving_study_ok(
    db_session: Session, saving_study: SavingStudy, suggested_rates: List[SuggestedRate]
):
    saving_study, suggested_rate = finish_study_db(
        db_session, saving_study, suggested_rates[0]
    )

    assert saving_study.status == SavingStudyStatusEnum.COMPLETED
    assert (
        db_session.query(SuggestedRate)
        .filter(SuggestedRate.is_selected == true())
        .count()
        == 1
    )
