from datetime import datetime
from decimal import Decimal
from typing import List

from fastapi_filter import FilterDepends, with_prefix
from pydantic import BaseModel, condecimal, conint, constr

from src.infrastructure.sqlalchemy.filters import Filter
from src.modules.rates.models import ClientType, EnergyType, PriceType
from src.modules.rates.schemas import RateTypeBasicResponse, RelatedRateTypeFilter
from src.modules.saving_studies.models import (
    SavingStudy,
    SavingStudyStatusEnum,
    SuggestedRate,
)
from src.modules.users.schemas import BaseUserResponsible, RelatedUserFilter
from utils.i18n import trans as _


class BaseSavingStudy(BaseModel):
    energy_type: EnergyType
    is_existing_client: bool
    is_from_sips: bool
    is_compare_conditions: bool
    cups: constr(min_length=20, max_length=22)
    client_type: ClientType | None
    client_name: constr(max_length=124) | None
    client_nif: constr(max_length=9) | None
    analyzed_days: conint(gt=0) | None
    consumption_p1: condecimal(decimal_places=2, ge=0) | None
    consumption_p2: condecimal(decimal_places=2, ge=0) | None
    consumption_p3: condecimal(decimal_places=2, ge=0) | None
    consumption_p4: condecimal(decimal_places=2, ge=0) | None
    consumption_p5: condecimal(decimal_places=2, ge=0) | None
    consumption_p6: condecimal(decimal_places=2, ge=0) | None
    annual_consumption: condecimal(decimal_places=2, ge=0) | None
    power_1: condecimal(decimal_places=2, ge=0) | None
    power_2: condecimal(decimal_places=2, ge=0) | None
    power_3: condecimal(decimal_places=2, ge=0) | None
    power_4: condecimal(decimal_places=2, ge=0) | None
    power_5: condecimal(decimal_places=2, ge=0) | None
    power_6: condecimal(decimal_places=2, ge=0) | None
    current_marketer: str | None
    power_price_1: condecimal(decimal_places=6, ge=0) | None
    power_price_2: condecimal(decimal_places=6, ge=0) | None
    power_price_3: condecimal(decimal_places=6, ge=0) | None
    power_price_4: condecimal(decimal_places=6, ge=0) | None
    power_price_5: condecimal(decimal_places=6, ge=0) | None
    power_price_6: condecimal(decimal_places=6, ge=0) | None
    energy_price_1: condecimal(decimal_places=6, ge=0) | None
    energy_price_2: condecimal(decimal_places=6, ge=0) | None
    energy_price_3: condecimal(decimal_places=6, ge=0) | None
    energy_price_4: condecimal(decimal_places=6, ge=0) | None
    energy_price_5: condecimal(decimal_places=6, ge=0) | None
    energy_price_6: condecimal(decimal_places=6, ge=0) | None
    fixed_price: condecimal(decimal_places=6, ge=0) | None
    other_cost_kwh: condecimal(decimal_places=6, ge=0) | None
    other_cost_percentage: condecimal(decimal_places=6, ge=0) | None
    other_cost_eur_month: condecimal(decimal_places=6, ge=0) | None

    class Config:
        orm_mode = True


class SavingStudyRequest(BaseSavingStudy):
    current_rate_type_id: int | None


class SavingStudyDeleteRequest(BaseModel):
    ids: list[int]


class SuggestedRateUpdate(BaseModel):
    applied_profit_margin: condecimal(decimal_places=6, ge=0)

    class Config:
        orm_mode = True


class SuggestedRateResponse(BaseModel):
    id: int
    marketer_name: str
    rate_name: str
    is_selected: bool
    has_contractual_commitment: bool
    duration: conint(gt=0)
    is_full_renewable: bool
    has_net_metering: bool
    net_metering_value: condecimal(decimal_places=6, ge=0)
    applied_profit_margin: condecimal(decimal_places=6, ge=0)

    energy_price_1: condecimal(decimal_places=6, ge=0) | None
    energy_price_2: condecimal(decimal_places=6, ge=0) | None
    energy_price_3: condecimal(decimal_places=6, ge=0) | None
    energy_price_4: condecimal(decimal_places=6, ge=0) | None
    energy_price_5: condecimal(decimal_places=6, ge=0) | None
    energy_price_6: condecimal(decimal_places=6, ge=0) | None
    power_price_1: condecimal(decimal_places=6, ge=0) | None
    power_price_2: condecimal(decimal_places=6, ge=0) | None
    power_price_3: condecimal(decimal_places=6, ge=0) | None
    power_price_4: condecimal(decimal_places=6, ge=0) | None
    power_price_5: condecimal(decimal_places=6, ge=0) | None
    power_price_6: condecimal(decimal_places=6, ge=0) | None
    fixed_term_price: condecimal(decimal_places=6, ge=0) | None
    price_type: PriceType | None

    final_cost: condecimal(decimal_places=6, ge=0) | None
    energy_cost: condecimal(decimal_places=6, ge=0) | None
    power_cost: condecimal(decimal_places=6, ge=0) | None
    fixed_cost: condecimal(decimal_places=6, ge=0) | None
    other_costs: condecimal(decimal_places=6, ge=0) | None
    ie_cost: condecimal(decimal_places=6, ge=0) | None
    ih_cost: condecimal(decimal_places=6, ge=0) | None
    iva_cost: condecimal(decimal_places=6, ge=0) | None

    total_commission: condecimal(decimal_places=6, ge=0) | None
    theoretical_commission: condecimal(decimal_places=6, ge=0) | None
    other_costs_commission: condecimal(decimal_places=6, ge=0) | None

    saving_relative: condecimal(decimal_places=6) | None
    saving_absolute: condecimal(decimal_places=6) | None

    class Config:
        orm_mode = True


class SuggestedRateFilter(Filter):
    marketer_name__unaccent: str | None
    rate_name__unaccent: str | None
    has_contractual_commitment: bool | None
    is_full_renewable: bool | None
    has_net_metering: bool | None

    order_by: List[str] = ["-id"]

    class Constants(Filter.Constants):
        model = SuggestedRate


class RelatedSuggestedRateFilter(Filter):
    marketer_name__unaccent: str | None
    rate_name__unaccent: str | None

    order_by: List[str] = ["-id"]

    class Constants(Filter.Constants):
        model = SuggestedRate


class SavingStudyFilter(Filter):
    id: int | None
    id__in: list[int] | None
    cups: str | None
    status: SavingStudyStatusEnum | None
    create_at__gte: datetime | None
    create_at__lt: datetime | None
    client_type: ClientType | None
    client_name__unaccent: str | None
    client_nif: str | None
    current_marketer__unaccent: str | None
    energy_price_1: Decimal | None
    energy_price_1__gte: Decimal | None
    energy_price_1__lte: Decimal | None
    is_deleted: bool | None
    user_creator: RelatedUserFilter | None = FilterDepends(
        with_prefix("user_creator", RelatedUserFilter), use_cache=False
    )
    current_rate_type: RelatedRateTypeFilter | None = FilterDepends(
        with_prefix("rate_type", RelatedRateTypeFilter), use_cache=False
    )
    suggested_rates: RelatedSuggestedRateFilter = FilterDepends(
        with_prefix("suggested_rates", RelatedSuggestedRateFilter), use_cache=False
    )
    order_by: List[str] = ["-id"]

    class Constants(Filter.Constants):
        model = SavingStudy


class SavingStudyFinishRequest(BaseModel):
    suggested_rate_id: int


class SuggestedRatePartialResponse(BaseModel):
    id: int
    rate_name: str

    class Config:
        orm_mode = True


class SavingStudyFinishOutput(BaseModel):
    id: int | None
    create_at: datetime
    status: SavingStudyStatusEnum
    cups: constr(min_length=20, max_length=22)
    client_type: ClientType
    client_name: constr(max_length=124) | None
    client_nif: constr(max_length=9) | None
    current_rate_type_id: int | None
    current_marketer: str | None
    fixed_price: condecimal(decimal_places=6, ge=0) | None
    other_cost_kwh: condecimal(decimal_places=6, ge=0) | None
    other_cost_percentage: condecimal(decimal_places=6, ge=0) | None
    other_cost_eur_month: condecimal(decimal_places=6, ge=0) | None
    selected_suggested_rate: SuggestedRateResponse | None
    user_creator: BaseUserResponsible

    @classmethod
    def from_orm(cls, saving_study: SavingStudy) -> "SavingStudyFinishOutput":
        selected_rate = saving_study.selected_suggested_rate

        return cls(
            **saving_study.__dict__,
            selected_suggested_rate=selected_rate if selected_rate else None,
            user_creator=saving_study.user_creator,
        )

    class Config:
        orm_mode = True


class SavingStudyOutput(BaseSavingStudy):
    id: int | None
    create_at: datetime | None
    status: SavingStudyStatusEnum | None
    current_rate_type: RateTypeBasicResponse | None
    user_creator: BaseUserResponsible | None
    selected_suggested_rate: SuggestedRateResponse | None

    @classmethod
    def from_orm(cls, saving_study: SavingStudy) -> "SavingStudyOutput":
        selected_rate = saving_study.selected_suggested_rate

        return cls(
            **saving_study.__dict__,
            current_rate_type=saving_study.current_rate_type,
            selected_suggested_rate=selected_rate if selected_rate else None,
            user_creator=saving_study.user_creator,
        )


class SuggestedRateCosts(BaseModel):
    final_cost: condecimal(ge=0) | None
    total_cost: condecimal(ge=0) | None
    energy_cost: condecimal(ge=0) | None
    power_cost: condecimal(ge=0) | None
    fixed_cost: condecimal(ge=0) | None
    other_costs: condecimal(ge=0) | None
    ie_cost: condecimal(ge=0) | None
    ih_cost: condecimal(ge=0) | None
    iva_cost: condecimal(ge=0) | None


class CostCalculatorInfo(BaseModel):
    id: int | None
    name: str | None
    energy_price_1: condecimal(decimal_places=6, ge=0) | None
    energy_price_2: condecimal(decimal_places=6, ge=0) | None
    energy_price_3: condecimal(decimal_places=6, ge=0) | None
    energy_price_4: condecimal(decimal_places=6, ge=0) | None
    energy_price_5: condecimal(decimal_places=6, ge=0) | None
    energy_price_6: condecimal(decimal_places=6, ge=0) | None
    consumption_p1: condecimal(decimal_places=2, ge=0) | None
    consumption_p2: condecimal(decimal_places=2, ge=0) | None
    consumption_p3: condecimal(decimal_places=2, ge=0) | None
    consumption_p4: condecimal(decimal_places=2, ge=0) | None
    consumption_p5: condecimal(decimal_places=2, ge=0) | None
    consumption_p6: condecimal(decimal_places=2, ge=0) | None
    power_1: condecimal(decimal_places=2, ge=0) | None
    power_2: condecimal(decimal_places=2, ge=0) | None
    power_3: condecimal(decimal_places=2, ge=0) | None
    power_4: condecimal(decimal_places=2, ge=0) | None
    power_5: condecimal(decimal_places=2, ge=0) | None
    power_6: condecimal(decimal_places=2, ge=0) | None
    power_price_1: condecimal(decimal_places=6, ge=0) | None
    power_price_2: condecimal(decimal_places=6, ge=0) | None
    power_price_3: condecimal(decimal_places=6, ge=0) | None
    power_price_4: condecimal(decimal_places=6, ge=0) | None
    power_price_5: condecimal(decimal_places=6, ge=0) | None
    power_price_6: condecimal(decimal_places=6, ge=0) | None
    price_type: PriceType = PriceType.fixed_fixed
    fixed_term_price: condecimal(decimal_places=6, ge=0) | None

    class Config:
        orm_mode = True


saving_study_export_headers = {
    "id": _("Id"),
    "cups": _("Cups"),
    "client_type": _("Client type"),
    "client_name": _("Client name"),
    "client_nif": _("Client NIF"),
    "current_rate_type.id": _("Rate type ID"),
    "current_rate_type.name": _("Rate type name"),
    "current_rate_type.energy_type": _("Energy type"),
    "current_marketer": _("Current marketer"),
    "selected_suggested_rate.id": _("Suggested rate ID"),
    "selected_suggested_rate.name": _("Suggested rate name"),
    "selected_suggested_rate.final_cost": _("Suggested rate final cost"),
    "selected_suggested_rate.theoretical_commission": _(
        "Suggested rate theoretical commission"
    ),
    "selected_suggested_rate.saving_relative": _("Suggested rate saving relative"),
    "selected_suggested_rate.saving_absolute": _("Suggested rate saving absolute"),
    "create_at": _("Date"),
    "user_creator.id": _("User creator ID"),
    "user_creator.first_name": _("User creator first name"),
    "user_creator.last_name": _("User creator last name"),
    "status": _("Status"),
}
