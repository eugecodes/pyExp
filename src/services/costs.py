from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import false, label

from src.infrastructure.sqlalchemy.common import update_obj_db
from src.infrastructure.sqlalchemy.costs import (
    create_energy_cost_db,
    create_other_cost_db,
    get_energy_cost_by,
    get_energy_costs_queryset,
    get_other_cost_by,
    get_other_cost_queryset,
)
from src.modules.costs.models import EnergyCost, OtherCost
from src.modules.costs.schemas import (
    CostDeleteRequest,
    EnergyCostAmountRangeResponse,
    EnergyCostCreateRequest,
    EnergyCostFilter,
    EnergyCostUpdatePartialRequest,
    OtherCostCreateUpdateRequest,
    OtherCostFilter,
    OtherCostPartialUpdateRequest,
)
from src.modules.rates.models import EnergyType
from src.modules.users.models import User
from src.services.common import update_from_dict
from src.services.rates import get_validated_rates


def energy_cost_create(
    db: Session, energy_cost_data: EnergyCostCreateRequest, current_user: User
) -> EnergyCost:
    energy_cost = EnergyCost(**energy_cost_data.dict())
    energy_cost.user_id = current_user.id
    try:
        energy_cost = create_energy_cost_db(db, energy_cost)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="value_error.already_exists"
        )
    return energy_cost


def list_energy_costs(db: Session, energy_cost_filter: EnergyCostFilter):
    return energy_cost_filter.sort(
        energy_cost_filter.filter(
            get_energy_costs_queryset(db, None, EnergyCost.is_deleted == false())
        )
    )


def get_energy_cost(db: Session, energy_cost_id: int) -> EnergyCost:
    energy_cost = get_energy_cost_by(
        db,
        EnergyCost.id == energy_cost_id,
        EnergyCost.is_deleted == false(),
    )

    if not energy_cost:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="energy_cost_not_exist"
        )

    return energy_cost


def energy_cost_partial_update(
    db: Session,
    energy_cost_id: int,
    energy_cost_data: EnergyCostUpdatePartialRequest,
    current_user: User,
) -> User:
    energy_cost = get_energy_cost(db, energy_cost_id)
    energy_cost_data_request = energy_cost_data.dict(exclude_unset=True)

    if (
        not current_user.is_superadmin
        and energy_cost.is_protected
        and (
            energy_cost_data_request.get("is_deleted")
            or energy_cost_data_request.get("concept")
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="modify_energy_cost_not_allowed",
        )

    update_from_dict(energy_cost, energy_cost_data_request)
    try:
        energy_cost = update_obj_db(db, energy_cost)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="value_error.already_exists"
        )
    return energy_cost


def get_energy_cost_amount_range(db: Session) -> EnergyCostAmountRangeResponse:
    return (
        db.query(
            label("minimum_amount", func.min(EnergyCost.amount)),
            label("maximum_amount", func.max(EnergyCost.amount)),
        )
        .filter(EnergyCost.is_deleted == false())
        .first()
        ._mapping
    )


def delete_energy_costs(
    db: Session, energy_costs_data: CostDeleteRequest, current_user: User
):
    if current_user.is_superadmin:
        db.query(EnergyCost).filter(EnergyCost.id.in_(energy_costs_data.ids)).update(
            {"is_deleted": True}
        )
        db.commit()
        return
    db.query(EnergyCost).filter(
        EnergyCost.id.in_(energy_costs_data.ids), EnergyCost.is_protected == false()
    ).update({"is_deleted": True})
    db.commit()


def other_cost_validate_power_range(
    min_power: float, max_power: float, energy_type: str
):
    if energy_type == EnergyType.electricity and (
        min_power is None or max_power is None or max_power < min_power
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.power_range.invalid",
        )
    if energy_type == EnergyType.gas and (
        min_power is not None or max_power is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.rate.invalid",
        )


def other_cost_create(
    db: Session, other_cost_data: OtherCostCreateUpdateRequest
) -> OtherCost:
    other_cost_dict = other_cost_data.dict()
    validated_rates = get_validated_rates(db, other_cost_dict.pop("rates"))
    other_cost_validate_power_range(
        other_cost_dict.get("min_power"),
        other_cost_dict.get("max_power"),
        validated_rates[0].rate_type.energy_type,
    )
    other_cost_dict["rates"] = validated_rates
    other_cost = OtherCost(**other_cost_dict)
    return create_other_cost_db(db, other_cost)


def get_other_cost(db: Session, other_cost_id: int) -> OtherCost:
    other_cost = get_other_cost_by(
        db,
        OtherCost.id == other_cost_id,
        OtherCost.is_deleted == false(),
    )

    if not other_cost:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="other_cost_not_exist"
        )

    return other_cost


def other_cost_update(
    db: Session,
    other_cost_id: int,
    other_cost_data: OtherCostCreateUpdateRequest,
) -> OtherCost:
    other_cost = get_other_cost(db, other_cost_id)
    other_cost_dict = other_cost_data.dict()
    validated_rates = get_validated_rates(db, other_cost_dict.get("rates"))
    if (
        other_cost.marketer_id != validated_rates[0].marketer_id
        or other_cost.energy_type != validated_rates[0].rate_type.energy_type
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.rate.invalid",
        )
    other_cost_validate_power_range(
        other_cost_dict.get("min_power"),
        other_cost_dict.get("max_power"),
        validated_rates[0].rate_type.energy_type,
    )
    other_cost_dict["rates"] = validated_rates
    update_from_dict(other_cost, other_cost_dict)
    other_cost = update_obj_db(db, other_cost)
    return other_cost


def list_other_costs(db: Session, other_cost_filter: OtherCostFilter):
    return other_cost_filter.sort(
        other_cost_filter.filter(
            get_other_cost_queryset(db, None, OtherCost.is_deleted == false())
        )
    )


def other_cost_partial_update(
    db: Session,
    other_cost_id: int,
    other_cost_data: OtherCostPartialUpdateRequest,
) -> OtherCost:
    other_cost = update_obj_db(
        db,
        update_from_dict(
            get_other_cost(db, other_cost_id), other_cost_data.dict(exclude_unset=True)
        ),
    )
    return other_cost


def delete_other_costs(db: Session, other_costs_data: CostDeleteRequest):
    db.query(OtherCost).filter(OtherCost.id.in_(other_costs_data.ids)).update(
        {"is_deleted": True}
    )
    db.commit()
