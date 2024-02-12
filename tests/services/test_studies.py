from decimal import Decimal
from typing import List
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from sqlalchemy import true
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.modules.commissions.models import Commission, MarginType
from src.modules.costs.models import EnergyCost, OtherCost, OtherCostType
from src.modules.margins.models import Margin
from src.modules.rates.models import EnergyType, PriceType, Rate, RateType
from src.modules.saving_studies.models import (
    SavingStudy,
    SavingStudyStatusEnum,
    SuggestedRate,
)
from src.modules.saving_studies.schemas import (
    CostCalculatorInfo,
    SavingStudyDeleteRequest,
    SavingStudyFilter,
    SavingStudyRequest,
    SuggestedRateCosts,
    SuggestedRateFilter,
    SuggestedRateUpdate,
)
from src.modules.users.models import User
from src.services.studies import (
    CalculatorsFactory,
    ComissionCalculatorFixedBase,
    ComissionCalculatorFixedFixed,
    CostCalculatorElectricity,
    CostCalculatorGas,
    SuggestedRatesGenerator,
    delete_saving_study,
    duplicate_saving_study,
    finish_saving_study,
    generate_suggested_rates_for_study,
    get_saving_study,
    list_saving_studies,
    list_suggested_rates,
    saving_study_create,
    saving_study_update,
    suggested_rate_update,
    validate_saving_study_before_generating_rates,
    validate_suggested_rate_for_update,
)


@patch("src.services.studies.validate_saving_study_before_generating_rates")
def test_generate_rates_for_study_ok(
    mock_validator,
    db_session: Session,
    saving_study: SavingStudy,
) -> None:
    mock_validator.return_value = None
    saving_study.annual_consumption = 15
    saving_study.power_6 = 10
    saving_study.power_2 = 10

    suggested_rates = generate_suggested_rates_for_study(db_session, saving_study.id)

    assert len(suggested_rates) == 1
    assert suggested_rates[0].rate_name == "Electricity rate active marketer"


@patch("src.services.studies.validate_saving_study_before_generating_rates")
def test_generate_rates_for_study_ok_rate_power_range_null(
    mock_validator,
    db_session: Session,
    saving_study: SavingStudy,
    electricity_rate_active_marketer: Rate,
) -> None:
    mock_validator.return_value = None
    electricity_rate_active_marketer.min_power = None
    electricity_rate_active_marketer.max_power = None
    db_session.commit()
    saving_study.annual_consumption = 15
    saving_study.power_6 = 10
    saving_study.power_2 = 10

    suggested_rates = generate_suggested_rates_for_study(db_session, saving_study.id)

    assert len(suggested_rates) == 1
    assert suggested_rates[0].rate_name == "Electricity rate active marketer"


def test_generate_rates_for_study_no_study(
    db_session: Session,
) -> None:
    with pytest.raises(HTTPException):
        generate_suggested_rates_for_study(db_session, 1)


@patch("src.services.studies.validate_saving_study_before_generating_rates")
def test_generate_rates_for_study_no_rate_type(
    mock_validator,
    db_session: Session,
    saving_study: SavingStudy,
    electricity_rate_type: RateType,
) -> None:
    mock_validator.return_value = None
    electricity_rate_type.is_deleted = True
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        generate_suggested_rates_for_study(db_session, saving_study.id)

    assert exc.value.status_code == 404
    assert exc.value.detail == "rate_type_not_exist"


@patch("src.services.studies.SuggestedRatesGenerator.generate_suggested_rates")
@patch("src.services.studies.validate_saving_study_before_generating_rates")
def test_generate_rates_for_study_numeric_overflow(
    mock_validator, mock_rates, db_session: Session, saving_study: SavingStudy
) -> None:
    saving_study.annual_consumption = 15
    saving_study.power_6 = 10
    saving_study.power_2 = 10

    suggested_rate = SuggestedRate(
        id=1,
        saving_study_id=saving_study.id,
        marketer_name="Marketer name",
        has_contractual_commitment=True,
        duration=12,
        rate_name="Rate name",
        is_full_renewable=True,
        has_net_metering=True,
        net_metering_value=12.3,
        applied_profit_margin=12.3,
        min_profit_margin=16.3,
        max_profit_margin=61.2,
        profit_margin_type=MarginType.rate_type,
        is_selected=False,
        energy_price_1=112.3,
        power_price_1=23.4,
        final_cost=10e15,
    )

    mock_validator.return_value = None
    mock_rates.return_value = [suggested_rate]
    with pytest.raises(HTTPException) as exc:
        generate_suggested_rates_for_study(db_session, saving_study.id)

    assert exc.value.status_code == 500
    assert exc.value.detail == "value_error.numeric_field_overflow"


class TestSuggestedRatesGenerator:
    def test___init__(self, db_session: Session, saving_study: SavingStudy) -> None:
        suggested_rates_generator = SuggestedRatesGenerator(
            db_session=db_session, saving_study=saving_study
        )

        assert suggested_rates_generator.db_session == db_session
        assert suggested_rates_generator.saving_study == saving_study

    def test_get_default_margin_rate_unique_margin_consume(
        self,
        db_session: Session,
        electricity_rate: Rate,
        margin: Margin,
        saving_study: SavingStudy,
    ) -> None:
        margin.rate_id = electricity_rate.id
        margin.min_margin = 1

        default_margin = SuggestedRatesGenerator(
            db_session=db_session, saving_study=saving_study
        ).get_default_margin_rate(electricity_rate)

        assert default_margin.min_margin == 1

    def test_get_default_margin_rate_not_annual_consumption(
        self,
        db_session: Session,
        electricity_rate: Rate,
        margin: Margin,
        margin_consume_range: Margin,
        saving_study: SavingStudy,
    ) -> None:
        margin.id = 1234
        margin.rate_id = electricity_rate.id
        margin.min_margin = 1
        margin.min_consumption = 1
        margin_consume_range.id = 1235
        margin_consume_range.rate_id = electricity_rate.id
        margin_consume_range.min_margin = 2
        margin_consume_range.min_consumption = 0

        default_margin = SuggestedRatesGenerator(
            db_session=db_session, saving_study=saving_study
        ).get_default_margin_rate(electricity_rate)

        assert default_margin.id == 1234

    def test_get_default_margin_rate_margin_empty(
        self,
        db_session: Session,
        electricity_rate: Rate,
        saving_study: SavingStudy,
    ) -> None:
        saving_study.annual_consumption = 0
        default_margin = SuggestedRatesGenerator(
            db_session=db_session, saving_study=saving_study
        ).get_default_margin_rate(electricity_rate)

        assert default_margin is None

    def test_get_default_margin_rate_unique_margin_rate(
        self,
        db_session: Session,
        electricity_rate: Rate,
        margin: Margin,
        saving_study: SavingStudy,
    ) -> None:
        margin.rate_id = electricity_rate.id
        margin.type = MarginType.rate_type
        margin.min_margin = 2
        db_session.add(margin)
        db_session.commit()

        default_margin = SuggestedRatesGenerator(
            db_session=db_session, saving_study=saving_study
        ).get_default_margin_rate(electricity_rate)

        assert default_margin.min_margin == 2

    def test_get_default_margin_rate_no_margin(
        self, db_session: Session, electricity_rate: Rate, saving_study: SavingStudy
    ) -> None:
        default_margin = SuggestedRatesGenerator(
            db_session=db_session, saving_study=saving_study
        ).get_default_margin_rate(electricity_rate)

        assert default_margin is None

    @pytest.mark.parametrize(
        "annual_consumption",
        [
            Decimal("0.1"),
            Decimal("5000.0"),
        ],
    )
    def test_get_default_margin_rate_annual_consumption_out_of_the_range(
        self,
        db_session: Session,
        electricity_rate: Rate,
        margin_consume_range: Margin,
        saving_study: SavingStudy,
        annual_consumption: Decimal,
    ) -> None:
        margin_consume_range.rate_id = electricity_rate.id
        saving_study.annual_consumption = annual_consumption
        db_session.add(margin_consume_range)
        db_session.add(saving_study)
        db_session.commit()

        default_margin = SuggestedRatesGenerator(
            db_session=db_session, saving_study=saving_study
        ).get_default_margin_rate(electricity_rate)

        assert default_margin is None

    def test_get_default_margin_rate_annual_consumption_in_the_range(
        self,
        db_session: Session,
        electricity_rate: Rate,
        margin_consume_range: Margin,
        margin: Margin,
        saving_study: SavingStudy,
    ) -> None:
        margin_consume_range.rate_id = electricity_rate.id
        margin_consume_range.min_consumption = 16.0
        margin_consume_range.max_consumption = 22.39
        margin.rate_id = electricity_rate.id
        margin.min_consumption = 12.5
        margin.max_consumption = 15.99
        saving_study.annual_consumption = 20.0
        db_session.add(margin_consume_range)
        db_session.add(margin)
        db_session.add(saving_study)
        db_session.commit()

        default_margin = SuggestedRatesGenerator(
            db_session=db_session, saving_study=saving_study
        ).get_default_margin_rate(electricity_rate)

        # Get margin_consume_range because the annual_consumption is in the range
        assert default_margin.id == margin_consume_range.id

    def test_generate_suggested_rates_electricity(
        self,
        db_session: Session,
        electricity_rate: Rate,
        margin: Margin,
        saving_study: SavingStudy,
    ) -> None:
        # power
        saving_study.power_1 = Decimal("9")
        saving_study.power_2 = Decimal("15.01")
        saving_study.power_3 = Decimal("15.01")
        saving_study.power_4 = Decimal("15.01")
        saving_study.power_5 = Decimal("15.01")
        saving_study.power_6 = Decimal("15.01")
        saving_study.power_price_1 = Decimal("0.0409")
        saving_study.power_price_2 = Decimal("0.0348")
        saving_study.power_price_3 = Decimal("0.0117")
        saving_study.power_price_4 = Decimal("0.0107")
        saving_study.power_price_5 = Decimal("0.008")
        saving_study.power_price_6 = Decimal("0.0059")
        saving_study.is_compare_conditions = True

        # energy
        saving_study.energy_price_1 = Decimal("0.30221")
        saving_study.energy_price_2 = Decimal("0.29087")
        saving_study.energy_price_3 = Decimal("0.26969")
        saving_study.energy_price_4 = Decimal("0.26218")
        saving_study.energy_price_5 = Decimal("0.25491")
        saving_study.energy_price_6 = Decimal("0.25391")
        saving_study.consumption_p1 = Decimal("2124")
        saving_study.consumption_p2 = Decimal("2682")
        saving_study.consumption_p3 = Decimal("1807")
        saving_study.consumption_p4 = Decimal("2016")
        saving_study.consumption_p5 = Decimal("810")
        saving_study.consumption_p6 = Decimal("5452")
        saving_study.annual_consumption = Decimal("14891")

        # electricity rate
        electricity_rate.min_power = Decimal("9")
        electricity_rate.max_power = Decimal("15.001")
        electricity_rate.min_consumption = Decimal("810")
        electricity_rate.max_consumption = Decimal("2124")
        electricity_rate.power_price_1 = Decimal("0.054315")
        electricity_rate.power_price_2 = Decimal("0.032600")
        electricity_rate.power_price_3 = Decimal("0.010964")
        electricity_rate.power_price_4 = Decimal("0.010010")
        electricity_rate.power_price_5 = Decimal("0.007486")
        electricity_rate.power_price_6 = Decimal("0.005482")
        electricity_rate.energy_price_1 = Decimal("0.229884")
        electricity_rate.energy_price_2 = Decimal("0.220654")
        electricity_rate.energy_price_3 = Decimal("0.203385")
        electricity_rate.energy_price_4 = Decimal("0.20507")
        electricity_rate.energy_price_5 = Decimal("0.189022")
        electricity_rate.energy_price_6 = Decimal("0.181553")

        margin.rate_id = electricity_rate.id
        margin.min_margin = 7
        margin.max_margin = 7
        margin.type = MarginType.consume_range
        margin.min_consumption = Decimal("500")
        margin.max_consumption = Decimal("30000")

        suggested_rates = SuggestedRatesGenerator(
            db_session=db_session, saving_study=saving_study
        ).generate_suggested_rates(
            [
                electricity_rate,
            ]
        )

        assert len(suggested_rates) == 1
        assert suggested_rates[0].saving_study_id == 1
        assert suggested_rates[0].marketer_name == "Marketer"
        assert suggested_rates[0].has_contractual_commitment is True
        assert suggested_rates[0].duration == 12
        assert suggested_rates[0].rate_name == "Electricity rate"
        assert suggested_rates[0].is_full_renewable is True
        assert suggested_rates[0].has_net_metering is True
        assert suggested_rates[0].net_metering_value == Decimal("28.32")
        assert suggested_rates[0].max_profit_margin == Decimal("7")
        assert suggested_rates[0].min_profit_margin == Decimal("7")
        assert suggested_rates[0].applied_profit_margin == Decimal("7")

        assert suggested_rates[0].power_price_1 == Decimal("0.054315")
        assert suggested_rates[0].power_price_2 == Decimal("0.032600")
        assert suggested_rates[0].power_price_3 == Decimal("0.010964")
        assert suggested_rates[0].power_price_4 == Decimal("0.010010")
        assert suggested_rates[0].power_price_5 == Decimal("0.007486")
        assert suggested_rates[0].power_price_6 == Decimal("0.005482")
        assert suggested_rates[0].energy_price_1 == Decimal("0.229884")
        assert suggested_rates[0].energy_price_2 == Decimal("0.220654")
        assert suggested_rates[0].energy_price_3 == Decimal("0.203385")
        assert suggested_rates[0].energy_price_4 == Decimal("0.20507")
        assert suggested_rates[0].energy_price_5 == Decimal("0.189022")
        assert suggested_rates[0].energy_price_6 == Decimal("0.181553")

        assert suggested_rates[0].total_commission == Decimal("0")
        assert suggested_rates[0].theoretical_commission == Decimal("0")
        assert suggested_rates[0].other_costs_commission == Decimal("0")

        assert suggested_rates[0].fixed_term_price is None
        assert suggested_rates[0].price_type == PriceType.fixed_fixed

        # TODO: check this value
        assert suggested_rates[0].final_cost == Decimal("3546.92533830")
        assert suggested_rates[0].power_cost == Decimal("542.98510330")
        assert suggested_rates[0].ie_cost == Decimal("0")
        assert suggested_rates[0].iva_cost == Decimal("0")
        assert suggested_rates[0].other_costs == Decimal("0")
        assert suggested_rates[0].ih_cost is None
        assert suggested_rates[0].fixed_cost is None
        assert suggested_rates[0].saving_absolute == Decimal("1005.64968670")
        assert suggested_rates[0].saving_relative == Decimal(
            "22.08968948732481349936676771"
        )

    def test_generate_suggested_rates_gas(
        self,
        db_session: Session,
        gas_rate: Rate,
        margin: Margin,
        saving_study: SavingStudy,
    ) -> None:
        # energy
        saving_study.consumption_p1 = Decimal("2124")
        saving_study.consumption_p2 = Decimal("2682")
        saving_study.consumption_p3 = Decimal("1807")
        saving_study.consumption_p4 = Decimal("2016")
        saving_study.consumption_p5 = Decimal("810")
        saving_study.consumption_p6 = Decimal("5452")
        saving_study.annual_consumption = Decimal("14891")
        saving_study.is_compare_conditions = True

        # electricity rate
        gas_rate.min_power = Decimal("9")
        gas_rate.max_power = Decimal("15.001")
        gas_rate.min_consumption = Decimal("810")
        gas_rate.max_consumption = Decimal("2124")
        gas_rate.power_price_1 = Decimal("0.054315")
        gas_rate.energy_price_1 = Decimal("0.229884")

        # fixed term
        gas_rate.fixed_term_price = Decimal("0.23")

        # margin
        margin.rate_id = gas_rate.id
        margin.min_margin = 7
        margin.max_margin = 7
        margin.type = MarginType.consume_range
        margin.min_consumption = Decimal("500")
        margin.max_consumption = Decimal("30000")

        suggested_rates = SuggestedRatesGenerator(
            db_session=db_session, saving_study=saving_study
        ).generate_suggested_rates(
            [
                gas_rate,
            ]
        )

        assert len(suggested_rates) == 1
        assert suggested_rates[0].saving_study_id == 1
        assert suggested_rates[0].marketer_name == "Marketer"
        assert suggested_rates[0].has_contractual_commitment is False
        assert suggested_rates[0].duration == 24
        assert suggested_rates[0].rate_name == "Gas rate name"
        assert suggested_rates[0].is_full_renewable is False
        assert suggested_rates[0].has_net_metering is False
        assert suggested_rates[0].net_metering_value == Decimal("0")
        assert suggested_rates[0].max_profit_margin == Decimal("7")
        assert suggested_rates[0].min_profit_margin == Decimal("7")
        assert suggested_rates[0].applied_profit_margin == Decimal("7")

        assert suggested_rates[0].power_price_1 == Decimal("0.054315")
        assert suggested_rates[0].power_price_2 is None
        assert suggested_rates[0].power_price_3 is None
        assert suggested_rates[0].power_price_4 is None
        assert suggested_rates[0].power_price_5 is None
        assert suggested_rates[0].power_price_6 is None
        assert suggested_rates[0].energy_price_1 == Decimal("0.229884")
        assert suggested_rates[0].energy_price_2 is None
        assert suggested_rates[0].energy_price_3 is None
        assert suggested_rates[0].energy_price_4 is None
        assert suggested_rates[0].energy_price_5 is None
        assert suggested_rates[0].energy_price_6 is None

        assert suggested_rates[0].fixed_term_price == Decimal("0.23")
        assert suggested_rates[0].price_type == PriceType.fixed_base

        assert suggested_rates[0].total_commission == Decimal("0")
        assert suggested_rates[0].theoretical_commission == Decimal("0")
        assert suggested_rates[0].other_costs_commission == Decimal("0")

        # TODO: check this value
        assert suggested_rates[0].final_cost == Decimal("15440.223616")
        assert suggested_rates[0].saving_absolute == Decimal("42544.976384")
        assert suggested_rates[0].saving_relative == Decimal(
            "73.37213010216400046908521485"
        )

    @patch("src.services.studies.CostCalculatorElectricity.compute_total_cost")
    def test_compute_current_cost_ok(
        self,
        mock_costs,
        db_session: Session,
        saving_study: SavingStudy,
    ) -> None:
        rate_generator = SuggestedRatesGenerator(
            db_session=db_session, saving_study=saving_study
        )
        mock_costs.return_value = mock_costs.return_value = SuggestedRateCosts(
            total_cost=Decimal("100"),
        )

        assert rate_generator.compute_current_cost() == Decimal("100")
        assert mock_costs.call_count == 1

    @patch("src.services.studies.CostCalculatorElectricity.compute_total_cost")
    @patch("src.services.studies.ComissionCalculatorFixedFixed.compute_comission")
    def test_compute_final_cost_and_commission_electricity(
        self,
        mock_comission,
        mock_costs,
        db_session: Session,
        saving_study: SavingStudy,
        electricity_rate: Rate,
    ) -> None:
        rate_generator = SuggestedRatesGenerator(
            db_session=db_session, saving_study=saving_study
        )
        mock_costs.return_value = SuggestedRateCosts(
            total_cost=Decimal("100"),
        )
        mock_comission.return_value = Decimal("0.015")

        (
            costs,
            theoretical_commission,
        ) = rate_generator.compute_final_cost_and_commission(
            electricity_rate, Decimal("0.1")
        )

        assert costs.final_cost == Decimal("100.015")
        assert mock_costs.call_count == 1
        assert mock_comission.call_count == 1

    @patch("src.services.studies.CostCalculatorGas.compute_total_cost")
    @patch("src.services.studies.ComissionCalculatorFixedBase.compute_comission")
    def test_compute_final_cost_and_commission_gas(
        self,
        mock_comission,
        mock_costs,
        db_session: Session,
        saving_study: SavingStudy,
        gas_rate: Rate,
    ) -> None:
        rate_generator = SuggestedRatesGenerator(
            db_session=db_session, saving_study=saving_study
        )
        mock_costs.return_value = SuggestedRateCosts(
            total_cost=Decimal("100"),
        )
        mock_comission.return_value = Decimal("0.18408")
        (
            costs,
            theoretical_commission,
        ) = rate_generator.compute_final_cost_and_commission(gas_rate, Decimal("0.1"))

        assert costs.final_cost == Decimal("100.18408")
        assert mock_costs.call_count == 1
        assert mock_comission.call_count == 1

    @patch("src.services.studies.CostCalculatorElectricity.get_current_other_costs")
    @patch("src.services.studies.CostCalculatorElectricity.get_energy_cost")
    @patch("src.services.studies.CostCalculatorElectricity.get_power_cost")
    @patch("src.services.studies.CostCalculatorElectricity.get_others_costs")
    @patch("src.services.studies.CostCalculatorElectricity.get_ie")
    @patch("src.services.studies.CostCalculatorElectricity.get_iva")
    def test_compute_final_cost_electricity(
        self,
        iva_mock,
        ie_mock,
        other_costs_mock,
        power_cost_mock,
        energy_mock,
        current_other_costs_mock,
        db_session: Session,
        saving_study: SavingStudy,
        electricity_rate: Rate,
    ) -> None:
        suggested_generator = SuggestedRatesGenerator(
            db_session=db_session, saving_study=saving_study
        )
        energy_mock.return_value = Decimal("100")
        power_cost_mock.return_value = Decimal("100")
        other_costs_mock.return_value = Decimal("100")
        current_other_costs_mock.return_value = Decimal("100")
        ie_mock.return_value = Decimal("100")
        iva_mock.return_value = Decimal("1")

        (
            costs,
            theoretical_commission,
        ) = suggested_generator.compute_final_cost_and_commission(
            electricity_rate, Decimal("0.1")
        )
        assert costs.final_cost == Decimal("60600")
        assert costs.energy_cost == Decimal("100")
        assert costs.power_cost == Decimal("100")
        assert costs.other_costs == Decimal("100")
        assert costs.ie_cost == Decimal("30000")
        assert costs.iva_cost == Decimal("30300")
        assert theoretical_commission == Decimal("0")
        assert energy_mock.call_count == 1
        assert power_cost_mock.call_count == 1
        assert other_costs_mock.call_count == 1
        assert ie_mock.call_count == 1
        assert iva_mock.call_count == 1

    @patch("src.services.studies.CostCalculatorElectricity.get_current_other_costs")
    @patch("src.services.studies.CostCalculatorGas.get_energy_cost")
    @patch("src.services.studies.CostCalculatorGas.get_fixed_cost")
    @patch("src.services.studies.CostCalculatorGas.get_others_costs")
    @patch("src.services.studies.CostCalculatorGas.get_ih")
    @patch("src.services.studies.CostCalculatorGas.get_iva")
    def test_compute_final_cost_gas(
        self,
        iva_mock,
        ih_mock,
        other_costs_mock,
        fixed_costs_mock,
        energy_mock,
        current_other_costs_mock,
        db_session: Session,
        saving_study: SavingStudy,
        gas_rate: Rate,
    ) -> None:
        suggested_generator = SuggestedRatesGenerator(
            db_session=db_session, saving_study=saving_study
        )
        energy_mock.return_value = Decimal("100")
        other_costs_mock.return_value = Decimal("100")
        current_other_costs_mock.return_value = Decimal("100")
        fixed_costs_mock.return_value = Decimal("100")
        ih_mock.return_value = Decimal("0.00234")
        iva_mock.return_value = Decimal("100")

        saving_study.consumption_p1 = Decimal("100")
        (
            costs,
            theoretical_commission,
        ) = suggested_generator.compute_final_cost_and_commission(
            gas_rate, Decimal("0.1")
        )
        assert costs.final_cost == Decimal("30323.63400")
        assert costs.fixed_cost == Decimal("100")
        assert costs.energy_cost == Decimal("100")
        assert costs.other_costs == Decimal("100")
        assert costs.ih_cost == Decimal("0.234")
        assert costs.iva_cost == Decimal("30023.40000")
        assert theoretical_commission == Decimal("0")
        assert energy_mock.call_count == 1
        assert fixed_costs_mock.call_count == 1
        assert other_costs_mock.call_count == 1
        assert ih_mock.call_count == 1
        assert iva_mock.call_count == 1

    def test_compute_other_costs_commission_no_costs_related_with_rate(
        self, db_session: Session, saving_study: SavingStudy, electricity_rate: Rate
    ):
        suggested_generator = SuggestedRatesGenerator(
            db_session=db_session, saving_study=saving_study
        )
        assert suggested_generator.compute_other_costs_commission(
            electricity_rate
        ) == Decimal("0")

    def test_compute_other_costs_commission(
        self,
        db_session: Session,
        saving_study: SavingStudy,
        electricity_rate: Rate,
        other_cost: OtherCost,
    ):
        other_cost.rates.append(electricity_rate)
        db_session.add(other_cost)
        db_session.add(electricity_rate)
        db_session.commit()

        suggested_generator = SuggestedRatesGenerator(
            db_session=db_session, saving_study=saving_study
        )
        assert suggested_generator.compute_other_costs_commission(
            electricity_rate
        ) == Decimal("17.10")


class TestComissionCalculator:
    def test_compute_theoretical_commission_fixed_base_ok(
        self,
        db_session: Session,
        saving_study: SavingStudy,
        gas_rate: Rate,
        commission_fixed_base: Commission,
    ) -> None:
        assert ComissionCalculatorFixedBase(saving_study).compute_comission(
            gas_rate, Decimal("0.1")
        ) == Decimal("0.18408")

    def test_compute_theoretical_commission_fixed_base_no_percentage_ok(
        self,
        db_session: Session,
        saving_study: SavingStudy,
        gas_rate: Rate,
        commission_fixed_base: Commission,
    ) -> None:
        commission_fixed_base.percentage_Test_commission = None

        assert ComissionCalculatorFixedBase(saving_study).compute_comission(
            gas_rate, Decimal("0.1")
        ) == Decimal("0")

    def test_compute_theoretical_commission_fixed_fixed_ok(
        self,
        db_session: Session,
        saving_study: SavingStudy,
        electricity_rate: Rate,
        commission: Commission,
    ):
        saving_study.annual_consumption = Decimal("5.3")

        assert ComissionCalculatorFixedFixed(saving_study).compute_comission(
            electricity_rate
        ) == Decimal("12")

    def test_compute_theoretical_commission_fixed_fixed_consumption_out_of_range_ok(
        self,
        db_session: Session,
        saving_study: SavingStudy,
        electricity_rate: Rate,
        commission: Commission,
    ):
        assert ComissionCalculatorFixedFixed(saving_study).compute_comission(
            electricity_rate
        ) == Decimal("0")

    def test_compute_theoretical_commission_fixed_fixed_no_commission_ok(
        self,
        db_session: Session,
        saving_study: SavingStudy,
        electricity_rate: Rate,
    ):
        assert ComissionCalculatorFixedFixed(saving_study).compute_comission(
            electricity_rate
        ) == Decimal("0")

    def test_compute_theoretical_commission_fixed_fixed_power_ok(
        self,
        db_session: Session,
        saving_study: SavingStudy,
        electricity_rate: Rate,
        commission_power: Commission,
    ):
        assert ComissionCalculatorFixedFixed(saving_study).compute_comission(
            electricity_rate
        ) == Decimal("16")


class TestCostCalculator:
    @pytest.mark.parametrize(
        "consumptions, prices, expected_cost",
        [
            (
                [0, 0, 0, 0, 0, 0],
                ["0.0", "0.0", "0.0", "0.0", "0.0", "0.0"],
                Decimal("0"),
            ),
            (
                [1, 0, 0, 0, 0, 0],
                ["1.0", "0.0", "0.0", "0.0", "0.0", "0.0"],
                Decimal("1"),
            ),
            (
                [1, 1, 0, 0, 0, 0],
                ["1.0", "1.0", "0.0", "0.0", "0.0", "0.0"],
                Decimal("2"),
            ),
            (
                [1, 1, None, 0, 0, 0],
                ["1.0", "1.0", None, "0.0", "0.0", "0.0"],
                Decimal("2.0"),
            ),
            (
                [1, 1, None, 1, 1, 1],
                ["1.0", "1.0", None, "1.0", "1.0", "1.0"],
                Decimal("2.0"),
            ),
            (
                [1, 1, 1, 1, 1, 1],
                ["1.0", "1.0", "1.0", "1.0", "1.0", "1.0"],
                Decimal("6.0"),
            ),
        ],
    )
    def test_get_energy_cost_fixed_fixed(
        self,
        db_session: Session,
        saving_study: SavingStudy,
        electricity_rate: Rate,
        consumptions: List[int],
        prices: List[Decimal],
        expected_cost: Decimal,
    ) -> None:
        for i, price in enumerate(prices):
            price = Decimal(price) if price is not None else None
            setattr(electricity_rate, f"energy_price_{i+1}", price)
        for i, consumption in enumerate(consumptions):
            consumption = consumption if consumption is not None else None
            setattr(saving_study, f"consumption_p{i+1}", consumption)
        cost_calculator_info = CostCalculatorInfo.from_orm(electricity_rate)

        electricity_cost = CostCalculatorElectricity(
            db_session, saving_study
        ).get_energy_cost(cost_calculator_info, Decimal("0.1"))

        assert electricity_cost == expected_cost

    @pytest.mark.parametrize(
        "consumptions, prices, applied_margin, expected_cost",
        [
            (
                [0, 0, 0, 0, 0, 0],
                ["0.0", "0.0", "0.0", "0.0", "0.0", "0.0"],
                Decimal("0"),
                Decimal("0"),
            ),
            (
                [1, 0, 0, 0, 0, 0],
                ["1.0", "0.0", "0.0", "0.0", "0.0", "0.0"],
                Decimal("6"),
                Decimal("7"),  # (1 + 6) * 1
            ),
            (
                [1, 1, 0, 0, 0, 0],
                ["1.0", "1.0", "0.0", "0.0", "0.0", "0.0"],
                Decimal("5"),
                Decimal("12"),  # (1 + 5) * 2
            ),
            (
                [1, 1, None, 0, 0, 0],
                ["1.0", "1.0", None, "0.0", "0.0", "0.0"],
                Decimal("1"),
                Decimal("4"),  # (1 + 1) * 2
            ),
            (
                [1, 1, None, 1, 1, 1],
                ["1.0", "1.0", None, "1.0", "1.0", "1.0"],
                Decimal("1"),
                Decimal("4"),  # (1 + 1) * 2
            ),
            (
                [1, 1, 1, 1, 1, 1],
                ["1.0", "1.0", "1.0", "1.0", "1.0", "1.0"],
                Decimal("5"),
                Decimal("36"),  # (1 + 5) * 6
            ),
            (
                [1, 1, 1, 1, 1, 1],
                ["1.0", None, "1.0", "1.0", "1.0", "1.0"],
                Decimal("5"),
                Decimal("6"),  # (1 + 5) * 1
            ),
            (
                [3, 1, 1, 1, 1, 1],
                ["2.444444", None, "1.0", "1.0", "1.0", "1.0"],
                Decimal("5.111111"),
                Decimal("22.666665"),  # (2.444444 + 5.111111) * 3
            ),
        ],
    )
    def test_get_energy_cost_fixed_base(
        self,
        db_session: Session,
        saving_study: SavingStudy,
        electricity_rate: Rate,
        consumptions: List[int],
        prices: List[Decimal],
        applied_margin: Decimal,
        expected_cost: Decimal,
    ) -> None:
        electricity_rate.price_type = PriceType.fixed_base
        for i, price in enumerate(prices):
            price = Decimal(price) if price is not None else None
            setattr(electricity_rate, f"energy_price_{i+1}", price)
        for i, consumption in enumerate(consumptions):
            consumption = consumption if consumption is not None else None
            setattr(saving_study, f"consumption_p{i+1}", consumption)
        cost_calculator_info = CostCalculatorInfo.from_orm(electricity_rate)

        electricity_cost = CostCalculatorElectricity(
            db_session, saving_study
        ).get_energy_cost(cost_calculator_info, applied_margin)

        assert electricity_cost == expected_cost

    @pytest.mark.parametrize(
        "powers, prices, expected_cost",
        [
            (
                ["0.0", "0.0", "0.0", "0.0", "0.0", "0.0"],
                ["0.0", "0.0", "0.0", "0.0", "0.0", "0.0"],
                Decimal("0"),
            ),
            (
                ["1.0", "0.0", "0.0", "0.0", "0.0", "0.0"],
                ["1.0", "0.0", "0.0", "0.0", "0.0", "0.0"],
                Decimal("365"),  # 1 * 1 * 365
            ),
            (
                ["1.0", None, "1.0", "0.0", "0.0", "0.0"],
                ["5.0", "255.1", "1.0", "0.0", "0.0", "0.0"],
                Decimal("1825"),  # 1 * 5 * 365
            ),
            (
                ["1.0", "1.0", "1.0", "1.0", "1.0", "1.0"],
                ["1.0", "2.0", "3.0", "4.0", "5.0", "6.0"],
                Decimal(
                    "7665"
                ),  # (1 * 1 + 1 * 2 + 1 * 3 + 1 * 4 + 1 * 5 + 1 * 6) * 365
            ),
        ],
    )
    def test_get_power_cost(
        self,
        db_session: Session,
        saving_study: SavingStudy,
        electricity_rate: Rate,
        powers: List[Decimal],
        prices: List[Decimal],
        expected_cost: Decimal,
    ):
        for i, price in enumerate(prices):
            price = Decimal(price) if price is not None else None
            setattr(electricity_rate, f"power_price_{i+1}", price)
        for i, power in enumerate(powers):
            power = power if power is not None else None
            setattr(saving_study, f"power_{i+1}", power)
        db_session.add(electricity_rate)
        db_session.add(saving_study)
        db_session.commit()
        cost_calculator_info = CostCalculatorInfo.from_orm(electricity_rate)

        electricity_cost = CostCalculatorElectricity(
            db_session, saving_study
        ).get_power_cost(cost_calculator_info)

        assert electricity_cost == expected_cost

    def test_get_ie_ok(
        self,
        db_session: Session,
        saving_study: SavingStudy,
        energy_cost_electric_tax: EnergyCost,
    ):
        ie = CostCalculatorElectricity(
            db_session=db_session, saving_study=saving_study
        ).get_ie()
        assert ie == Decimal("0.05117")

    def test_get_ie_no_cost_ok(self, db_session: Session, saving_study: SavingStudy):
        ie = CostCalculatorElectricity(
            db_session=db_session, saving_study=saving_study
        ).get_ie()
        assert ie == Decimal("0")

    @pytest.mark.parametrize(
        "cost_type, quantity, power_cost, energy_cost, expected_cost",
        [
            (
                OtherCostType.eur_month,
                Decimal("0"),
                Decimal("0"),
                Decimal("0"),
                Decimal("0"),
            ),
            (
                OtherCostType.eur_month,
                Decimal("13"),
                Decimal("0"),
                Decimal("0"),
                Decimal("155.9998290412832424293233652"),
            ),  # 30.4166667 * 13
            (
                OtherCostType.percentage,
                Decimal("0"),
                Decimal("0"),
                Decimal("0"),
                Decimal("0"),
            ),
            (
                OtherCostType.percentage,
                Decimal("0.12"),
                Decimal("245.34"),
                Decimal("34.2223"),
                Decimal("33.547476"),
            ),  # (245.34 + 34.2223) * 0.12
            (
                OtherCostType.eur_kwh,
                Decimal("0"),
                Decimal("0"),
                Decimal("0"),
                Decimal("0"),
            ),
            (
                OtherCostType.eur_kwh,
                Decimal("1.22"),
                None,
                None,
                Decimal("0.0"),
            ),  # total_consumption * 1.22
        ],
    )
    def test_compute_other_cost_ok(
        self,
        db_session: Session,
        saving_study: SavingStudy,
        cost_type: OtherCostType,
        quantity: Decimal,
        power_cost: Decimal,
        energy_cost: Decimal,
        expected_cost: Decimal,
    ):
        other_costs = CostCalculatorElectricity(
            db_session, saving_study
        ).compute_other_cost(cost_type, quantity, power_cost, energy_cost)

        assert other_costs == expected_cost  # (365 / 12) * 32

    def test_get_others_costs_ok(
        self,
        db_session: Session,
        saving_study: SavingStudy,
        electricity_rate: Rate,
        other_cost: OtherCost,
    ):
        other_cost.quantity = Decimal("13")
        other_cost.type = OtherCostType.eur_month
        cost_calculator_info = CostCalculatorInfo.from_orm(electricity_rate)

        other_costs = CostCalculatorElectricity(
            db_session, saving_study
        ).get_others_costs(cost_calculator_info, Decimal("0"), Decimal("0"))

        assert other_costs == Decimal("155.9998290412832424293233652")

    def test_get_others_costs_3_costs(
        self,
        db_session: Session,
        saving_study: SavingStudy,
        electricity_rate: Rate,
        other_costs: List[OtherCost],
    ):
        cost_calculator_info = CostCalculatorInfo.from_orm(electricity_rate)

        other_costs = CostCalculatorElectricity(
            db_session, saving_study
        ).get_others_costs(cost_calculator_info, 10.12, 33.33)

        # Sum of costs
        # (365 / 12) * 13 = 395,416666667
        # 10.12 + 33.33 * 0.12 = 5.214
        # 15.34 * 1.22 = 18.7148
        # 395,416666667 + 5.214 + 18.7148 = 419.345466666667
        assert other_costs == Decimal("161.2138290412832419493233652")

    def test_get_current_other_costs_ok(
        self, db_session: Session, saving_study: SavingStudy, electricity_rate: Rate
    ):
        saving_study.other_cost_eur_month = Decimal("14.13")
        saving_study.other_cost_kwh = Decimal("13.14")
        saving_study.other_cost_percentage = Decimal("3.4")

        current_costs = CostCalculatorElectricity(
            db_session, saving_study
        ).get_current_other_costs(10, 33)

        # TODO: check this value
        assert current_costs == Decimal("303.8798272001893696554853091")

    def test_get_iva_ok(
        self,
        db_session: Session,
        saving_study: SavingStudy,
        energy_cost_protected: EnergyCost,
    ):
        iva = CostCalculatorElectricity(
            db_session=db_session, saving_study=saving_study
        ).get_iva()

        assert iva == Decimal("0.21")

    def test_get_iva_gas_ok(
        self,
        db_session: Session,
        saving_study: SavingStudy,
        energy_cost_protected: EnergyCost,
    ):
        iva = CostCalculatorGas(
            db_session=db_session, saving_study=saving_study
        ).get_iva()

        assert iva == Decimal("0.21")

    def test_get_iva_no_cost_ok(self, db_session: Session, saving_study: SavingStudy):
        iva = CostCalculatorElectricity(
            db_session=db_session, saving_study=saving_study
        ).get_iva()

        assert iva == Decimal("0")

    @pytest.mark.parametrize(
        "price_type, energy_price, consumption, applied_margin, expected_cost",
        [
            (
                PriceType.fixed_fixed,
                Decimal("0.0"),
                100,
                Decimal("0.0"),
                Decimal("0.0"),
            ),
            (
                PriceType.fixed_fixed,
                Decimal("0.1"),
                100,
                Decimal("0.1"),
                Decimal("10.0"),
            ),
            (
                PriceType.fixed_base,
                Decimal("0.1"),
                100,
                Decimal("0.2"),
                Decimal("30.0"),
            ),
        ],
    )
    def test_get_energy_cost_gas(
        self,
        db_session: Session,
        saving_study: SavingStudy,
        gas_rate: Rate,
        price_type: PriceType,
        energy_price: Decimal,
        consumption: Decimal,
        applied_margin: Decimal,
        expected_cost: Decimal,
    ):
        saving_study.consumption_p1 = consumption
        gas_rate.price_type = price_type
        gas_rate.energy_price_1 = energy_price
        db_session.add_all([saving_study, gas_rate])
        db_session.commit()
        cost_calculator_info = CostCalculatorInfo.from_orm(gas_rate)

        energy_cost = CostCalculatorGas(db_session, saving_study).get_energy_cost(
            cost_calculator_info, applied_margin
        )

        assert energy_cost == expected_cost

    @pytest.mark.parametrize(
        "fixed_term_price, days, expected_cost",
        [
            (Decimal("0.0"), 0, Decimal("0.0")),
            (Decimal("0.1"), 30, Decimal("3.0")),
            (Decimal("12.1"), 365, Decimal("4416.5")),
        ],
    )
    def test_get_fixed_cost_gas(
        self,
        db_session: Session,
        saving_study: SavingStudy,
        gas_rate: Rate,
        fixed_term_price: Decimal,
        days: int,
        expected_cost: Decimal,
    ):
        saving_study.analyzed_days = days
        gas_rate.fixed_term_price = fixed_term_price
        db_session.add_all([saving_study, gas_rate])
        db_session.commit()

        power_cost = CostCalculatorGas(db_session, saving_study).get_fixed_cost(
            gas_rate.fixed_term_price
        )

        assert power_cost == expected_cost

    def test_get_ih_ok(
        self,
        db_session: Session,
        saving_study: SavingStudy,
        energy_cost_hydrocarbons_tax: EnergyCost,
    ):
        saving_study.consumption_p1 = Decimal("100")
        ih = CostCalculatorGas(
            db_session=db_session, saving_study=saving_study
        ).get_ih()
        assert ih == Decimal("0.234")

    def test_get_ih_no_cost_ok(self, db_session: Session, saving_study: SavingStudy):
        ih = CostCalculatorGas(
            db_session=db_session, saving_study=saving_study
        ).get_ih()

        assert ih == Decimal("0")


class TestCalculatorFactory:
    def test_init_cost_calculator_electricity(
        self, db_session: Session, saving_study: SavingStudy
    ):
        cost_calculator = CalculatorsFactory.init_cost_calculator(
            EnergyType.electricity, db_session, saving_study
        )

        assert type(cost_calculator) == CostCalculatorElectricity

    def test_init_cost_calculator_gas(
        self, db_session: Session, saving_study: SavingStudy
    ):
        cost_calculator = CalculatorsFactory.init_cost_calculator(
            EnergyType.gas, db_session, saving_study
        )

        assert type(cost_calculator) == CostCalculatorGas

    def test_init_comission_calculator_fixed_base(
        self, db_session: Session, saving_study: SavingStudy
    ):
        comission_calculator = CalculatorsFactory.init_comission_calculator(
            PriceType.fixed_base, saving_study
        )

        assert type(comission_calculator) == ComissionCalculatorFixedBase

    def test_init_comission_calculator_fixed_fixed(
        self, db_session: Session, saving_study: SavingStudy
    ):
        comission_calculator = CalculatorsFactory.init_comission_calculator(
            PriceType.fixed_fixed, saving_study
        )

        assert type(comission_calculator) == ComissionCalculatorFixedFixed


def test_saving_study_create_ok(
    db_session: Session, user_create: User, electricity_rate_type: RateType
):
    saving_study_create(
        db_session,
        SavingStudyRequest(
            cups="testtesttesttesttest",
            current_rate_type_id=electricity_rate_type.id,
            energy_type=EnergyType.electricity,
            is_existing_client=False,
            is_from_sips=False,
            is_compare_conditions=False,
            analyzed_days=100,
            energy_price_1=100,
            client_type="particular",
        ),
        user_create,
    )
    assert db_session.query(SavingStudy).count() == 1


def test_saving_study_create_ok_rate_type_id_null(
    db_session: Session, user_create: User, electricity_rate_type: RateType
):
    saving_study_create(
        db_session,
        SavingStudyRequest(
            cups="testtesttesttesttest",
            energy_type=EnergyType.electricity,
            is_existing_client=False,
            is_from_sips=False,
            is_compare_conditions=False,
            analyzed_days=100,
            energy_price_1=100,
            client_type="particular",
        ),
        user_create,
    )
    assert db_session.query(SavingStudy).count() == 1


@patch("src.services.studies.create_saving_study_db")
def test_saving_study_create_duplicate_id(
    mock_save,
    db_session: Session,
    user_create: User,
    electricity_rate_type: RateType,
    saving_study: SavingStudy,
):
    mock_save.side_effect = IntegrityError(params=None, orig=None, statement=None)

    with pytest.raises(HTTPException) as exc:
        saving_study_create(
            db_session,
            SavingStudyRequest(
                cups="testtesttesttesttest",
                current_rate_type_id=electricity_rate_type.id,
                energy_type=EnergyType.electricity,
                is_existing_client=False,
                is_from_sips=False,
                is_compare_conditions=False,
                analyzed_days=100,
                energy_price_1=100,
                client_type="particular",
            ),
            user_create,
        )

    assert exc.value.status_code == 409
    assert exc.value.detail == "value_error.already_exists"


def test_saving_study_create_rate_type_not_found(
    db_session: Session,
    user_create: User,
    electricity_rate_type: RateType,
    saving_study: SavingStudy,
):
    with pytest.raises(HTTPException) as exc:
        saving_study_create(
            db_session,
            SavingStudyRequest(
                cups="testtesttesttesttest",
                current_rate_type_id=1000,
                energy_type=EnergyType.electricity,
                is_existing_client=False,
                is_from_sips=False,
                is_compare_conditions=False,
                analyzed_days=100,
                energy_price_1=100,
                client_type="particular",
            ),
            user_create,
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "rate_type_not_exist"


def test_list_saving_studies_ok(
    db_session: Session, saving_study: SavingStudy, deleted_saving_study: SavingStudy
):
    assert list_saving_studies(db_session, SavingStudyFilter()).count() == 1


def test_list_saving_studies_empty_ok(
    db_session: Session, deleted_saving_study: SavingStudy
):
    assert list_saving_studies(db_session, SavingStudyFilter()).count() == 0


def test_saving_study_update_ok(
    db_session: Session, saving_study: SavingStudy, electricity_rate_type: RateType
):
    saving_study_request = SavingStudyRequest(
        cups="testtesttesttesttest",
        current_rate_type_id=electricity_rate_type.id,
        energy_type=EnergyType.gas,
        is_existing_client=False,
        is_from_sips=False,
        is_compare_conditions=False,
        analyzed_days=365,
        energy_price_1=1000,
        client_type="particular",
        other_cost_kwh=10.3,
    )
    saving_study_updated = saving_study_update(
        db_session, saving_study.id, saving_study_request
    )
    assert saving_study_updated.current_rate_type_id == electricity_rate_type.id
    assert saving_study_updated.energy_type == EnergyType.gas
    assert saving_study_updated.is_existing_client is False
    assert saving_study_updated.is_from_sips is False
    assert saving_study_updated.is_compare_conditions is False
    assert saving_study_updated.analyzed_days == 365
    assert saving_study_updated.energy_price_1 == 1000
    assert saving_study_updated.client_type == "particular"
    assert saving_study_updated.other_cost_kwh == Decimal("10.3")


def test_saving_study_update_ok_no_rate_type(
    db_session: Session, saving_study: SavingStudy, electricity_rate_type: RateType
):
    saving_study_request = SavingStudyRequest(
        cups="testtesttesttesttest",
        energy_type=EnergyType.gas,
        is_existing_client=False,
        is_from_sips=False,
        is_compare_conditions=False,
        analyzed_days=365,
        energy_price_1=1000,
        client_type="particular",
        other_cost_kwh=10.3,
    )
    saving_study_updated = saving_study_update(
        db_session, saving_study.id, saving_study_request
    )
    assert saving_study_updated.energy_type == EnergyType.gas
    assert saving_study_updated.is_existing_client is False
    assert saving_study_updated.is_from_sips is False
    assert saving_study_updated.is_compare_conditions is False
    assert saving_study_updated.analyzed_days == 365
    assert saving_study_updated.energy_price_1 == 1000
    assert saving_study_updated.client_type == "particular"
    assert saving_study_updated.other_cost_kwh == Decimal("10.3")


def test_saving_study_update_error_current_rate_type_have_been_deleted(
    db_session: Session, saving_study: SavingStudy, electricity_rate_type: RateType
):
    saving_study_request = SavingStudyRequest(
        cups="testtesttesttesttest",
        energy_type=EnergyType.gas,
        is_existing_client=False,
        is_from_sips=False,
        is_compare_conditions=False,
        analyzed_days=365,
        energy_price_1=1000,
        client_type="particular",
        other_cost_kwh=10.3,
    )
    electricity_rate_type.is_deleted = True
    db_session.commit()
    with pytest.raises(HTTPException) as exc:
        _ = saving_study_update(db_session, saving_study.id, saving_study_request)

    assert exc.value.detail == "rate_type_not_exist"


def test_saving_study_update_saving_study_not_exist(
    db_session: Session, saving_study: SavingStudy, electricity_rate_type: RateType
):
    saving_study_request = SavingStudyRequest(
        cups="testtesttesttesttest",
        current_rate_type_id=electricity_rate_type.id,
        energy_type=EnergyType.gas,
        is_existing_client=False,
        is_from_sips=False,
        is_compare_conditions=False,
        analyzed_days=365,
        energy_price_1=1000,
        client_type="particular",
    )
    with pytest.raises(HTTPException) as exc:
        _ = saving_study_update(db_session, 100, saving_study_request)

    assert exc.value.detail == "saving_study_not_exist"


def test_saving_study_update_rate_type_not_exist(
    db_session: Session, saving_study: SavingStudy
):
    saving_study_request = SavingStudyRequest(
        cups="testtesttesttesttest",
        current_rate_type_id=1000,
        energy_type=EnergyType.gas,
        is_existing_client=False,
        is_from_sips=False,
        is_compare_conditions=False,
        analyzed_days=365,
        energy_price_1=1000,
        client_type="particular",
    )
    with pytest.raises(HTTPException) as exc:
        _ = saving_study_update(db_session, saving_study.id, saving_study_request)

    assert exc.value.detail == "rate_type_not_exist"


def test_validate_saving_study_ok():
    saving_study = SavingStudy(
        cups="stringstringstringst",
        current_rate_type_id=1,
        energy_type="gas",
        is_existing_client=False,
        is_from_sips=False,
        is_compare_conditions=True,
        analyzed_days=365,
        energy_price_1=100,
        power_1=22,
        client_type="particular",
    )
    assert (
        validate_saving_study_before_generating_rates(saving_study=saving_study) is None
    )


def test_validate_saving_study_rate_type_missing():
    saving_study = SavingStudy(
        cups="stringstringstringst",
        energy_type="gas",
        is_existing_client=False,
        is_from_sips=False,
        is_compare_conditions=True,
        analyzed_days=365,
        energy_price_1=100,
        power_1=22,
        client_type="particular",
    )
    with pytest.raises(HTTPException) as exc:
        validate_saving_study_before_generating_rates(saving_study=saving_study)

    assert exc.value.detail == "value_error.current_rate_type_id.missing"


def test_validate_saving_study_power_1_missing():
    saving_study = SavingStudy(
        cups="stringstringstringst",
        current_rate_type_id=1,
        energy_type="electricity",
        is_existing_client=False,
        is_from_sips=False,
        is_compare_conditions=True,
        analyzed_days=365,
        energy_price_1=100,
        client_type="particular",
    )
    with pytest.raises(HTTPException) as exc:
        validate_saving_study_before_generating_rates(saving_study=saving_study)

    assert exc.value.detail == "value_error.power_1.missing"


def test_validate_saving_study_power_2_missing():
    saving_study = SavingStudy(
        cups="stringstringstringst",
        current_rate_type_id=1,
        energy_type="electricity",
        is_existing_client=False,
        is_from_sips=False,
        is_compare_conditions=True,
        analyzed_days=365,
        energy_price_1=100,
        power_1=22,
        client_type="particular",
    )
    with pytest.raises(HTTPException) as exc:
        validate_saving_study_before_generating_rates(saving_study=saving_study)

    assert exc.value.detail == "value_error.power_2.missing"


def test_validate_saving_study_energy_price_1_missing():
    saving_study = SavingStudy(
        cups="stringstringstringst",
        current_rate_type_id=1,
        energy_type="electricity",
        is_existing_client=False,
        is_from_sips=False,
        is_compare_conditions=True,
        analyzed_days=365,
        power_1=10,
        power_2=20,
        client_type="particular",
    )
    with pytest.raises(HTTPException) as exc:
        validate_saving_study_before_generating_rates(saving_study=saving_study)

    assert exc.value.detail == "value_error.energy_price_1.missing"


def test_get_saving_study(db_session: Session, saving_study: SavingStudy):
    assert get_saving_study(db_session, 1)


def test_get_saving_study_not_exist(db_session: Session, saving_study: SavingStudy):
    with pytest.raises(HTTPException) as exc:
        get_saving_study(db_session, 1234)
    assert exc.value.detail == "saving_study_not_exist"


def test_get_rate_deleted(db_session: Session, saving_study: SavingStudy):
    saving_study.is_deleted = True

    with pytest.raises(HTTPException) as exc:
        get_saving_study(db_session, 1)

    assert exc.value.detail == "saving_study_not_exist"


def test_finish_saving_study_ok(
    db_session: Session, saving_study: SavingStudy, suggested_rates: List[SuggestedRate]
):
    saving_study, suggested_rate = finish_saving_study(
        db_session, saving_study.id, suggested_rates[0].id
    )

    assert saving_study.id == suggested_rates[0].id
    assert saving_study.status == SavingStudyStatusEnum.COMPLETED
    assert (
        db_session.query(SuggestedRate)
        .filter(SuggestedRate.is_selected == true())
        .count()
        == 1
    )


def test_finish_saving_study_suggested_rate_not_exist(
    db_session: Session, saving_study: SavingStudy, suggested_rates: List[SuggestedRate]
):
    with pytest.raises(HTTPException) as exc:
        saving_study, suggested_rate = finish_saving_study(
            db_session, saving_study.id, 1000
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "suggested_rate_not_exist"


def test_finish_saving_study_suggested_rate_not_related_to_study(
    db_session: Session,
    saving_study: SavingStudy,
    deleted_saving_study: SavingStudy,
    suggested_rates: List[SuggestedRate],
):
    suggested_rates[1].saving_study_id = 2
    with pytest.raises(HTTPException) as exc:
        saving_study, suggested_rate = finish_saving_study(
            db_session, saving_study.id, suggested_rates[1].id
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "suggested_rate_not_exist"


def test_finish_saving_study_study_not_exist(
    db_session: Session, saving_study: SavingStudy, suggested_rates: List[SuggestedRate]
):
    with pytest.raises(HTTPException) as exc:
        saving_study, suggested_rate = finish_saving_study(
            db_session, 1000, suggested_rates[0].id
        )

    assert exc.value.status_code == 404
    assert exc.value.detail == "saving_study_not_exist"


def test_list_suggested_rates_ok(
    db_session: Session, saving_study: SavingStudy, suggested_rate: SuggestedRate
):
    assert (
        list_suggested_rates(db_session, SuggestedRateFilter(), saving_study.id).count()
        == 1
    )


def test_list_suggested_rates_empty_ok(db_session: Session, saving_study: SavingStudy):
    assert (
        list_suggested_rates(db_session, SuggestedRateFilter(), saving_study.id).count()
        == 0
    )


def test_list_suggested_rates_saving_study_not_exist(db_session: Session):
    with pytest.raises(HTTPException) as exc:
        list_suggested_rates(db_session, SuggestedRateFilter(), 1234)
    assert exc.value.detail == "saving_study_not_exist"


def test_update_suggested_rate_ok(
    db_session: Session,
    saving_study: SavingStudy,
    suggested_rate: SuggestedRate,
    electricity_rate: Rate,
    other_cost: OtherCost,
):
    saving_study.annual_consumption = 15
    saving_study.power_6 = 10
    saving_study.power_2 = 10
    saving_study.consumption_p1 = Decimal("10.5")

    suggested_rate.other_costs_commission = Decimal("10.0")

    suggested_rate_data = SuggestedRateUpdate(applied_profit_margin=20.0)
    electricity_rate.name = "Rate name"
    suggested_rate = suggested_rate_update(
        db_session, saving_study.id, suggested_rate.id, suggested_rate_data
    )

    assert suggested_rate.applied_profit_margin == 20.0
    assert suggested_rate.final_cost == Decimal("564.49")
    assert suggested_rate.energy_cost == Decimal("180.50")
    assert suggested_rate.power_cost == 0
    assert suggested_rate.other_costs == Decimal("384.00")
    assert suggested_rate.ie_cost == Decimal("0")
    assert suggested_rate.iva_cost == Decimal("0")
    assert suggested_rate.fixed_cost is None
    assert suggested_rate.ih_cost is None
    assert suggested_rate.theoretical_commission == Decimal("0")
    assert suggested_rate.total_commission == Decimal("10.00")
    assert suggested_rate.other_costs_commission == Decimal("10.00")


def test_update_suggested_rate_exception(
    db_session: Session, saving_study: SavingStudy, suggested_rate: SuggestedRate
):
    suggeste_rate_data = SuggestedRateUpdate(applied_profit_margin=15.0)
    with pytest.raises(HTTPException) as exc:
        _ = suggested_rate_update(
            db_session, saving_study.id, suggested_rate.id, suggeste_rate_data
        )

    assert exc.value.detail == "value_error.applied_profit_margin.value_error"


def test_validate_suggested_rate_for_update_ok(suggested_rate: SuggestedRate):
    assert (
        validate_suggested_rate_for_update(
            suggested_rate, {"applied_profit_margin": 20.0}
        )
        is None
    )


def test_validate_suggested_rate_for_update_raises_exception(
    suggested_rate: SuggestedRate,
):
    with pytest.raises(HTTPException) as exc:
        validate_suggested_rate_for_update(
            suggested_rate, {"applied_profit_margin": 15.0}
        )

    assert exc.value.detail == "value_error.applied_profit_margin.value_error"


def test_delete_saving_study_ok(
    db_session: Session, saving_study: SavingStudy, deleted_saving_study: SavingStudy
):
    deleted_saving_study.is_deleted = False
    db_session.add(deleted_saving_study)
    db_session.commit()
    saving_study_data = SavingStudyDeleteRequest(ids=[1, 2])
    delete_saving_study(db_session, saving_study_data)
    assert (
        db_session.query(SavingStudy).filter(SavingStudy.is_deleted == true()).count()
        == 2
    )
    assert db_session.query(SavingStudy).count() == 2


def test_delete_saving_study_ok_id_not_exist(
    db_session: Session,
    saving_study: SavingStudy,
):
    saving_study_data = SavingStudyDeleteRequest(ids=[1000, 2000])
    delete_saving_study(db_session, saving_study_data)
    assert (
        db_session.query(SavingStudy).filter(SavingStudy.is_deleted == true()).count()
        == 0
    )
    assert db_session.query(SavingStudy).count() == 1


def test_duplicate_saving_study_ok(
    db_session: Session, saving_study: SavingStudy, user_create: User
):
    new_saving_study = duplicate_saving_study(db_session, saving_study.id, user_create)
    assert new_saving_study.is_deleted is False
    assert new_saving_study.is_existing_client is False
    assert new_saving_study.is_compare_conditions is False
    assert new_saving_study.is_from_sips is False
    assert new_saving_study.status == SavingStudyStatusEnum.IN_PROGRESS
    assert new_saving_study.energy_type == EnergyType.electricity
    assert new_saving_study.cups == "ES0021000000000000AA"
    assert new_saving_study.client_name == "Client name"
    assert new_saving_study.client_type == "particular"
    assert new_saving_study.client_nif == "12345678A"
    assert new_saving_study.current_rate_type_id == 1
    assert new_saving_study.analyzed_days == 365
    assert new_saving_study.annual_consumption == Decimal("15.34")
    assert new_saving_study.consumption_p1 is None
    assert new_saving_study.consumption_p2 is None
    assert new_saving_study.consumption_p3 is None
    assert new_saving_study.consumption_p4 is None
    assert new_saving_study.consumption_p5 is None
    assert new_saving_study.consumption_p6 is None
    assert new_saving_study.power_1 is None
    assert new_saving_study.power_2 is None
    assert new_saving_study.power_3 is None
    assert new_saving_study.power_4 is None
    assert new_saving_study.power_5 is None
    assert new_saving_study.power_6 == Decimal("5.75")
    assert new_saving_study.power_price_1 is None
    assert new_saving_study.power_price_2 is None
    assert new_saving_study.power_price_3 is None
    assert new_saving_study.power_price_4 is None
    assert new_saving_study.power_price_5 is None
    assert new_saving_study.power_price_6 is None
    assert new_saving_study.energy_price_1 == Decimal("27.3")
    assert new_saving_study.energy_price_2 is None
    assert new_saving_study.energy_price_3 is None
    assert new_saving_study.energy_price_4 is None
    assert new_saving_study.energy_price_5 is None
    assert new_saving_study.energy_price_6 == Decimal("23.6")


def test_duplicate_saving_study_not_found(
    db_session: Session, saving_study: SavingStudy, user_create: User
):
    with pytest.raises(HTTPException) as exc:
        _ = duplicate_saving_study(db_session, 1000, user_create)

    assert exc.value.status_code == 404
    assert exc.value.detail == "saving_study_not_exist"
