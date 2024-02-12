from dataclasses import dataclass, field

from fastapi import HTTPException, status
from sqlalchemy import false
from sqlalchemy.orm import Query, Session

from src.infrastructure.sqlalchemy.commissions import (
    create_commission_db,
    get_commission_by,
    get_commission_queryset,
)
from src.infrastructure.sqlalchemy.common import is_overlapping, update_obj_db
from src.modules.commissions.models import Commission, RangeType
from src.modules.commissions.schemas import (
    CommissionCreateRequest,
    CommissionDeleteRequest,
    CommissionFilter,
    CommissionPartialUpdateRequest,
    CommissionUpdateRequest,
)
from src.modules.marketers.models import Marketer
from src.modules.rates.models import PriceType, Rate
from src.services.common import update_from_dict
from src.services.rates import get_validated_rates


@dataclass
class RateInfo:
    rates_price_type: PriceType
    marketer_id: int
    rate_ids: list[int] = field(default_factory=list)
    rates_rate_type_id: int | None = None


def validate_commission_fields_by_rates(
    commission_data: CommissionCreateRequest, price_type: PriceType, rate_type_id: int
) -> None:
    if (
        price_type == PriceType.fixed_base
        and (
            commission_data.percentage_Test_commission is None
            or commission_data.rate_type_segmentation is not None
            or commission_data.range_type is not None
            or commission_data.Test_commission is not None
        )
    ) or (
        price_type == PriceType.fixed_fixed
        and (
            commission_data.percentage_Test_commission is not None
            or commission_data.rate_type_segmentation is None
            or commission_data.range_type is None
            or commission_data.Test_commission is None
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.rate.invalid_price_type",
        )

    if (
        commission_data.rate_type_segmentation
        and commission_data.rate_type_id != rate_type_id
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.rate.invalid_rate_type",
        )


def validate_commission_consumption(
    db: Session, commission_data: CommissionCreateRequest, rate_info: RateInfo
) -> None:
    if (
        commission_data.min_consumption is None
        or commission_data.max_consumption is None
        or commission_data.min_power is not None
        or commission_data.max_power is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.range_type.invalid",
        )
    if commission_data.min_consumption > commission_data.max_consumption:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.consumption_range.invalid",
        )

    query = db.query(Commission).filter(
        Commission.is_deleted == false(),
        Commission.rates.any(Marketer.id == rate_info.marketer_id),
        Commission.rates.any(Rate.id.in_(rate_info.rate_ids)),
        Commission.rates.any(Rate.price_type == rate_info.rates_price_type),
    )
    if rate_info.rates_rate_type_id:
        query.filter(
            Commission.rates.any(Rate.rate_type_id == rate_info.rates_rate_type_id)
        )

    if rate_info.rates_price_type == PriceType.fixed_fixed and is_overlapping(
        query,
        commission_data.min_consumption,
        commission_data.max_consumption,
        Commission.min_consumption,
        Commission.max_consumption,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.consumption_range.overlap",
        )


def validate_commission_power(
    db: Session, commission_data: CommissionCreateRequest, rate_info: RateInfo
) -> None:
    if (
        commission_data.min_consumption is not None
        or commission_data.max_consumption is not None
        or commission_data.min_power is None
        or commission_data.max_power is None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.range_type.invalid",
        )
    if commission_data.min_power > commission_data.max_power:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.power_range.invalid_range",
        )

    query = db.query(Commission).filter(
        Commission.is_deleted == false(),
        Commission.rates.any(Marketer.id == rate_info.marketer_id),
        Commission.rates.any(Rate.id.in_(rate_info.rate_ids)),
        Commission.rates.any(Rate.price_type == rate_info.rates_price_type),
    )
    if rate_info.rates_rate_type_id:
        query.filter(
            Commission.rates.any(Rate.rate_type_id == rate_info.rates_rate_type_id)
        )

    if rate_info.rates_price_type == PriceType.fixed_fixed and is_overlapping(
        query,
        commission_data.min_power,
        commission_data.max_power,
        Commission.min_power,
        Commission.max_power,
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.power_range.overlap",
        )


def validate_commission_range_type(
    db: Session,
    commission_data: CommissionCreateRequest,
    range_type: RangeType,
    rate_info: RateInfo,
) -> None:
    if range_type == RangeType.consumption:
        validate_commission_consumption(
            db,
            commission_data,
            rate_info,
        )
    if range_type == RangeType.power:
        validate_commission_power(
            db,
            commission_data,
            rate_info,
        )


def validate_duplicated_commissions_fixed_base(
    validated_rates: list[Rate],
    id_commission_updated: int = None,
) -> None:
    """
    Checks if the rates are already related with some commission. If that is the case, we need to raise an exception

    :validated_rates: The list of rates to evaluate
    :param id_commission_updated: The id of the commission being updated
    """
    for rate in validated_rates:
        if rate.commissions:
            if id_commission_updated:
                check_same_commission_is_being_updated(
                    rate.commissions, id_commission_updated
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="value_error.already_exists",
                )


def check_same_commission_is_being_updated(
    commissions: list[Commission], id_commission_updated: int
) -> None:
    """
    Checks if the rate is already related with the commission that it is being updated.
    If that is not the case, then we need to raise an expcetion because a fixed base rate cannot be
    related with more than one commission
    """
    for commission in commissions:
        if not commission.id == id_commission_updated:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="value_error.already_exists",
            )


def commission_create(
    db: Session, commission_data: CommissionCreateRequest
) -> Commission:
    commission_dict = commission_data.dict()
    rate_ids = list(commission_dict.pop("rates"))
    validated_rates = get_validated_rates(
        db,
        rate_ids,
        same_price_and_rate_type=True,
        rate_type_segmentation=commission_dict.get("rate_type_segmentation"),
    )

    validate_commission_fields_by_rates(
        commission_data, validated_rates[0].price_type, validated_rates[0].rate_type_id
    )
    rate_info = RateInfo(
        validated_rates[0].price_type,
        validated_rates[0].marketer_id,
        rate_ids,
        validated_rates[0].rate_type_id
        if commission_data.rate_type_segmentation
        else None,
    )
    validate_commission_range_type(
        db, commission_data, commission_data.range_type, rate_info
    )
    if validated_rates[0].price_type == PriceType.fixed_base:
        validate_duplicated_commissions_fixed_base(validated_rates)

    commission_dict["rates"] = validated_rates
    commission = Commission(**commission_dict)
    return create_commission_db(db, commission)


def get_commission(db: Session, commission_id: int) -> Commission:
    commission = get_commission_by(
        db,
        Commission.id == commission_id,
        Commission.is_deleted == false(),
    )

    if not commission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="commission_not_exist"
        )

    return commission


def commission_update(
    db: Session,
    commission_id: int,
    commission_data: CommissionUpdateRequest,
) -> Commission:
    commission = get_commission(db, commission_id)
    commission_dict = commission_data.dict()
    rate_ids = list(commission_dict.get("rates"))
    validated_rates = get_validated_rates(
        db,
        rate_ids,
        True,
        commission_dict.get("rate_type_segmentation"),
    )

    if (
        commission.marketer_id != validated_rates[0].marketer_id
        or commission.price_type != validated_rates[0].price_type
        or (
            commission.rate_type_segmentation
            and (
                commission.rate_type_id != validated_rates[0].rate_type_id
                or commission.rate_type__energy_type
                != validated_rates[0].rate_type.energy_type
            )
        )
        or commission.rates__energy_type != validated_rates[0].rate_type.energy_type
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.rate.invalid",
        )

    if (
        commission.price_type == PriceType.fixed_base
        and (
            commission_data.percentage_Test_commission is None
            or commission_data.Test_commission is not None
        )
    ) or (
        commission.price_type == PriceType.fixed_fixed
        and (
            commission_data.percentage_Test_commission is not None
            or commission_data.Test_commission is None
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="value_error.rate.invalid_price_type",
        )

    rate_info = RateInfo(
        validated_rates[0].price_type,
        validated_rates[0].marketer_id,
        rate_ids,
        validated_rates[0].rate_type_id,
    )
    validate_commission_range_type(
        db,
        commission_data,
        commission.range_type,
        rate_info,
    )

    if validated_rates[0].price_type == PriceType.fixed_base:
        validate_duplicated_commissions_fixed_base(validated_rates, commission.id)

    commission_dict["rates"] = validated_rates
    update_from_dict(commission, commission_dict)
    commission = update_obj_db(db, commission)
    return commission


def commission_partial_update(
    db: Session,
    commission_id: int,
    commission_data: CommissionPartialUpdateRequest,
) -> Commission:
    commission = update_obj_db(
        db,
        update_from_dict(
            get_commission(db, commission_id), commission_data.dict(exclude_unset=True)
        ),
    )
    return commission


def list_commissions(db: Session, commission_filter: CommissionFilter) -> Query:
    return commission_filter.sort(
        commission_filter.filter(
            get_commission_queryset(db, None, Commission.is_deleted == false())
        )
    )


def delete_commissions(db: Session, commissions_data: CommissionDeleteRequest) -> None:
    db.query(Commission).filter(Commission.id.in_(commissions_data.ids)).update(
        {"is_deleted": True}
    )
    db.commit()
