from decimal import Decimal

from sqlalchemy.orm import Session

from src.modules.saving_studies.models import (
    SavingStudy,
    SavingStudyStatusEnum,
    SuggestedRate,
)
from src.modules.saving_studies.schemas import SavingStudyFinishOutput
from src.modules.users.models import User


class TestSavingStudyFinishOutput:
    def test_from_orm(
        self,
        db_session: Session,
        saving_study: SavingStudy,
        suggested_rate: SuggestedRate,
        user_create: User,
    ):
        suggested_rate.is_selected = True
        saving_study.status = SavingStudyStatusEnum.COMPLETED
        study_output = SavingStudyFinishOutput.from_orm(saving_study)

        assert study_output.id == 1
        assert study_output.status == SavingStudyStatusEnum.COMPLETED
        assert study_output.cups == "ES0021000000000000AA"
        assert study_output.client_type == "particular"
        assert study_output.client_name == "Client name"
        assert study_output.client_nif == "12345678A"
        assert study_output.current_rate_type_id == 1
        assert study_output.current_marketer is None
        assert study_output.other_cost_kwh is None
        assert study_output.other_cost_eur_month is None
        assert study_output.other_cost_percentage is None
        assert study_output.fixed_price is None

        assert study_output.selected_suggested_rate.id == 1
        assert study_output.selected_suggested_rate.rate_name == "Rate name"
        assert study_output.selected_suggested_rate.has_contractual_commitment is True
        assert study_output.selected_suggested_rate.duration == 12
        assert study_output.selected_suggested_rate.is_full_renewable is True
        assert study_output.selected_suggested_rate.has_net_metering is True
        assert study_output.selected_suggested_rate.net_metering_value == Decimal(
            "12.3"
        )
        assert study_output.selected_suggested_rate.applied_profit_margin == Decimal(
            "12.3"
        )
        assert study_output.selected_suggested_rate.final_cost is None
        assert study_output.selected_suggested_rate.theoretical_commission is None
        assert study_output.selected_suggested_rate.saving_absolute is None
        assert study_output.selected_suggested_rate.saving_relative is None

        assert study_output.user_creator.id == 1
        assert study_output.user_creator.first_name == "John"
        assert study_output.user_creator.last_name == "Graham"

    def test_from_orm_no_selected_rate(
        self, db_session: Session, saving_study: SavingStudy, user_create: User
    ):
        study_output = SavingStudyFinishOutput.from_orm(saving_study)

        assert study_output.id == saving_study.id
        assert study_output.status == saving_study.status
        assert study_output.cups == saving_study.cups
        assert study_output.client_type == saving_study.client_type
        assert study_output.client_name == saving_study.client_name
        assert study_output.client_nif == saving_study.client_nif
        assert study_output.current_rate_type_id == saving_study.current_rate_type_id
        assert study_output.current_marketer == saving_study.current_marketer
        assert study_output.other_cost_eur_month is None
        assert study_output.other_cost_percentage is None
        assert study_output.fixed_price is None
        assert study_output.fixed_price == saving_study.fixed_price

        assert study_output.selected_suggested_rate is None

        assert study_output.user_creator.id == user_create.id
        assert study_output.user_creator.first_name == user_create.first_name
        assert study_output.user_creator.last_name == user_create.last_name
