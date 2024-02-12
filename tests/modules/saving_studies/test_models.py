from decimal import Decimal
from typing import List

import pytest

from src.modules.rates.models import EnergyType
from src.modules.saving_studies.models import SavingStudy, SuggestedRate


def test_saving_study__str__(saving_study: SavingStudy) -> None:
    assert saving_study.__str__() == "SavingStudy(id=1, cups=ES0021000000000000AA)"


def test_suggested_rate__str__(suggested_rate: SuggestedRate) -> None:
    assert suggested_rate.__str__() == "SuggestedRate(id=1, rate_name=Rate name)"


@pytest.mark.parametrize(
    "energy_type, consumptions, expected",
    [
        (
            EnergyType.electricity,
            [
                Decimal("1.00"),
                Decimal("2.00"),
                Decimal("3.00"),
                Decimal("4.00"),
                Decimal("5.00"),
                Decimal("6.00"),
            ],
            Decimal("21.00"),
        ),
        (
            EnergyType.electricity,
            [
                Decimal("1.00"),
                Decimal("2.00"),
                Decimal("3.00"),
                Decimal("4.00"),
                Decimal("5.00"),
                Decimal("1.00"),
            ],
            Decimal("16.00"),
        ),
        (
            EnergyType.electricity,
            [
                Decimal("1.00"),
                Decimal("2.00"),
                Decimal("3.00"),
                Decimal("4.00"),
                Decimal("5.00"),
                Decimal("1.00"),
            ],
            Decimal("16.00"),
        ),
        (
            EnergyType.electricity,
            [
                Decimal("1.00"),
                Decimal("2.00"),
                None,
                Decimal("4.00"),
                Decimal("5.00"),
                Decimal("1.00"),
            ],
            Decimal("13.00"),
        ),
        (EnergyType.electricity, [None, None, None, None, None, None], Decimal("0.0")),
        (
            EnergyType.gas,
            [
                Decimal("1.00"),
                Decimal("2.00"),
                Decimal("3.00"),
                Decimal("4.00"),
                Decimal("5.00"),
                Decimal("6.00"),
            ],
            Decimal("1.00"),
        ),
        (
            EnergyType.gas,
            [Decimal("1.00"), None, None, None, None, None],
            Decimal("1.00"),
        ),
    ],
)
def test_saving_study_total_consumption(
    saving_study: SavingStudy,
    energy_type: EnergyType,
    consumptions: List[str],
    expected: Decimal,
) -> None:
    saving_study.current_rate_type.energy_type = energy_type
    for i, consumption in enumerate(consumptions):
        consumption = Decimal(consumption) if consumption else None
        setattr(saving_study, f"consumption_p{i+1}", consumption)

    assert saving_study.total_consumption == expected


def test_saving_study_get_selected_rate_no_selected_rate(
    saving_study: SavingStudy, suggested_rate: SuggestedRate
):
    selected_suggested_rate = saving_study.selected_suggested_rate
    assert selected_suggested_rate is None


def test_saving_study_get_selected_rate(
    saving_study: SavingStudy, suggested_rate: SuggestedRate
):
    suggested_rate.is_selected = True
    selected_suggested_rate = saving_study.selected_suggested_rate
    assert selected_suggested_rate is not None
