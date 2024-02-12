from typing import Type

from fastapi import HTTPException, status
from sqlalchemy import Table, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql.expression import false, label

from src.infrastructure.sqlalchemy.common import update_obj_db
from src.infrastructure.sqlalchemy.database import Base
from src.infrastructure.sqlalchemy.rates import (
    create_rate_db,
    create_rate_type_db,
    get_rate_by,
    get_rate_queryset,
    get_rate_type_by,
    get_rate_types_queryset,
)
from src.modules.commissions.models import Commission, commissions_rates_association
from src.modules.costs.models import OtherCost, other_cost_rates_association
from src.modules.margins.models import Margin
from src.modules.rates.models import (
    EnergyType,
    HistoricalRate,
    PriceType,
    Rate,
    RateType,
)
from src.modules.rates.schemas import (
    RateCreateRequest,
    RateDeleteRequest,
    RateFilter,
    RatePartialUpdateRequest,
    RateTypeCreateRequest,
    RateTypeFilter,
    RateTypeUpdatePartialRequest,
    RateUpdateRequest,
)
from src.modules.users.models import User
from src.services.common import update_from_dict
from src.services.marketers import get_marketer

MIN_PRICES = 1
MAX_PRICES = 7
ENERGY_PRICE_FIELD_NAME = "energy_price"
POWER_PRICE_FIELD_NAME = "power_price"


def rate_type_create(
    db: Session, rate_type_data: RateTypeCreateRequest, current_user: User
) -> RateType:
    rate_type = RateType(**rate_type_data.dict())
    rate_type.user_id = current_user.id
    try:
        rate_type = create_rate_type_db(db, rate_type)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="value_error.already_exists"
        )
    return rate_type


def list_rate_types(db: Session, rate_types_filter: RateTypeFilter):
    return rate_types_filter.sort(
        rate_types_filter.filter(
            get_rate_types_queryset(db, [RateType.user], RateType.is_deleted == false())
        )
    )


def get_rate_type(db: Session, rate_type_id: int) -> RateType:
    rate_type = get_rate_type_by(
        db, RateType.id == rate_type_id, RateType.is_deleted == false()
    )

    if not rate_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="rate_type_not_exist"
        )

    return rate_type


def rate_type_partial_update(
    db: Session,
    rate_type_id: int,
    rate_type_data: RateTypeUpdatePartialRequest,
) -> User:
    rate_type = get_rate_type(db, rate_type_id)

    if rate_type.energy_type == EnergyType.gas and (
        rate_type_data.min_power is not None or rate_type_data.max_power is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.energy_type.invalid",
        )
    rate_type_data_request = rate_type_data.dict(exclude_unset=True)
    if rate_type.energy_type == EnergyType.electricity:
        min_power = rate_type_data_request.get("min_power", rate_type.min_power)
        max_power = rate_type_data_request.get("max_power", rate_type.max_power)
        if (min_power is not None and max_power is None) or (
            min_power is None and max_power is not None
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="value_error.power_range.missing",
            )
        if min_power is not None and max_power is not None and min_power > max_power:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="value_error.power_range.invalid_range",
            )
    update_from_dict(rate_type, rate_type_data_request)
    rate_type = update_obj_db(db, rate_type)
    return rate_type


def get_rate_type_power_ranges(db: Session):
    return (
        db.query(
            label("minimum_min_power", func.min(RateType.min_power)),
            label("maximum_min_power", func.max(RateType.min_power)),
            label("minimum_max_power", func.min(RateType.max_power)),
            label("maximum_max_power", func.max(RateType.max_power)),
        )
        .filter(RateType.is_deleted == false())
        .first()
        ._mapping
    )


def delete_rate_types(db: Session, rate_types_data: RateDeleteRequest):
    db.query(RateType).filter(RateType.id.in_(rate_types_data.ids)).update(
        {"is_deleted": True}
    )
    db.query(Rate).filter(Rate.rate_type_id.in_(rate_types_data.ids)).update(
        {"is_active": False}
    )
    db.commit()


def validate_rate(energy_type: str, price_type: PriceType, values: dict):
    if not values.get("compensation_surplus"):
        values["compensation_surplus_value"] = None

    min_power = values.get("min_power")
    max_power = values.get("max_power")

    if not (min_power is None and max_power is None):
        if energy_type != EnergyType.electricity or price_type != PriceType.fixed_fixed:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="value_error.power_range.invalid_rate_combination",
            )
        if min_power is None or max_power is None or min_power > max_power:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="value_error.power_range.invalid_range",
            )

    is_full_renewable = values.get("is_full_renewable")

    if energy_type == EnergyType.gas:
        min_consumption = values.get("min_consumption")
        max_consumption = values.get("max_consumption")

        if (
            (min_consumption is None and max_consumption is not None)
            or (min_consumption is not None and max_consumption is None)
            or (
                min_consumption is not None
                and max_consumption is not None
                and min_consumption > max_consumption
            )
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="value_error.consumption_range.invalid_consumption_range",
            )

        # if is_full_renewable is not None or compensation_surplus is not None:
        #     raise HTTPException(
        #         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        #         detail="value_error.energy_type.invalid_field",
        #     )

    if energy_type == EnergyType.electricity and is_full_renewable is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.is_full_renewable.required",
        )
    return values


def validate_rate_create(energy_type: str, values: dict):
    if energy_type == EnergyType.gas:
        energy_field_names = [
            f"{ENERGY_PRICE_FIELD_NAME}_{price_number}"
            for price_number in range(MIN_PRICES + 1, MAX_PRICES)
        ]
        power_field_names = [
            f"{POWER_PRICE_FIELD_NAME}_{price_number}"
            for price_number in range(MIN_PRICES, MAX_PRICES)
        ]
        price_field_names = energy_field_names + power_field_names
        for price_field in price_field_names:
            if values.get(price_field) is not None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="value_error.energy_type.invalid_price",
                )


def rate_create(db: Session, rate_data: RateCreateRequest) -> Rate:
    rate_type = get_rate_type(db, rate_data.rate_type_id)
    get_marketer(db, rate_data.marketer_id)

    rate_data_dict = rate_data.dict()
    rate_data_dict = validate_rate(
        rate_type.energy_type, rate_data_dict.get("price_type"), rate_data_dict
    )
    validate_rate_create(rate_type.energy_type, rate_data_dict)

    rate = Rate(**rate_data_dict)
    try:
        rate = create_rate_db(db, rate)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="value_error.already_exists"
        )
    return rate


def get_rate(db: Session, rate_id: int) -> Rate:
    rate = get_rate_by(db, Rate.id == rate_id, Rate.is_deleted == false())

    if not rate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="rate_not_exist"
        )

    return rate


def get_validated_rates(
    db: Session,
    rates_ids: list,
    same_price_and_rate_type: bool = False,
    rate_type_segmentation: bool = True,
):
    rates_qs = get_rate_queryset(
        db, [RateType], Rate.id.in_(rates_ids), Rate.is_deleted == false()
    )
    rates = rates_qs.order_by(Rate.id).all()
    rates_count = len(rates)
    if rates_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="rate_not_exist"
        )
    rates_qs = rates_qs.filter(
        Rate.marketer_id == rates[0].marketer_id,
        RateType.energy_type == rates[0].rate_type.energy_type,
    )
    if same_price_and_rate_type:
        rates_qs = rates_qs.filter(
            Rate.price_type == rates[0].price_type,
        )
        if rate_type_segmentation:
            rates_qs = rates_qs.filter(
                Rate.rate_type_id == rates[0].rate_type_id,
            )

    if rates_count != len(rates_ids) or rates_count != rates_qs.count():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.rate.invalid",
        )
    return rates


def validate_rate_update_consumption_range(
    energy_type: EnergyType, rate_data: dict
) -> dict:
    min_consumption = rate_data.get("min_consumption")
    max_consumption = rate_data.get("max_consumption")

    if energy_type == EnergyType.electricity:
        rate_data.pop("min_consumption", None)
        rate_data.pop("max_consumption", None)
        rate_data.pop("fixed_term_price", None)
    if (
        energy_type == EnergyType.gas
        and (min_consumption is None and max_consumption is not None)
        or (min_consumption is not None and max_consumption is None)
        or (
            min_consumption is not None
            and max_consumption is not None
            and min_consumption > max_consumption
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.consumption_range.invalid_consumption_range",
        )

    return rate_data


def rate_update(
    db: Session,
    rate_id: int,
    rate_data: RateUpdateRequest,
) -> Rate:
    rate = get_rate(db, rate_id)
    rate_data_request = rate_data.dict(exclude_unset=True)
    rate_data_request = validate_rate(
        rate.rate_type.energy_type, rate.price_type, rate_data_request
    )
    rate_data_request = validate_rate_update_consumption_range(
        rate.rate_type.energy_type, rate_data_request
    )
    modifications_hist = []
    for key, value in rate_data_request.items():
        if getattr(rate, key) == value:
            continue
        if "_price" in key:
            if rate.rate_type.energy_type == EnergyType.gas and key not in (
                "fixed_term_price",
                "energy_price_1",
            ):
                continue
            if value:
                modifications_hist.append(
                    {"price_name": key, "price": value, "rate_id": rate.id}
                )
        setattr(rate, key, value)

    db.bulk_insert_mappings(HistoricalRate, modifications_hist)
    try:
        rate = update_obj_db(db, rate)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="value_error.already_exists"
        )
    return rate


def rate_partial_update(
    db: Session,
    rate_id: int,
    rate_data: RatePartialUpdateRequest,
) -> Rate:
    rate = update_obj_db(
        db, update_from_dict(get_rate(db, rate_id), rate_data.dict(exclude_unset=True))
    )
    return rate


def list_rate(db: Session, rate_filter: RateFilter):
    return rate_filter.sort(
        rate_filter.filter(get_rate_queryset(db, None, Rate.is_deleted == false()))
    )


def delete_rates(db: Session, rates_data: RateDeleteRequest):
    def delete_related_objects(
        model_class: Type[Base],
        objects_to_update: list[Type[Base]],
        relationship_table: Table,
    ) -> None:
        ids_to_update = [row.id for row in objects_to_update]

        if ids_to_update:
            db.query(model_class).filter(model_class.id.in_(ids_to_update)).update(
                {"is_deleted": True}
            )

        # Update the relationship between Rate and the other table
        db.execute(
            relationship_table.delete().where(
                relationship_table.c.rate_id.in_(rates_data.ids)
            )
        )

    db.query(Rate).filter(Rate.id.in_(rates_data.ids)).update({"is_deleted": True})
    db.query(Margin).filter(Margin.rate_id.in_(rates_data.ids)).update(
        {"is_deleted": True}
    )

    commissions_to_update = (
        db.query(Commission)
        .join(Rate.commissions)
        .filter(Rate.id.in_(rates_data.ids))
        .options(joinedload(Commission.rates))
        .group_by(Commission.id)
        .having(func.count(Rate.id) == 1)
        .all()
    )
    delete_related_objects(
        Commission, commissions_to_update, commissions_rates_association
    )

    other_costs_to_update = (
        db.query(OtherCost)
        .join(Rate.other_costs)
        .filter(Rate.id.in_(rates_data.ids))
        .options(joinedload(OtherCost.rates))
        .group_by(OtherCost.id)
        .having(func.count(Rate.id) == 1)
        .all()
    )
    delete_related_objects(
        OtherCost, other_costs_to_update, other_cost_rates_association
    )

    db.commit()
