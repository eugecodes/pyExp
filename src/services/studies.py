import logging
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Tuple

from fastapi import HTTPException, status
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Query, Session
from sqlalchemy.sql.expression import false

from src.infrastructure.sqlalchemy.common import update_obj_db
from src.infrastructure.sqlalchemy.costs import get_energy_cost_by
from src.infrastructure.sqlalchemy.rates import get_rate_by
from src.infrastructure.sqlalchemy.studies import (
    create_saving_study_db,
    delete_study_suggested_rates,
    finish_study_db,
    get_candidate_rates,
    get_other_costs_rate_study,
    get_saving_studies_queryset,
    get_saving_study_by,
    get_suggested_rate_by,
    get_suggested_rates_queryset,
)
from src.modules.commissions.models import RangeType
from src.modules.costs.models import EnergyCost, OtherCostType
from src.modules.margins.models import Margin, MarginType
from src.modules.rates.models import EnergyType, PriceType, Rate
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
from src.services.common import update_from_dict
from src.services.rates import get_rate_type
from src.services.sips import fill_study_with_sips

logger = logging.getLogger(__name__)

DAYS_PER_MONTH = Decimal("30.4167")
OTHER_COST_FIELDS = {
    "eur/month": "other_cost_kwh",
    "percentage": "other_cost_percentage",
    "eur/kwh": "other_cost_eur_month",
}
IVA = "iva"
IVA_REDUCIDO = "iva_reducido"
IMP_HIDROCARBUROS = "imp_hidrocarburos"
IMP_ELECTRICOS = "imp_electricos"


class CostCalculator(ABC):
    def __init__(self, db_session: Session, saving_study: SavingStudy):
        self.db_session = db_session
        self.saving_study = saving_study

    @abstractmethod
    def compute_total_cost(
        self,
        conf_calculator_info: CostCalculatorInfo,
        applied_margin: Decimal,
        current_other_cost: bool = False,
    ) -> SuggestedRateCosts:
        raise NotImplementedError

    @abstractmethod
    def get_energy_cost(
        self, conf_calculator_info: CostCalculatorInfo, applied_margin: Decimal
    ) -> Decimal:
        raise NotImplementedError

    def compute_other_cost(
        self,
        type: OtherCostType,
        quantity: Decimal,
        power_cost: Decimal,
        energy_cost: Decimal,
    ) -> Decimal:
        if quantity is None:
            return Decimal("0")
        if type == OtherCostType.eur_month:
            return (
                Decimal(str(self.saving_study.analyzed_days))
                / Decimal(str(DAYS_PER_MONTH))
                * Decimal(str(quantity))
            )
        elif type == OtherCostType.eur_kwh:
            return Decimal(str(self.saving_study.total_consumption)) * Decimal(
                str(quantity)
            )
        elif type == OtherCostType.percentage:
            return Decimal(str((energy_cost + power_cost))) * Decimal(str(quantity))

    def get_others_costs(
        self,
        cost_calculator_info: CostCalculatorInfo,
        power_cost: Decimal,
        energy_cost: Decimal,
    ) -> Decimal:
        total_cost = Decimal("0")
        for other_cost in get_other_costs_rate_study(
            self.db_session, self.saving_study, cost_calculator_info.id
        ):
            total_cost += self.compute_other_cost(
                other_cost.type, other_cost.quantity, power_cost, energy_cost
            )
        return total_cost

    def get_iva(self) -> Decimal:
        iva = get_energy_cost_by(self.db_session, EnergyCost.code == IVA)
        if not iva:
            return Decimal("0")
        return iva.amount / 100

    def get_current_other_costs(self, cost: Decimal, energy_cost: Decimal) -> Decimal:
        return sum(
            [
                self.compute_other_cost(
                    other_cost_type.value,
                    getattr(
                        self.saving_study, OTHER_COST_FIELDS[other_cost_type.value]
                    ),
                    cost,
                    energy_cost,
                )
                for other_cost_type in OtherCostType
            ]
        )


class CostCalculatorElectricity(CostCalculator):
    def compute_total_cost(
        self,
        cost_calculator_info: CostCalculatorInfo,
        applied_margin: Decimal,
        current_other_cost: bool = False,
    ) -> SuggestedRateCosts:
        energy_cost = self.get_energy_cost(cost_calculator_info, applied_margin)
        power_cost = self.get_power_cost(cost_calculator_info)
        other_costs = (
            self.get_current_other_costs(power_cost, energy_cost)
            if current_other_cost
            else self.get_others_costs(cost_calculator_info, power_cost, energy_cost)
        )
        ie_cost = self.get_ie() * (energy_cost + power_cost + other_costs)
        iva_cost = self.get_iva() * (energy_cost + power_cost + other_costs + ie_cost)

        starting_log = (
            f"Detailed cost for rate {cost_calculator_info.name}"
            if current_other_cost
            else "Current cost for saving study with"
        )
        logger.info(
            "[saving_study_id=%s] %s energy_cost=%s power_cost=%s "
            "other_costs=%s ie_cost=%s iva_cost=%s",
            self.saving_study.id,
            starting_log,
            energy_cost,
            power_cost,
            other_costs,
            ie_cost,
            iva_cost,
        )
        costs = SuggestedRateCosts(
            total_cost=energy_cost + power_cost + other_costs + ie_cost + iva_cost,
            energy_cost=energy_cost,
            power_cost=power_cost,
            other_costs=other_costs,
            ie_cost=ie_cost,
            iva_cost=iva_cost,
        )
        return costs

    def get_energy_cost(
        self, cost_calculator_info: CostCalculatorInfo, applied_margin: Decimal
    ) -> Decimal:
        cost_list = []
        for i in range(1, 7):
            energy_price = getattr(cost_calculator_info, f"energy_price_{i}")
            consumption = getattr(self.saving_study, f"consumption_p{i}")
            if energy_price is None or consumption is None:
                break
            energy_price = (
                energy_price + applied_margin
                if cost_calculator_info.price_type == PriceType.fixed_base
                else energy_price
            )
            cost_list.append(energy_price * consumption)
        return sum(cost_list)

    def get_power_cost(self, cost_calculator_info: CostCalculatorInfo) -> Decimal:
        cost_list = []
        for i in range(1, 7):
            power_price = getattr(cost_calculator_info, f"power_price_{i}")
            power = getattr(self.saving_study, f"power_{i}")
            if power_price is None or power is None:
                break
            cost_list.append(power_price * power)
        return sum(cost_list) * self.saving_study.analyzed_days

    def get_ie(self) -> Decimal:
        ie = get_energy_cost_by(self.db_session, EnergyCost.code == IMP_ELECTRICOS)
        if not ie:
            return Decimal("0")
        return ie.amount / 100


class CostCalculatorGas(CostCalculator):
    def compute_total_cost(
        self,
        cost_calculator_info: CostCalculatorInfo,
        applied_margin: Decimal,
        current_other_cost: bool = False,
    ) -> SuggestedRateCosts:
        energy_cost = self.get_energy_cost(cost_calculator_info, applied_margin)
        fixed_cost = self.get_fixed_cost(cost_calculator_info.fixed_term_price)
        other_costs = (
            self.get_current_other_costs(fixed_cost, energy_cost)
            if current_other_cost
            else self.get_others_costs(cost_calculator_info, fixed_cost, energy_cost)
        )
        ih_cost = (
            self.get_ih() * self.saving_study.consumption_p1
            if self.saving_study.consumption_p1
            else Decimal("0")
        )
        iva_cost = self.get_iva() * (energy_cost + fixed_cost + other_costs + ih_cost)

        starting_log = (
            f"Detailled cost for rate {cost_calculator_info.name}"
            if current_other_cost
            else "Current cost for saving study with"
        )
        logger.info(
            "[saving_study_id=%s] %s energy_cost=%s fixed_cost=%s "
            "other_costs=%s ih_cost=%s iva_cost=%s",
            self.saving_study.id,
            starting_log,
            energy_cost,
            fixed_cost,
            other_costs,
            ih_cost,
            iva_cost,
        )
        costs = SuggestedRateCosts(
            total_cost=energy_cost + fixed_cost + other_costs + ih_cost + iva_cost,
            energy_cost=energy_cost,
            fixed_cost=fixed_cost,
            other_costs=other_costs,
            ih_cost=ih_cost,
            iva_cost=iva_cost,
        )
        return costs

    def get_energy_cost(
        self, cost_calculator_info: CostCalculatorInfo, applied_margin: Decimal
    ) -> Decimal:
        # USE p1 to compute energy cost
        applied_margin = (
            applied_margin
            if cost_calculator_info.price_type == PriceType.fixed_base
            else Decimal("0")
        )
        return (
            cost_calculator_info.energy_price_1 + applied_margin
        ) * self.saving_study.consumption_p1

    def get_fixed_cost(self, fixed_term_price: Decimal) -> Decimal:
        return fixed_term_price * self.saving_study.analyzed_days

    def get_ih(self) -> Decimal:
        ih = get_energy_cost_by(self.db_session, EnergyCost.code == IMP_HIDROCARBUROS)
        if not ih:
            return Decimal("0")
        return Decimal(str(ih.amount))


class ComissionCalculator(ABC):
    def __init__(self, saving_study: SavingStudy):
        self.saving_study = saving_study

    @abstractmethod
    def compute_comission(self, rate: Rate, applied_margin: Decimal) -> Decimal:
        raise NotImplementedError


class ComissionCalculatorFixedBase(ComissionCalculator):
    def compute_comission(self, rate: Rate, applied_margin: Decimal) -> Decimal:
        percentage_Test_commission = (
            rate.commissions[0].percentage_Test_commission
            if rate.commissions
            and rate.commissions[0]
            and rate.commissions[0].percentage_Test_commission
            else Decimal("0")
        )

        logger.info(
            "[saving_study_id=%s] Detailed theoretical_commission for rate %s annual_consumption=%s "
            "applied_margin=%s percentage_Test_commission=%s",
            self.saving_study.id,
            rate.name,
            self.saving_study.annual_consumption,
            applied_margin,
            percentage_Test_commission,
        )

        return (
            self.saving_study.annual_consumption
            * applied_margin
            * percentage_Test_commission
            / 100
        )


class ComissionCalculatorFixedFixed(ComissionCalculator):
    def compute_comission(
        self, rate: Rate, applied_margin: Decimal | None = None
    ) -> Decimal:
        theoretical_commission = Decimal("0")
        power = self.saving_study.power_6 or self.saving_study.power_2
        for commission in rate.commissions:
            if (
                commission.rate_type_segmentation
                and (
                    commission.range_type == RangeType.consumption
                    and (
                        commission.min_consumption
                        <= self.saving_study.annual_consumption
                        <= commission.max_consumption
                    )
                )
                or (
                    commission.range_type == RangeType.power
                    and (commission.min_power <= power <= commission.max_power)
                )
            ):
                theoretical_commission += commission.Test_commission

        logger.info(
            "[saving_study_id=%s] Detailled theoretical_commission for rate %s theoretical_commission=%s",
            self.saving_study.id,
            rate.name,
            theoretical_commission,
        )

        return theoretical_commission


class CalculatorsFactory:
    COST_CALCULATORS = {
        EnergyType.electricity: CostCalculatorElectricity,
        EnergyType.gas: CostCalculatorGas,
    }

    COMISSION_CALCULATORS = {
        PriceType.fixed_base: ComissionCalculatorFixedBase,
        PriceType.fixed_fixed: ComissionCalculatorFixedFixed,
    }

    @classmethod
    def init_cost_calculator(
        cls, energy_type: EnergyType, db_session: Session, saving_study: SavingStudy
    ) -> CostCalculator:
        return cls.COST_CALCULATORS[energy_type](db_session, saving_study)

    @classmethod
    def init_comission_calculator(
        cls, price_type: PriceType, saving_study: SavingStudy
    ) -> ComissionCalculator:
        return cls.COMISSION_CALCULATORS[price_type](saving_study)


def generate_suggested_rates_for_study(
    db_session: Session, saving_study_id: int
) -> List[SuggestedRate]:
    saving_study = get_saving_study(db_session, saving_study_id)
    validate_saving_study_before_generating_rates(saving_study)
    _ = get_rate_type(db_session, saving_study.current_rate_type_id)

    logger.info("[saving_study_id=%s] Generating suggested rates", saving_study.id)
    suggested_rates_deleted = delete_study_suggested_rates(db_session, saving_study.id)
    logger.info(
        "[saving_study_id=%s] %s Suggested rates deleted",
        saving_study.id,
        suggested_rates_deleted,
    )
    candidate_rates = get_candidate_rates(db_session, saving_study.id)
    logger.info(
        "[saving_study_id=%s] %s Candidate rates found",
        saving_study.id,
        candidate_rates.count(),
    )

    suggested_rates_generator = SuggestedRatesGenerator(db_session, saving_study)
    suggested_rates = suggested_rates_generator.generate_suggested_rates(
        candidate_rates
    )
    try:
        db_session.add_all(suggested_rates)
        db_session.commit()
    except DataError:
        db_session.rollback()
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="value_error.numeric_field_overflow",
        )
    logger.info(
        "[saving_study_id=%s] %s Suggested rates saved",
        saving_study.id,
        len(suggested_rates),
    )
    return suggested_rates


class SuggestedRatesGenerator:
    def __init__(self, db_session: Session, saving_study: SavingStudy) -> None:
        self.db_session = db_session
        self.saving_study = saving_study

    def get_default_margin_rate(self, rate: Rate) -> Margin:
        if len(rate.margin) == 1 and rate.margin[0].type == MarginType.rate_type:
            return rate.margin[0]

        if not self.saving_study.annual_consumption:
            return self.get_margin_with_min_consumption(rate.margin)

        # filter only the margin inside the consume range
        margins_in_range = [
            margin
            for margin in rate.margin
            if margin.min_consumption
            <= self.saving_study.annual_consumption
            <= margin.max_consumption
        ]
        return margins_in_range[0] if len(margins_in_range) == 1 else None

    def get_margin_with_min_consumption(self, margins: list[Margin]) -> Margin | None:
        margins_with_min_consumption = [
            margin for margin in margins if margin.min_consumption is not None
        ]
        if margins_with_min_consumption:
            return min(
                margins_with_min_consumption, key=lambda margin: margin.min_consumption
            )

    def generate_suggested_rates(self, rates: List[Rate]) -> List[SuggestedRate]:
        logger.info(
            "[saving_study_id=%s] Generating suggested rates...", self.saving_study.id
        )
        # TODO: clean previous suggested rates
        current_cost = Decimal("0")
        if self.saving_study.is_compare_conditions:
            current_cost = self.compute_current_cost()
        suggested_rates = []
        for rate in rates:
            default_margin = self.get_default_margin_rate(rate)
            applied_margin = (
                default_margin.min_margin if default_margin else Decimal("0")
            )
            costs, theoretical_commission = self.compute_final_cost_and_commission(
                rate, applied_margin
            )
            other_costs_commission = self.compute_other_costs_commission(rate)

            suggested_rate = SuggestedRate(
                saving_study_id=self.saving_study.id,
                marketer_name=rate.marketer.name,
                has_contractual_commitment=rate.permanency,
                duration=rate.length,
                rate_name=rate.name,
                is_full_renewable=getattr(rate, "is_full_renewable", False) or False,
                has_net_metering=getattr(rate, "compensation_surplus", False) or False,
                net_metering_value=getattr(rate, "compensation_surplus_value", 0) or 0,
                profit_margin_type=getattr(default_margin, "type", None),
                max_profit_margin=getattr(default_margin, "max_margin", 0) or 0,
                min_profit_margin=getattr(default_margin, "min_margin", 0) or 0,
                applied_profit_margin=applied_margin,
                energy_price_1=rate.energy_price_1,
                energy_price_2=rate.energy_price_2,
                energy_price_3=rate.energy_price_3,
                energy_price_4=rate.energy_price_4,
                energy_price_5=rate.energy_price_5,
                energy_price_6=rate.energy_price_6,
                power_price_1=rate.power_price_1,
                power_price_2=rate.power_price_2,
                power_price_3=rate.power_price_3,
                power_price_4=rate.power_price_4,
                power_price_5=rate.power_price_5,
                power_price_6=rate.power_price_6,
                fixed_term_price=rate.fixed_term_price,
                price_type=rate.price_type,
                final_cost=costs.final_cost,
                energy_cost=costs.energy_cost,
                other_costs=costs.other_costs,
                iva_cost=costs.iva_cost,
                power_cost=costs.power_cost,
                ie_cost=costs.ie_cost,
                fixed_cost=costs.fixed_cost,
                ih_cost=costs.ih_cost,
                total_commission=theoretical_commission + other_costs_commission,
                theoretical_commission=theoretical_commission,
                other_costs_commission=other_costs_commission,
            )

            if self.saving_study.is_compare_conditions and current_cost:
                suggested_rate.saving_relative = (
                    (current_cost - costs.final_cost) / current_cost * 100
                )
                suggested_rate.saving_absolute = current_cost - costs.final_cost

            suggested_rates.append(suggested_rate)
            logger.info(
                "[saving_study_id=%s] Suggested rate generated: applied_margin=%s, final_cost=%s rate=%s",
                self.saving_study.id,
                applied_margin,
                costs.final_cost,
                suggested_rate,
            )

        logger.info(
            "[saving_study_id=%s] %s Suggested rates generated for saving study %s",
            self.saving_study.id,
            len(suggested_rates),
            self.saving_study,
        )

        return suggested_rates

    def compute_current_cost(self) -> Decimal:
        logger.info(
            "[saving_study_id=%s] Computing current cost with energy  %s",
            self.saving_study.id,
            self.saving_study.energy_type,
        )

        cost_calculator = CalculatorsFactory.init_cost_calculator(
            self.saving_study.energy_type, self.db_session, self.saving_study
        )
        cost_calculator_info = CostCalculatorInfo.from_orm(self.saving_study)
        cost_calculator_info.fixed_term_price = self.saving_study.fixed_price
        current_cost = cost_calculator.compute_total_cost(
            cost_calculator_info, Decimal("0"), current_other_cost=True
        )

        return current_cost.total_cost

    def compute_final_cost_and_commission(
        self, rate: Rate, applied_margin: Decimal
    ) -> (SuggestedRateCosts, Decimal):
        logger.info(
            "[saving_study_id=%s] Computing final cost for rate %s with energy  %s",
            self.saving_study.id,
            rate,
            rate.rate_type.energy_type,
        )
        comission_calculator = CalculatorsFactory.init_comission_calculator(
            rate.price_type, self.saving_study
        )
        theoretical_commission = comission_calculator.compute_comission(
            rate, applied_margin
        )
        cost_calculator = CalculatorsFactory.init_cost_calculator(
            rate.rate_type.energy_type, self.db_session, self.saving_study
        )
        costs = cost_calculator.compute_total_cost(
            CostCalculatorInfo.from_orm(rate), applied_margin
        )
        costs.final_cost = costs.total_cost + theoretical_commission

        return costs, theoretical_commission

    def compute_other_costs_commission(self, rate: Rate) -> Decimal:
        if not rate.other_costs:
            return Decimal("0")
        return sum(cost.extra_fee for cost in rate.other_costs)


def saving_study_create(
    db: Session, saving_study_request: SavingStudyRequest, current_user: User
) -> SavingStudy:
    saving_study = SavingStudy(**saving_study_request.dict())
    saving_study.user_creator_id = current_user.id

    if saving_study_request.current_rate_type_id:
        current_rate_type = get_rate_type(db, saving_study_request.current_rate_type_id)
        saving_study.current_rate_type_id = current_rate_type.id

    if (
        saving_study_request.is_from_sips
        and saving_study.energy_type == EnergyType.electricity
    ):
        saving_study = fill_study_with_sips(saving_study)

    try:
        saving_study = create_saving_study_db(db, saving_study)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="value_error.already_exists"
        )
    return saving_study


def list_saving_studies(db: Session, saving_study_filter: SavingStudyFilter):
    return saving_study_filter.sort(
        saving_study_filter.filter(
            get_saving_studies_queryset(db, None, SavingStudy.is_deleted == false())
        )
    )


def get_saving_study(db: Session, saving_study_id: int) -> SavingStudy:
    saving_study = get_saving_study_by(
        db, SavingStudy.id == saving_study_id, SavingStudy.is_deleted == false()
    )

    if not saving_study:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="saving_study_not_exist"
        )

    return saving_study


def saving_study_update(
    db: Session,
    saving_study_id: int,
    saving_study_data: SavingStudyRequest,
) -> SavingStudy:
    saving_study_dict = saving_study_data.dict(exclude_unset=True)

    saving_study = get_saving_study(db, saving_study_id)
    rate_type_id = saving_study_dict.get("current_rate_type_id")
    if not rate_type_id:
        _ = (
            get_rate_type(db, saving_study.current_rate_type_id)
            if saving_study.current_rate_type_id
            else None
        )
    else:
        _ = get_rate_type(db, rate_type_id)

    update_from_dict(saving_study, saving_study_dict)
    saving_study = update_obj_db(db, saving_study)
    return saving_study


def validate_saving_study_before_generating_rates(saving_study: SavingStudy) -> None:
    if not saving_study.current_rate_type_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.current_rate_type_id.missing",
        )

    if saving_study.energy_type == EnergyType.electricity:
        if not saving_study.power_1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="value_error.power_1.missing",
            )
        elif not saving_study.power_2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="value_error.power_2.missing",
            )

    if saving_study.is_compare_conditions and not saving_study.energy_price_1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.energy_price_1.missing",
        )


def list_suggested_rates(
    db: Session, suggested_rate_filter: SuggestedRateFilter, saving_study_id: int
) -> Query:
    _ = get_saving_study(db, saving_study_id)
    return suggested_rate_filter.sort(
        suggested_rate_filter.filter(
            get_suggested_rates_queryset(
                db, None, SuggestedRate.saving_study_id == saving_study_id
            )
        )
    )


def get_suggested_rate(
    db: Session, sugggested_rate_id: int, saving_study_id: int
) -> SuggestedRate:
    suggested_rate = get_suggested_rate_by(
        db,
        SuggestedRate.saving_study_id == saving_study_id,
        SuggestedRate.id == sugggested_rate_id,
    )

    if not suggested_rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="suggested_rate_not_exist"
        )

    return suggested_rate


def finish_saving_study(
    db: Session, saving_study_id: int, suggested_rate_id: int
) -> Tuple[SavingStudy, SuggestedRate]:
    saving_study = get_saving_study(db, saving_study_id)
    suggested_rate = get_suggested_rate(db, suggested_rate_id, saving_study_id)
    saving_study, suggested_rate = finish_study_db(db, saving_study, suggested_rate)
    return saving_study, suggested_rate


def suggested_rate_update(
    db: Session,
    saving_study_id: int,
    suggested_rate_id: int,
    suggested_rate_data: SuggestedRateUpdate,
) -> SuggestedRate:
    saving_study = get_saving_study(db, saving_study_id)
    suggested_rate = get_suggested_rate(db, suggested_rate_id, saving_study_id)

    suggested_rate_dict = suggested_rate_data.dict(exclude_unset=True)
    validate_suggested_rate_for_update(suggested_rate, suggested_rate_dict)

    rate = get_rate_by(db, Rate.name == suggested_rate.rate_name)
    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="rate_not_exist"
        )
    suggested_rate_generator = SuggestedRatesGenerator(db, saving_study)
    (
        new_costs,
        theoretical_commission,
    ) = suggested_rate_generator.compute_final_cost_and_commission(
        rate, suggested_rate_dict["applied_profit_margin"]
    )
    suggested_rate.final_cost = new_costs.final_cost
    suggested_rate.energy_cost = new_costs.energy_cost
    suggested_rate.power_cost = new_costs.power_cost
    suggested_rate.fixed_cost = new_costs.fixed_cost
    suggested_rate.ie_cost = new_costs.ie_cost
    suggested_rate.ih_cost = new_costs.ih_cost
    suggested_rate.other_costs = new_costs.other_costs
    suggested_rate.iva_cost = new_costs.iva_cost

    suggested_rate.theoretical_commission = theoretical_commission
    suggested_rate.total_commission = (
        suggested_rate.other_costs_commission + theoretical_commission
        if suggested_rate.other_costs_commission
        else theoretical_commission
    )

    suggested_rate.applied_profit_margin = suggested_rate_dict["applied_profit_margin"]
    update_obj_db(db, suggested_rate)

    return suggested_rate


def validate_suggested_rate_for_update(
    suggested_rate: SuggestedRate, data_for_update: dict
) -> None:
    applied_profit_margin = data_for_update["applied_profit_margin"]
    if (
        applied_profit_margin < suggested_rate.min_profit_margin
        or applied_profit_margin > suggested_rate.max_profit_margin
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.applied_profit_margin.value_error",
        )


def delete_saving_study(
    db: Session, saving_study_data: SavingStudyDeleteRequest
) -> None:
    db.query(SavingStudy).filter(SavingStudy.id.in_(saving_study_data.ids)).update(
        {"is_deleted": True}
    )
    db.commit()


def duplicate_saving_study(
    db: Session, saving_study_id: int, current_user: User
) -> SavingStudy:
    saving_study = get_saving_study(db, saving_study_id)
    new_saving_study = SavingStudy(
        is_existing_client=saving_study.is_existing_client,
        is_from_sips=False,
        is_compare_conditions=saving_study.is_compare_conditions,
        status=SavingStudyStatusEnum.IN_PROGRESS,
        energy_type=saving_study.energy_type,
        cups=saving_study.cups,
        client_type=saving_study.client_type,
        client_name=saving_study.client_name,
        client_nif=saving_study.client_nif,
        current_rate_type_id=saving_study.current_rate_type_id,
        analyzed_days=saving_study.analyzed_days,
        annual_consumption=saving_study.annual_consumption,
        consumption_p1=saving_study.consumption_p1,
        consumption_p2=saving_study.consumption_p2,
        consumption_p3=saving_study.consumption_p3,
        consumption_p4=saving_study.consumption_p4,
        consumption_p5=saving_study.consumption_p5,
        consumption_p6=saving_study.consumption_p6,
        energy_price_1=saving_study.energy_price_1,
        energy_price_2=saving_study.energy_price_2,
        energy_price_3=saving_study.energy_price_3,
        energy_price_4=saving_study.energy_price_4,
        energy_price_5=saving_study.energy_price_5,
        energy_price_6=saving_study.energy_price_6,
        power_1=saving_study.power_1,
        power_2=saving_study.power_2,
        power_3=saving_study.power_3,
        power_4=saving_study.power_4,
        power_5=saving_study.power_5,
        power_6=saving_study.power_6,
        power_price_1=saving_study.power_price_1,
        power_price_2=saving_study.power_price_2,
        power_price_3=saving_study.power_price_3,
        power_price_4=saving_study.power_price_4,
        power_price_5=saving_study.power_price_5,
        power_price_6=saving_study.power_price_6,
        user_creator_id=current_user.id,
    )

    db.add(new_saving_study)
    db.commit()
    return new_saving_study
