from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import false
from sqlalchemy.orm import Session

from src.modules.commissions.models import Commission, RangeType
from src.modules.commissions.schemas import (
    CommissionCreateRequest,
    CommissionDeleteRequest,
    CommissionFilter,
    CommissionPartialUpdateRequest,
    CommissionUpdateRequest,
)
from src.modules.rates.models import Rate
from src.services.commissions import (
    RateInfo,
    check_same_commission_is_being_updated,
    commission_create,
    commission_partial_update,
    commission_update,
    delete_commissions,
    get_commission,
    list_commissions,
    validate_commission_consumption,
    validate_commission_fields_by_rates,
    validate_commission_power,
    validate_commission_range_type,
    validate_duplicated_commissions_fixed_base,
)


def test_validate_commission_fields_by_rates_fixed_base_invalid_price_type_error():
    with pytest.raises(HTTPException) as exc:
        validate_commission_fields_by_rates(
            CommissionCreateRequest(
                name="Commission name",
                Test_commission=5.6,
                rates=[2],
            ),
            "fixed_base",
            2,
        )

    assert exc.value.detail == "value_error.rate.invalid_price_type"


def test_validate_commission_fields_by_rates_fixed_fixed_invalid_price_type_error():
    with pytest.raises(HTTPException) as exc:
        validate_commission_fields_by_rates(
            CommissionCreateRequest(
                name="Commission name",
                rate_type_id=1,
                range_type=RangeType.consumption,
                min_consumption=3.5,
                max_consumption=11.5,
                Test_commission=5.6,
                rates=[1],
            ),
            "fixed_fixed",
            1,
        )

    assert exc.value.detail == "value_error.rate.invalid_price_type"


def test_validate_commission_fields_by_rates_fixed_fixed_rate_type_missing_error():
    with pytest.raises(HTTPException) as exc:
        validate_commission_fields_by_rates(
            CommissionCreateRequest(
                name="Commission name",
                rate_type_segmentation=True,
                range_type=RangeType.consumption,
                min_consumption=3.5,
                max_consumption=11.5,
                Test_commission=5.6,
                rates=[1],
            ),
            "fixed_fixed",
            1,
        )

    assert exc.value.detail == "value_error.rate.invalid_rate_type"


def test_validate_commission_fields_by_rates_fixed_fixed_invalid_rate_type_error():
    with pytest.raises(HTTPException) as exc:
        validate_commission_fields_by_rates(
            CommissionCreateRequest(
                name="Commission name",
                rate_type_segmentation=True,
                rate_type_id=2,
                range_type=RangeType.consumption,
                min_consumption=3.5,
                max_consumption=11.5,
                Test_commission=5.6,
                rates=[1],
            ),
            "fixed_fixed",
            1,
        )

    assert exc.value.detail == "value_error.rate.invalid_rate_type"


def test_validate_commission_range_type_ok(
    db_session: Session,
):
    rate_info = RateInfo(
        rates_price_type="fixed_fixed",
        marketer_id=1,
        rates_rate_type_id=1,
        rate_ids=[1],
    )
    assert (
        validate_commission_range_type(
            db_session,
            CommissionCreateRequest(
                name="Commission name",
                rate_type_segmentation=True,
                rate_type_id=1,
                range_type="consumption",
                min_consumption=5.5,
                max_consumption=11.5,
                Test_commission=5.6,
                rates=[1],
            ),
            range_type="consumption",
            rate_info=rate_info,
        )
        is None
    )


def test_validate_commission_consumption_fixed_fixed_min_consumption_missing_error(
    db_session: Session,
):
    rate_info = RateInfo(
        rates_price_type="fixed_fixed",
        marketer_id=1,
        rate_ids=[1],
        rates_rate_type_id=1,
    )
    with pytest.raises(HTTPException) as exc:
        validate_commission_consumption(
            db_session,
            CommissionCreateRequest(
                name="Commission name",
                rate_type_segmentation=True,
                rate_type_id=1,
                range_type=RangeType.consumption,
                max_consumption=11.5,
                Test_commission=5.6,
                rates=[1],
            ),
            rate_info=rate_info,
        )

    assert exc.value.detail == "value_error.range_type.invalid"


def test_validate_commission_consumption_fixed_fixed_range_type_invalid_error(
    db_session: Session,
):
    rate_info = RateInfo(
        rates_price_type="fixed_fixed",
        marketer_id=1,
        rate_ids=[1],
        rates_rate_type_id=1,
    )
    with pytest.raises(HTTPException) as exc:
        validate_commission_consumption(
            db_session,
            CommissionCreateRequest(
                name="Commission name",
                rate_type_segmentation=True,
                rate_type_id=1,
                range_type=RangeType.consumption,
                min_consumption=3.5,
                max_consumption=11.5,
                max_power=21.5,
                Test_commission=5.6,
                rates=[1],
            ),
            rate_info=rate_info,
        )

    assert exc.value.detail == "value_error.range_type.invalid"


def test_validate_commission_consumption_fixed_fixed_consumption_range_invalid_error(
    db_session: Session,
):
    rate_info = RateInfo(
        rates_price_type="fixed_fixed",
        marketer_id=1,
        rate_ids=[1],
        rates_rate_type_id=1,
    )
    with pytest.raises(HTTPException) as exc:
        validate_commission_consumption(
            db_session,
            CommissionCreateRequest(
                name="Commission name",
                rate_type_segmentation=True,
                rate_type_id=1,
                range_type=RangeType.consumption,
                min_consumption=13.5,
                max_consumption=11.5,
                Test_commission=5.6,
                rates=[1],
            ),
            rate_info=rate_info,
        )

    assert exc.value.detail == "value_error.consumption_range.invalid"


def test_validate_commission_power_fixed_fixed_power_range_missing_error(
    db_session: Session,
):
    rate_info = RateInfo(
        rates_price_type="fixed_fixed",
        marketer_id=1,
        rate_ids=[1],
        rates_rate_type_id=1,
    )
    with pytest.raises(HTTPException) as exc:
        validate_commission_power(
            db_session,
            CommissionCreateRequest(
                name="Commission name",
                rate_type_segmentation=True,
                rate_type_id=1,
                range_type=RangeType.power,
                min_consumption=11.5,
                max_consumption=13.5,
                Test_commission=5.6,
                rates=[1],
            ),
            rate_info=rate_info,
        )

    assert exc.value.detail == "value_error.range_type.invalid"


def test_validate_commission_power_fixed_fixed_consuption_range_invalid_error(
    db_session: Session,
):
    rate_info = RateInfo(
        rates_price_type="fixed_fixed",
        marketer_id=1,
        rate_ids=[1],
        rates_rate_type_id=1,
    )
    with pytest.raises(HTTPException) as exc:
        validate_commission_power(
            db_session,
            CommissionCreateRequest(
                name="Commission name",
                rate_type_segmentation=True,
                rate_type_id=1,
                range_type=RangeType.power,
                min_power=11.5,
                max_power=13.5,
                max_consumption=33.5,
                Test_commission=5.6,
                rates=[1],
            ),
            rate_info=rate_info,
        )

    assert exc.value.detail == "value_error.range_type.invalid"


def test_validate_commission_power_fixed_fixed_power_range_invalid_error(
    db_session: Session,
):
    rate_info = RateInfo(
        rates_price_type="fixed_fixed",
        marketer_id=1,
        rate_ids=[1],
        rates_rate_type_id=1,
    )
    with pytest.raises(HTTPException) as exc:
        validate_commission_power(
            db_session,
            CommissionCreateRequest(
                name="Commission name",
                rate_type_segmentation=True,
                rate_type_id=1,
                range_type=RangeType.power,
                min_power=21.5,
                max_power=13.5,
                Test_commission=5.6,
                rates=[1],
            ),
            rate_info=rate_info,
        )

    assert exc.value.detail == "value_error.power_range.invalid_range"


def test_validate_commission_consumption_fixed_fixed_consumption_range_overlap(
    db_session: Session, commission: Commission
):
    rate_info = RateInfo(
        rates_price_type="fixed_fixed",
        marketer_id=1,
        rate_ids=[1],
        rates_rate_type_id=1,
    )
    with pytest.raises(HTTPException) as exc:
        validate_commission_consumption(
            db_session,
            CommissionCreateRequest(
                name="Commission new name",
                rate_type_segmentation=True,
                rate_type_id=1,
                range_type=RangeType.consumption,
                min_consumption=7.5,
                max_consumption=15.5,
                Test_commission=5.6,
                rates=[1],
            ),
            rate_info=rate_info,
        )

    assert exc.value.detail == "value_error.consumption_range.overlap"


def test_validate_commission_power_fixed_fixed_power_range_overlap(
    db_session: Session, commission_power: Commission
):
    rate_info = RateInfo(
        rates_price_type="fixed_fixed",
        marketer_id=1,
        rate_ids=[1],
        rates_rate_type_id=1,
    )
    with pytest.raises(HTTPException) as exc:
        validate_commission_power(
            db_session,
            CommissionCreateRequest(
                name="Commission new name",
                rate_type_segmentation=True,
                rate_type_id=1,
                range_type=RangeType.power,
                min_power=7.5,
                max_power=15.5,
                Test_commission=5.6,
                rates=[1],
            ),
            rate_info=rate_info,
        )

    assert exc.value.detail == "value_error.power_range.overlap"


def test_validate_duplicated_commissions_fixed_base_ok(
    db_session: Session,
    commission: Commission,
    commission_power: Commission,
    gas_rate: Rate,
):
    assert validate_duplicated_commissions_fixed_base([gas_rate]) is None


def test_validate_duplicated_commissions_fixed_base_ok_update(
    db_session: Session,
    commission: Commission,
    commission_power: Commission,
    commission_fixed_base: Commission,
    gas_rate: Rate,
):
    assert (
        validate_duplicated_commissions_fixed_base(
            [gas_rate], id_commission_updated=commission_fixed_base.id
        )
        is None
    )


def test_check_same_commission_is_being_updated_ok(
    db_session: Session,
    commission: Commission,
    commission_power: Commission,
    commission_fixed_base: Commission,
    gas_rate: Rate,
):
    assert (
        check_same_commission_is_being_updated(gas_rate.commissions, gas_rate.id)
        is None
    )


def test_check_same_commission_is_being_updated_error(
    db_session: Session,
    commission_fixed_base: Commission,
    electricity_rate: Rate,
    gas_rate: Rate,
):
    with pytest.raises(HTTPException) as exc:
        check_same_commission_is_being_updated(
            gas_rate.commissions, electricity_rate.id
        )

    assert exc.value.detail == "value_error.already_exists"


def test_validate_duplicated_commissions_fixed_base_error(
    db_session: Session, commission_fixed_base: Commission, gas_rate: Rate
):
    with pytest.raises(HTTPException) as exc:
        validate_duplicated_commissions_fixed_base([gas_rate])

    assert exc.value.detail == "value_error.already_exists"


def test_commission_create_fixed_base_ok(db_session: Session, gas_rate: Rate):
    commission_create(
        db_session,
        CommissionCreateRequest(
            name="Commission name",
            percentage_Test_commission=12,
            rate_type_id=2,
            rates=[2],
        ),
    )

    assert db_session.query(Commission).count() == 1


def test_commission_create_fixed_fixed_no_rate_type_power_ok(
    db_session: Session, electricity_rate: Rate
):
    commission_create(
        db_session,
        CommissionCreateRequest(
            name="Commission name",
            rate_type_segmentation=False,
            range_type=RangeType.power,
            min_power=3.5,
            max_power=11.5,
            Test_commission=5.6,
            rates=[1],
        ),
    )

    assert db_session.query(Commission).count() == 1


def test_commission_create_fixed_fixed_no_rate_type_consumption_ok(
    db_session: Session, electricity_rate: Rate
):
    commission_create(
        db_session,
        CommissionCreateRequest(
            name="Commission name",
            rate_type_segmentation=False,
            range_type=RangeType.consumption,
            min_consumption=3.5,
            max_consumption=11.5,
            Test_commission=5.6,
            rates=[1],
        ),
    )

    assert db_session.query(Commission).count() == 1


def test_commission_create_fixed_fixed_rate_type_power_ok(
    db_session: Session, electricity_rate: Rate
):
    commission_create(
        db_session,
        CommissionCreateRequest(
            name="Commission name",
            rate_type_segmentation=True,
            rate_type_id=1,
            range_type=RangeType.power,
            min_power=3.5,
            max_power=11.5,
            Test_commission=5.6,
            rates=[1],
        ),
    )

    assert db_session.query(Commission).count() == 1


def test_commission_create_fixed_fixed_rate_type_consumption_ok(
    db_session: Session, electricity_rate: Rate
):
    commission_create(
        db_session,
        CommissionCreateRequest(
            name="Commission name",
            rate_type_segmentation=True,
            rate_type_id=1,
            range_type=RangeType.consumption,
            min_consumption=3.5,
            max_consumption=11.5,
            Test_commission=5.6,
            rates=[1],
        ),
    )

    assert db_session.query(Commission).count() == 1


def test_commission_create_duplicated_data_error(
    db_session: Session, commission_fixed_base: Commission
):
    with pytest.raises(HTTPException) as exc:
        commission_create(
            db_session,
            CommissionCreateRequest(
                name="Commission fixed base",
                percentage_Test_commission=12,
                rates=[2],
            ),
        )

    assert exc.value.detail == ("value_error.already_exists")
    assert db_session.query(Commission).count() == 1


def test_get_commission_ok(db_session: Session, commission: Commission):
    assert get_commission(db_session, 1)


def test_get_commission_not_exist(db_session: Session, commission: Commission):
    with pytest.raises(HTTPException) as exc:
        get_commission(db_session, 1234)
    assert exc.value.detail == ("commission_not_exist")


def test_get_commission_deleted(db_session: Session, commission: Commission):
    commission.is_deleted = True

    with pytest.raises(HTTPException) as exc:
        get_commission(db_session, 1)

    assert exc.value.detail == ("commission_not_exist")


def test_commission_update_fixed_fixed_ok(
    db_session: Session, commission: Commission, electricity_rate_2: Rate
):
    commission = commission_update(
        db_session,
        1,
        CommissionUpdateRequest(
            name="Commission modified",
            min_consumption=28.2,
            max_consumption=32.8,
            Test_commission=8,
            rates=[4],
        ),
    )

    assert (
        db_session.query(Commission)
        .filter(Commission.name == "Commission modified")
        .count()
        == 1
    )
    assert commission.id == 1
    assert commission.name == "Commission modified"
    assert commission.range_type == "consumption"
    assert commission.min_consumption == Decimal("28.2")
    assert commission.max_consumption == Decimal("32.8")
    assert commission.min_power is None
    assert commission.max_power is None
    assert commission.percentage_Test_commission is None
    assert commission.rate_type_segmentation is True
    assert commission.Test_commission == 8
    assert commission.create_at
    assert commission.rates == [electricity_rate_2]
    assert commission.rate_type_id == 1


def test_commission_update_fixed_base_ok(
    db_session: Session,
    commission_fixed_base: Commission,
    gas_rate_deleted: Rate,
    gas_rate: Rate,
):
    gas_rate_deleted.is_deleted = False

    commission = commission_update(
        db_session,
        2,
        CommissionUpdateRequest(
            name="Commission fixed base modified",
            percentage_Test_commission=8,
            rates=[2, 3],
        ),
    )

    assert (
        db_session.query(Commission)
        .filter(Commission.name == "Commission fixed base modified")
        .count()
        == 1
    )
    assert commission.id == 2
    assert commission.name == "Commission fixed base modified"
    assert commission.range_type is None
    assert commission.min_consumption is None
    assert commission.max_consumption is None
    assert commission.min_power is None
    assert commission.max_power is None
    assert commission.percentage_Test_commission == 8
    assert commission.rate_type_segmentation is None
    assert commission.Test_commission is None
    assert commission.create_at
    assert len(commission.rates) == 2
    assert commission.rate_type_id is None


def test_commission_update_invalid_rate_error(
    db_session: Session, commission: Commission, gas_rate: Rate, electricity_rate: Rate
):
    with pytest.raises(HTTPException) as exc:
        commission_update(
            db_session,
            1,
            CommissionUpdateRequest(
                name="Commission name",
                min_consumption=3.5,
                max_consumption=11.5,
                Test_commission=12,
                rates=[2],
            ),
        )

    assert exc.value.detail == ("value_error.rate.invalid")
    assert db_session.query(Commission).filter(Commission.id == 1).count() == 1
    commission = db_session.query(Commission).filter(Commission.id == 1).first()
    assert commission.id == 1
    assert commission.name == "Commission name"
    assert commission.rates == [electricity_rate]


def test_commission_update_invalid_price_type_error(
    db_session: Session, commission: Commission
):
    with pytest.raises(HTTPException) as exc:
        commission_update(
            db_session,
            1,
            CommissionUpdateRequest(
                name="Commission name",
                min_consumption=3.5,
                max_consumption=11.5,
                Test_commission=12,
                percentage_Test_commission=3,
                rates=[1],
            ),
        )

    assert exc.value.detail == ("value_error.rate.invalid_price_type")
    assert db_session.query(Commission).filter(Commission.id == 1).count() == 1
    commission = db_session.query(Commission).filter(Commission.id == 1).first()
    assert commission.id == 1
    assert commission.name == "Commission name"
    assert commission.percentage_Test_commission is None


def test_commission_partial_update_is_deleted_ok(
    db_session: Session, commission: Commission
):
    commission_partial_update(
        db_session,
        1,
        CommissionPartialUpdateRequest(
            is_deleted=True,
        ),
    )

    commission = db_session.query(Commission).filter(Commission.id == 1).first()
    assert commission.is_deleted is True


def test_commission_partial_update_is_deleted_not_exists(
    db_session: Session, commission: Commission
):
    with pytest.raises(HTTPException) as exc:
        commission_partial_update(
            db_session,
            2,
            CommissionPartialUpdateRequest(
                is_deleted=True,
            ),
        )

    assert exc.value.detail == ("commission_not_exist")

    commission = db_session.query(Commission).filter(Commission.id == 1).first()
    assert commission.is_deleted is False


def test_list_commission_ok(
    db_session: Session, commission: Commission, commission_fixed_base: Commission
):
    assert list_commissions(db_session, CommissionFilter()).count() == 2


def test_list_commission_empty_ok(db_session: Session, other_cost: Commission):
    other_cost.is_deleted = True
    assert list_commissions(db_session, CommissionFilter()).count() == 0


def test_delete_commissions_ok(
    db_session: Session,
    commission: Commission,
    commission_fixed_base: Commission,
):
    delete_commissions(db_session, CommissionDeleteRequest(ids=[1, 2, 84]))

    assert (
        db_session.query(Commission).filter(Commission.is_deleted == false()).count()
        == 0
    )


def test_delete_commissions_empty_ok(
    db_session: Session,
    commission: Commission,
    commission_fixed_base: Commission,
):
    delete_commissions(db_session, CommissionDeleteRequest(ids=[]))

    assert (
        db_session.query(Commission).filter(Commission.is_deleted == false()).count()
        == 2
    )
