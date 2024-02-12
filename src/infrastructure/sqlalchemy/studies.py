from typing import List

from sqlalchemy import and_, false, func, or_, true
from sqlalchemy.orm import Query, Session

from src.modules.costs.models import OtherCost
from src.modules.marketers.models import Marketer
from src.modules.rates.models import EnergyType, PriceType, Rate, RateType
from src.modules.saving_studies.models import (
    SavingStudy,
    SavingStudyStatusEnum,
    SuggestedRate,
)


def create_saving_study_db(db: Session, saving_study: SavingStudy) -> SavingStudy:
    db.add(saving_study)
    db.commit()
    db.refresh(saving_study)
    return saving_study


def get_candidate_rates(
    db: Session,
    saving_study_id: int,
) -> Query:
    saving_study = (
        db.query(SavingStudy).filter(SavingStudy.id == saving_study_id).first()
    )

    power_min_required = saving_study.power_6 or saving_study.power_2 or 0
    query = db.query(Rate).filter(
        Rate.is_deleted == false(),
        Rate.is_active == true(),
        Rate.rate_type.has(RateType.is_deleted == false()),
        Rate.rate_type.has(RateType.enable == true()),
        Rate.rate_type_id == saving_study.current_rate_type_id,
        Rate.marketer.has(Marketer.is_deleted == false()),
        Rate.marketer.has(Marketer.is_active == true()),
        Rate.client_types.any(saving_study.client_type),
        or_(
            and_(
                Rate.rate_type.has(RateType.energy_type == EnergyType.electricity),
                Rate.price_type == PriceType.fixed_fixed,
                func.coalesce(Rate.min_power, 0) <= power_min_required,
                func.coalesce(Rate.max_power, 99_999_999) >= power_min_required,
            ),
            and_(
                Rate.rate_type.has(RateType.energy_type == EnergyType.electricity),
                Rate.price_type == PriceType.fixed_base,
            ),
            and_(
                Rate.rate_type.has(RateType.energy_type == EnergyType.gas),
                Rate.min_consumption <= saving_study.annual_consumption,
                Rate.max_consumption >= saving_study.annual_consumption,
            ),
        ),
    )
    return query


def get_saving_studies_queryset(db: Session, join_list: List = None, *filters):
    queryset = db.query(SavingStudy).filter(*filters)
    if join_list:
        queryset = queryset.join(*join_list)
    return queryset


def get_saving_study_by(db: Session, *filters) -> SavingStudy | None:
    return db.query(SavingStudy).filter(*filters).first()


def delete_study_suggested_rates(db: Session, study_id: int) -> None:
    db.query(SuggestedRate).filter(
        SuggestedRate.saving_study_id == study_id,
    ).delete()
    db.commit()


def delete_study_suggested_rates_not_selected(
    db: Session, study_id: int, suggested_rate_id: int
) -> None:
    db.query(SuggestedRate).filter(
        SuggestedRate.saving_study_id == study_id, SuggestedRate.id != suggested_rate_id
    ).delete()
    db.commit()


def get_suggested_rate_by(db: Session, *filters) -> SuggestedRate | None:
    return db.query(SuggestedRate).filter(*filters).first()


def get_suggested_rates_queryset(db: Session, join_list: List = None, *filters):
    queryset = db.query(SuggestedRate).filter(*filters)
    if join_list:
        queryset = queryset.join(*join_list)
    return queryset


def get_other_costs_rate_study(db: Session, study: SavingStudy, rate_id=int) -> Query:
    """
    Filter by
    - OtherCost is bind to rate
    - OtherCost is not deleted
    - OtherCost is active
    - OtherCost is mandatory
    - OtherCost has the client type of the study
    - OtherCost's power range include the study's power
    """
    min_power_required = study.power_6 or study.power_2 or 0
    return db.query(OtherCost).filter(
        OtherCost.rates.any(Rate.id == rate_id),
        OtherCost.is_deleted == false(),
        OtherCost.is_active == true(),
        OtherCost.mandatory == true(),
        OtherCost.client_types.any(study.client_type),
        OtherCost.min_power <= min_power_required,
        OtherCost.max_power >= min_power_required,
    )


def finish_study_db(
    db: Session, saving_study: SavingStudy, suggested_rate: SuggestedRate
) -> (SavingStudy, SuggestedRate):
    saving_study.status = SavingStudyStatusEnum.COMPLETED
    db.add(saving_study)
    delete_study_suggested_rates_not_selected(db, saving_study.id, suggested_rate.id)
    suggested_rate.is_selected = True
    db.add(suggested_rate)
    db.commit()
    db.refresh(saving_study)
    db.refresh(suggested_rate)
    return saving_study, suggested_rate
