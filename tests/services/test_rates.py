from decimal import Decimal

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import false
from sqlalchemy.orm import Session

from src.modules.commissions.models import Commission
from src.modules.costs.models import OtherCost
from src.modules.margins.models import Margin
from src.modules.marketers.models import Marketer
from src.modules.rates.models import HistoricalRate, Rate, RateType
from src.modules.rates.schemas import (
    RateCreateRequest,
    RateDeleteRequest,
    RatePartialUpdateRequest,
    RateTypeCreateRequest,
    RateTypeFilter,
    RateTypeUpdatePartialRequest,
    RateUpdateRequest,
)
from src.modules.users.models import User
from src.services.rates import (
    delete_rate_types,
    delete_rates,
    get_rate,
    get_rate_type,
    get_rate_type_power_ranges,
    get_validated_rates,
    list_rate_types,
    rate_create,
    rate_partial_update,
    rate_type_create,
    rate_type_partial_update,
    rate_update,
    validate_rate,
    validate_rate_create,
    validate_rate_update_consumption_range,
)


def test_rate_type_create_ok(db_session: Session, user_create: User) -> None:
    rate_type_create(
        db_session,
        RateTypeCreateRequest(name="Name", energy_type="gas", user_id=1),
        user_create,
    )

    assert db_session.query(RateType).count() == 1


def test_rate_type_create_already_exists_error(
    db_session: Session, user_create: User, electricity_rate_type: RateType
) -> None:
    with pytest.raises(HTTPException) as exc:
        rate_type_create(
            db_session,
            RateTypeCreateRequest(
                name="Electricity rate type", energy_type="electricity", user_id=1
            ),
            user_create,
        )

    assert exc.value.status_code == 409
    assert exc.value.detail == "value_error.already_exists"


def test_list_rate_types_ok(
    db_session: Session, gas_rate_type: RateType, deleted_rate_type: RateType
) -> None:
    assert list_rate_types(db_session, RateTypeFilter()).count() == 1


def test_list_rate_types_empty_ok(
    db_session: Session, deleted_rate_type: RateType
) -> None:
    assert list_rate_types(db_session, RateTypeFilter()).count() == 0


def test_rate_type_partial_update_ok(
    db_session: Session, electricity_rate_type: RateType
) -> None:
    rate_type_partial_update(
        db_session,
        1,
        RateTypeUpdatePartialRequest(
            max_power=25.15, min_power=15.3, enable=False, is_deleted=True
        ),
    )

    rate_type = db_session.query(RateType).filter(RateType.id == 1).first()
    assert rate_type.id == 1
    assert rate_type.name == "Electricity rate type"
    assert rate_type.energy_type == "electricity"
    assert rate_type.max_power == Decimal("25.15")
    assert rate_type.min_power == Decimal("15.3")
    assert rate_type.enable is False
    assert rate_type.is_deleted is True


def test_rate_type_partial_update_gas_ok(
    db_session: Session, gas_rate_type: RateType
) -> None:
    rate_type_partial_update(
        db_session,
        2,
        RateTypeUpdatePartialRequest(enable=False, is_deleted=True),
    )

    rate_type = db_session.query(RateType).filter(RateType.id == 2).first()
    assert rate_type.id == 2
    assert rate_type.name == "Gas rate type"
    assert rate_type.energy_type == "gas"
    assert rate_type.max_power is None
    assert rate_type.min_power is None
    assert rate_type.enable is False
    assert rate_type.is_deleted is True


def test_rate_type_partial_update_none_power_range_ok(
    db_session: Session, electricity_rate_type: RateType
) -> None:
    response = rate_type_partial_update(
        db_session,
        1,
        RateTypeUpdatePartialRequest(
            min_power=None,
            max_power=None,
        ),
    )

    rate_type = db_session.query(RateType).filter(RateType.id == 1).first()
    assert rate_type.name == "Electricity rate type"
    assert not rate_type.min_power
    assert not rate_type.max_power
    assert not response.min_power
    assert not response.max_power


def test_rate_type_partial_update_none_power_range_error(
    db_session: Session, electricity_rate_type: RateType
) -> None:
    with pytest.raises(HTTPException) as exc:
        rate_type_partial_update(
            db_session,
            1,
            RateTypeUpdatePartialRequest(
                min_power=None,
            ),
        )

    assert exc.value.detail == ("value_error.power_range.missing")
    rate_type = db_session.query(RateType).filter(RateType.id == 1).first()
    assert rate_type.name == "Electricity rate type"
    assert rate_type.min_power == 1.5


def test_rate_type_partial_update_invalid_energy_type(
    db_session: Session, gas_rate_type: RateType
) -> None:
    with pytest.raises(HTTPException) as exc:
        rate_type_partial_update(
            db_session,
            2,
            RateTypeUpdatePartialRequest(
                max_power=25.15,
                min_power=15.3,
            ),
        )
    assert exc.value.detail == ("value_error.energy_type.invalid")
    rate_type = db_session.query(RateType).filter(RateType.id == 2).first()
    assert rate_type.id == 2
    assert rate_type.name == "Gas rate type"
    assert rate_type.energy_type == "gas"
    assert rate_type.enable is True


def test_rate_type_partial_update_not_exists(
    db_session: Session, gas_rate_type: RateType
) -> None:
    with pytest.raises(HTTPException) as exc:
        rate_type_partial_update(
            db_session,
            1,
            RateTypeUpdatePartialRequest(
                max_power=25.15,
                min_power=3.2,
            ),
        )

    assert exc.value.detail == ("rate_type_not_exist")
    rate_type = db_session.query(RateType).filter(RateType.id == 2).first()
    assert rate_type.id == 2
    assert rate_type.name == "Gas rate type"
    assert rate_type.energy_type == "gas"
    assert rate_type.enable is True


def test_rate_type_partial_update_deleted(
    db_session: Session, deleted_rate_type: RateType
) -> None:
    with pytest.raises(HTTPException) as exc:
        rate_type_partial_update(
            db_session,
            4,
            RateTypeUpdatePartialRequest(
                max_power=25.15,
                min_power=3.2,
            ),
        )

    assert exc.value.detail == ("rate_type_not_exist")


def test_rate_type_partial_update_invalid_power_value(
    db_session: Session, electricity_rate_type: RateType
) -> None:
    with pytest.raises(ValidationError) as exc:
        rate_type_partial_update(
            db_session,
            1,
            RateTypeUpdatePartialRequest(
                min_power=-2.6,
            ),
        )

    # TODO --> Check why this is not a custom validation error
    assert exc.value.errors()[0]["msg"] == (
        "ensure this value is greater than or equal to 0"
    )
    rate_type = db_session.query(RateType).filter(RateType.id == 1).first()
    assert rate_type.name == "Electricity rate type"
    assert rate_type.min_power == Decimal("1.5")


def test_rate_type_partial_update_power_range_invalid(
    db_session: Session, electricity_rate_type: RateType
) -> None:
    with pytest.raises(HTTPException) as exc:
        rate_type_partial_update(
            db_session,
            1,
            RateTypeUpdatePartialRequest(
                max_power=2.23,
                min_power=15.3,
            ),
        )

    assert exc.value.detail == ("value_error.power_range.invalid_range")
    rate_type = db_session.query(RateType).filter(RateType.id == 1).first()
    assert rate_type.id == 1
    assert rate_type.min_power == Decimal("1.5")
    assert rate_type.max_power == Decimal("30.30")


def test_rate_type_partial_update_power_range_invalid_one_value(
    db_session: Session, electricity_rate_type: RateType
) -> None:
    with pytest.raises(HTTPException) as exc:
        rate_type_partial_update(
            db_session,
            1,
            RateTypeUpdatePartialRequest(
                min_power=45.3,
            ),
        )

    assert exc.value.detail == ("value_error.power_range.invalid_range")
    rate_type = db_session.query(RateType).filter(RateType.id == 1).first()
    assert rate_type.id == 1
    assert rate_type.min_power == Decimal("1.5")
    assert rate_type.max_power == Decimal("30.30")


def test_get_rate_type_ok(db_session: Session, electricity_rate_type: RateType) -> None:
    rate_type = get_rate_type(db_session, 1)
    assert rate_type.name == "Electricity rate type"
    assert rate_type.energy_type == "electricity"
    assert rate_type.max_power == Decimal("30.30")
    assert rate_type.min_power == Decimal("1.5")


def test_get_rate_type_not_exist(db_session: Session) -> None:
    with pytest.raises(HTTPException) as exc:
        get_rate_type(db_session, 28)

    assert exc.value.detail == ("rate_type_not_exist")


def test_get_rate_type_deleted(
    db_session: Session, deleted_rate_type: RateType
) -> None:
    with pytest.raises(HTTPException) as exc:
        get_rate_type(db_session, 4)

    assert exc.value.detail == ("rate_type_not_exist")


def test_get_rate_type_power_ranges_ok(
    db_session: Session, electricity_rate_type: RateType, disable_rate_type: RateType
) -> None:
    range_values = get_rate_type_power_ranges(db_session)
    assert range_values["minimum_min_power"] == Decimal("0")
    assert range_values["maximum_min_power"] == Decimal("1.5")
    assert range_values["minimum_max_power"] == Decimal("21.54")
    assert range_values["maximum_max_power"] == Decimal("30.3")


def test_get_rate_type_power_ranges_no_rate_types(
    db_session: Session, deleted_rate_type: RateType
) -> None:
    range_values = get_rate_type_power_ranges(db_session)
    assert not range_values["minimum_min_power"]
    assert not range_values["maximum_min_power"]
    assert not range_values["minimum_max_power"]
    assert not range_values["maximum_max_power"]


def test_delete_rate_types_ok(
    db_session: Session,
    electricity_rate_type: RateType,
    gas_rate_type: RateType,
    disable_rate_type: RateType,
    deleted_rate_type: RateType,
) -> None:
    delete_rate_types(db_session, RateDeleteRequest(ids=[1, 2, 84]))

    assert (
        db_session.query(RateType).filter(RateType.is_deleted == false()).count() == 1
    )


def test_delete_rate_types_with_related_rates_ok(
    db_session: Session,
    electricity_rate_type: RateType,
    gas_rate_type: RateType,
    gas_rate_type_2: RateType,
    disable_rate_type: RateType,
    deleted_rate_type: RateType,
    electricity_rate: Rate,
    electricity_rate_2: Rate,
    gas_rate_active: Rate,
) -> None:
    """
    It tests that all the rates related to the deleted rate types are disabled after its deletion
    """
    gas_rate = Rate(
        id=100,
        name="New Gas Rate",
        price_type="fixed_base",
        client_types=["particular"],
        energy_price_1=17.19,
        permanency=False,
        length=24,
        rate_type_id=gas_rate_type_2.id,
        marketer_id=2,
    )
    db_session.add(gas_rate)
    db_session.commit()
    delete_rate_types(db_session, RateDeleteRequest(ids=[1, 2, 84]))

    assert (
        db_session.query(RateType).filter(RateType.is_deleted == false()).count() == 2
    )
    assert electricity_rate.is_active is False
    assert electricity_rate_2.is_active is False
    assert gas_rate_active.is_active is False
    assert gas_rate.is_active is True


def test_delete_rate_types_empty_ok(
    db_session: Session,
    electricity_rate_type: RateType,
    gas_rate_type: RateType,
    disable_rate_type: RateType,
    deleted_rate_type: RateType,
) -> None:
    delete_rate_types(db_session, RateDeleteRequest(ids=[]))

    assert (
        db_session.query(RateType).filter(RateType.is_deleted == false()).count() == 3
    )


def test_validate_rate_ok() -> None:
    values = validate_rate(
        "electricity",
        "fixed_fixed",
        {"max_power": 15.15, "min_power": 0.0, "is_full_renewable": False},
    )
    assert values


def test_validate_rate_error_power_range_with_gas() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_rate(
            "gas",
            "fixed_fixed",
            {
                "max_power": 15.15,
                "min_power": 0.0,
            },
        )
    assert exc.value.detail == "value_error.power_range.invalid_rate_combination"


def test_validate_rate_error_power_range_with_fixed_base() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_rate(
            "electricity",
            "fixed_base",
            {
                "max_power": 15.15,
                "min_power": 0.0,
            },
        )
    assert exc.value.detail == "value_error.power_range.invalid_rate_combination"


def test_validate_rate_error_power_range_invalid() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_rate(
            "electricity",
            "fixed_fixed",
            {
                "max_power": 15.15,
                "min_power": 23.44,
            },
        )
    assert exc.value.detail == "value_error.power_range.invalid_range"


def test_validate_rate_error_power_range_missing() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_rate(
            "electricity",
            "fixed_fixed",
            {
                "max_power": 15.15,
            },
        )

    assert exc.value.detail == "value_error.power_range.invalid_range"


def test_validate_rate_error_electricity_with_consumption() -> None:
    values = validate_rate(
        "electricity",
        "fixed_fixed",
        {
            "max_power": 15.15,
            "min_power": 0.0,
            "min_consumption": 5.36,
            "is_full_renewable": False,
        },
    )

    assert values


def test_validate_rate_error_electricity_with_fixed_term_price() -> None:
    values = validate_rate(
        "electricity",
        "fixed_fixed",
        {
            "max_power": 15.15,
            "min_power": 0.0,
            "fixed_term_price": 5.36,
            "is_full_renewable": False,
        },
    )
    assert values


def test_validate_rate_electricity_with_compensation_surplus_ok() -> None:
    values = validate_rate(
        "electricity",
        "fixed_fixed",
        {
            "max_power": 15.15,
            "min_power": 0.0,
            "is_full_renewable": False,
            "compensation_surplus": True,
            "compensation_surplus_value": 18,
        },
    )
    assert values["compensation_surplus"]
    assert values["compensation_surplus_value"] == 18


def test_validate_rate_electricity_with_compensation_surplus_no_value_ok() -> None:
    values = validate_rate(
        "electricity",
        "fixed_fixed",
        {
            "max_power": 15.15,
            "min_power": 0.0,
            "is_full_renewable": False,
            "compensation_surplus": True,
        },
    )
    assert values


def test_validate_rate_electricity_with_compensation_surplus_with_value_ok() -> None:
    values = validate_rate(
        "electricity",
        "fixed_fixed",
        {
            "max_power": 15.15,
            "min_power": 0.0,
            "is_full_renewable": False,
            "compensation_surplus": False,
            "compensation_surplus_value": 18,
        },
    )
    assert values["compensation_surplus"] is False
    assert values["compensation_surplus_value"] is None


def test_validate_rate_electricity_error_is_full_renewable_missing() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_rate(
            "electricity",
            "fixed_fixed",
            {},
        )
    assert exc.value.detail == "value_error.is_full_renewable.required"


def test_validate_rate_error_missing_consumption_range() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_rate(
            "gas",
            "fixed_fixed",
            {
                "min_consumption": 26.3,
            },
        )
    assert exc.value.detail == "value_error.consumption_range.invalid_consumption_range"


def test_validate_rate_error_invalid_consumption_range() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_rate(
            "gas",
            "fixed_fixed",
            {
                "min_consumption": 26.3,
                "max_consumption": 6.3,
            },
        )
    assert exc.value.detail == "value_error.consumption_range.invalid_consumption_range"


def test_validate_rate_create_ok() -> None:
    assert (
        validate_rate_create(
            "electricity",
            {
                "price_type": "fixed_fixed",
                "energy_price_2": 5.36,
            },
        )
        is None
    )


def test_validate_rate_create_error_gas_with_energy_price_2() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_rate_create(
            "gas",
            {
                "price_type": "fixed_fixed",
                "energy_price_2": 5.36,
            },
        )
    assert exc.value.detail == "value_error.energy_type.invalid_price"


def test_validate_rate_create_error_gas_with_power_price_1() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_rate_create(
            "gas",
            {
                "price_type": "fixed_fixed",
                "power_price_1": 5.36,
            },
        )
    assert exc.value.detail == "value_error.energy_type.invalid_price"


def test_rate_create_ok(
    db_session: Session, electricity_rate_type: RateType, marketer: Marketer
) -> None:
    rate_create(
        db_session,
        RateCreateRequest(
            name="Electricity rate",
            price_type="fixed_fixed",
            client_types=["particular"],
            min_power=10.5,
            max_power=23.39,
            energy_price_1=17.19,
            energy_price_2=5.9,
            energy_price_3=87.73,
            energy_price_4=2.43,
            energy_price_5=12.23,
            energy_price_6=9.55,
            power_price_1=19.17,
            power_price_2=9.5,
            power_price_3=73.87,
            power_price_4=43.2,
            power_price_5=23.12,
            power_price_6=55.9,
            permanency=True,
            length=12,
            is_full_renewable=True,
            compensation_surplus=True,
            compensation_surplus_value=28.32,
            rate_type_id=1,
            marketer_id=1,
        ),
    )

    assert db_session.query(Rate).count() == 1


def test_get_rate_ok(db_session: Session, electricity_rate: Rate) -> None:
    assert get_rate(db_session, 1)


def test_get_rate_not_exist(db_session: Session, electricity_rate: Rate) -> None:
    with pytest.raises(HTTPException) as exc:
        get_rate(db_session, 1234)
    assert exc.value.detail == ("rate_not_exist")


def test_get_rate_deleted(db_session: Session, electricity_rate: Rate) -> None:
    electricity_rate.is_deleted = True

    with pytest.raises(HTTPException) as exc:
        get_rate(db_session, 1)

    assert exc.value.detail == ("rate_not_exist")


def test_get_validated_rates_ok(db_session: Session, electricity_rate: Rate) -> None:
    assert get_validated_rates(db_session, [1]) == [electricity_rate]


def test_get_validated_rates_same_price_and_rate_type_ok(
    db_session: Session, electricity_rate: Rate, electricity_rate_2: Rate
) -> None:
    assert get_validated_rates(db_session, [1, 4], True) == [
        electricity_rate,
        electricity_rate_2,
    ]


def test_get_validated_rates_same_price_and_rate_type_invalid_error(
    db_session: Session,
    electricity_rate: Rate,
    electricity_rate_2: Rate,
    disable_rate_type: RateType,
) -> None:
    electricity_rate_2.rate_type_id = 3

    with pytest.raises(HTTPException) as exc:
        get_validated_rates(db_session, [1, 4], True)

    assert exc.value.detail == ("value_error.rate.invalid")


def test_get_validated_rates_invalid_rate_error(
    db_session: Session, electricity_rate: Rate, gas_rate: Rate
) -> None:
    with pytest.raises(HTTPException) as exc:
        get_validated_rates(db_session, [1, 2])

    assert exc.value.detail == ("value_error.rate.invalid")


def test_get_validated_rate_not_exist_error(
    db_session: Session, electricity_rate: Rate, gas_rate: Rate
) -> None:
    with pytest.raises(HTTPException) as exc:
        get_validated_rates(db_session, [18])

    assert exc.value.detail == ("rate_not_exist")


def test_validate_rate_update_electricity_rate_with_consumption_range_ok() -> None:
    rate_data = validate_rate_update_consumption_range(
        "electricity",
        {"min_consumption": 3.23, "max_consumption": 23.23, "fixed_term_price": 0.33},
    )

    assert rate_data.get("min_consumption") is None
    assert rate_data.get("max_consumption") is None
    assert rate_data.get("fixed_term_price") is None


def test_validate_rate_update_gas_rate_with_consumption_range_ok() -> None:
    rate_data = validate_rate_update_consumption_range(
        "gas",
        {"min_consumption": 3.23, "max_consumption": 23.23, "fixed_term_price": 0.33},
    )

    assert rate_data.get("min_consumption") == 3.23
    assert rate_data.get("max_consumption") == 23.23
    assert rate_data.get("fixed_term_price") == 0.33


def test_validate_rate_update_gas_rate_max_consumption_missing_error() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_rate_update_consumption_range(
            "gas", {"min_consumption": 3.23, "fixed_term_price": 0.33}
        )

    assert exc.value.detail == (
        "value_error.consumption_range.invalid_consumption_range"
    )


def test_validate_rate_update_gas_rate_invalid_consumption_range_error() -> None:
    with pytest.raises(HTTPException) as exc:
        validate_rate_update_consumption_range(
            "gas", {"min_consumption": 33.23, "max_consumption": 0.33}
        )

    assert exc.value.detail == (
        "value_error.consumption_range.invalid_consumption_range"
    )


def test_rate_update_electricity_rate_ok(
    db_session: Session, electricity_rate: Rate, disable_rate_type: RateType
) -> None:
    rate_update(
        db_session,
        1,
        RateUpdateRequest(
            name="New rate name",
            client_types=["company"],
            rate_type_id=3,
            min_power=5.8,
            max_power=15.36,
            energy_price_1=19.17,
            energy_price_2=9.5,
            energy_price_3=73.87,
            energy_price_4=43.2,
            energy_price_5=23.12,
            energy_price_6=55.9,
            power_price_1=17.19,
            power_price_2=5.9,
            power_price_3=87.73,
            power_price_4=2.43,
            power_price_5=12.23,
            power_price_6=9.55,
            permanency=False,
            length=24,
            is_full_renewable=False,
            compensation_surplus=False,
        ),
    )

    electricity_rate = db_session.query(Rate).filter(Rate.id == 1).first()
    modifications_qs = db_session.query(HistoricalRate).filter(
        HistoricalRate.rate_id == 1
    )
    assert electricity_rate.id == 1
    assert electricity_rate.name == "New rate name"
    assert electricity_rate.client_types == ["company"]
    assert electricity_rate.rate_type_id == 3
    assert electricity_rate.min_power == Decimal("5.8")
    assert electricity_rate.max_power == Decimal("15.36")
    assert electricity_rate.energy_price_1 == Decimal("19.17")
    assert electricity_rate.energy_price_2 == Decimal("9.5")
    assert electricity_rate.energy_price_3 == Decimal("73.87")
    assert electricity_rate.energy_price_4 == Decimal("43.2")
    assert electricity_rate.energy_price_5 == Decimal("23.12")
    assert electricity_rate.energy_price_6 == Decimal("55.9")
    assert electricity_rate.power_price_1 == Decimal("17.19")
    assert electricity_rate.power_price_2 == Decimal("5.9")
    assert electricity_rate.power_price_3 == Decimal("87.73")
    assert electricity_rate.power_price_4 == Decimal("2.43")
    assert electricity_rate.power_price_5 == Decimal("12.23")
    assert electricity_rate.power_price_6 == Decimal("9.55")
    assert electricity_rate.permanency is False
    assert electricity_rate.length == 24
    assert electricity_rate.is_full_renewable is False
    assert electricity_rate.compensation_surplus is False
    assert not electricity_rate.compensation_surplus_value
    assert modifications_qs.filter(
        HistoricalRate.price_name == "energy_price_1"
    ).first().price == Decimal("19.17")
    assert modifications_qs.count() == 12


def test_rate_update_gas_rate_ok(
    db_session: Session, gas_rate: Rate, gas_rate_type_2: RateType
) -> None:
    rate_update(
        db_session,
        2,
        RateUpdateRequest(
            name="New rate name",
            client_types=["company"],
            rate_type_id=5,
            min_consumption=13.14,
            max_consumption=14.13,
            energy_price_1=19.17,
            fixed_term_price=32.5,
            permanency=False,
            length=7,
        ),
    )

    gas_rate = db_session.query(Rate).filter(Rate.id == 2).first()
    modifications_qs = db_session.query(HistoricalRate).filter(
        HistoricalRate.rate_id == 2
    )
    assert gas_rate.id == 2
    assert gas_rate.name == "New rate name"
    assert gas_rate.client_types == ["company"]
    assert gas_rate.rate_type_id == 5
    assert gas_rate.min_consumption == Decimal("13.14")
    assert gas_rate.max_consumption == Decimal("14.13")
    assert gas_rate.energy_price_1 == Decimal("19.17")
    assert gas_rate.fixed_term_price == Decimal("32.5")
    assert modifications_qs.count() == 2
    assert modifications_qs.filter(
        HistoricalRate.price_name == "energy_price_1"
    ).first().price == Decimal("19.17")
    assert modifications_qs.filter(
        HistoricalRate.price_name == "fixed_term_price"
    ).first().price == Decimal("32.5")


def test_rate_update_not_exists(db_session: Session, electricity_rate: Rate) -> None:
    with pytest.raises(HTTPException) as exc:
        rate_update(
            db_session,
            2,
            RateUpdateRequest(
                name="New rate name",
                client_types=["company"],
                rate_type_id=1,
                energy_price_1=17.19,
                permanency=False,
                length=7,
            ),
        )

    assert exc.value.detail == ("rate_not_exist")
    electricity_rate = db_session.query(Rate).filter(Rate.id == 1).first()
    assert electricity_rate.id == 1
    assert electricity_rate.name == "Electricity rate"
    assert electricity_rate.client_types == ["particular"]
    assert electricity_rate.is_active is True


def test_rate_update_invalid_power_range_value(
    db_session: Session, electricity_rate: Rate
) -> None:
    with pytest.raises(HTTPException) as exc:
        rate_update(
            db_session,
            electricity_rate.id,
            RateUpdateRequest(
                name="Electricity rate",
                client_types=["particular"],
                rate_type_id=1,
                energy_price_1=17.19,
                min_power=532.26,
                max_power=26.53,
                permanency=False,
                length=7,
            ),
        )

    assert exc.value.detail == ("value_error.power_range.invalid_range")
    electricity_rate = db_session.query(Rate).filter(Rate.id == 1).first()
    assert electricity_rate.min_power == Decimal("10.5")


def test_rate_update_invalid_field_for_electricity_energy_type(
    db_session: Session, electricity_rate: Rate
) -> None:
    rate_update(
        db_session,
        1,
        RateUpdateRequest(
            name="Electricity rate",
            client_types=["particular"],
            rate_type_id=1,
            energy_price_1=17.19,
            fixed_term_price=32.26,
            permanency=False,
            length=7,
            is_full_renewable=False,
        ),
    )

    electricity_rate = db_session.query(Rate).filter(Rate.id == 1).first()
    assert not electricity_rate.fixed_term_price


def test_rate_update_gas_price_ok(db_session: Session, gas_rate: RateType) -> None:
    rate_update(
        db_session,
        2,
        RateUpdateRequest(
            name="Modified gas rate",
            client_types=["particular"],
            rate_type_id=2,
            energy_price_1=9.5,
            fixed_term_price=19.17,
            min_consumption=3.17,
            max_consumption=19.67,
            permanency=False,
            length=7,
        ),
    )

    gas_rate = db_session.query(Rate).filter(Rate.id == 2).first()
    modifications_qs = db_session.query(HistoricalRate).filter(
        HistoricalRate.rate_id == 2
    )
    assert gas_rate.id == 2
    assert gas_rate.name == "Modified gas rate"
    assert gas_rate.energy_price_1 == Decimal("9.5")
    assert gas_rate.fixed_term_price == Decimal("19.17")
    assert gas_rate.min_consumption == Decimal("3.17")
    assert gas_rate.max_consumption == Decimal("19.67")
    assert modifications_qs.filter(
        HistoricalRate.price_name == "energy_price_1"
    ).first().price == Decimal("9.5")
    assert modifications_qs.filter(
        HistoricalRate.price_name == "fixed_term_price"
    ).first().price == Decimal("19.17")
    assert modifications_qs.count() == 2


def test_rate_update_gas_max_consuption_missing_error(
    db_session: Session, gas_rate: RateType
) -> None:
    with pytest.raises(HTTPException) as exc:
        rate_update(
            db_session,
            2,
            RateUpdateRequest(
                name="Gas rate name",
                client_types=["particular"],
                rate_type_id=2,
                energy_price_1=17.19,
                min_consumption=19.17,
                permanency=False,
                length=7,
            ),
        )

    assert exc.value.detail == (
        "value_error.consumption_range.invalid_consumption_range"
    )
    rate = db_session.query(Rate).filter(Rate.id == 2).first()
    assert not rate.min_consumption


def test_rate_update_gas_invalid_consuption_range_error(
    db_session: Session, gas_rate: RateType
) -> None:
    with pytest.raises(HTTPException) as exc:
        rate_update(
            db_session,
            2,
            RateUpdateRequest(
                name="Gas rate name",
                client_types=["particular"],
                rate_type_id=2,
                energy_price_1=17.19,
                min_consumption=19.17,
                max_consumption=3.67,
                permanency=False,
                length=7,
            ),
        )

    assert exc.value.detail == (
        "value_error.consumption_range.invalid_consumption_range"
    )
    rate = db_session.query(Rate).filter(Rate.id == 2).first()
    assert not rate.min_consumption
    assert not rate.max_consumption


def test_rate_update_invalid_price_ok(
    db_session: Session, electricity_rate: RateType
) -> None:
    rate_update(
        db_session,
        1,
        RateUpdateRequest(
            name="Modified rate",
            client_types=["particular"],
            rate_type_id=1,
            energy_price_1=17.19,
            energy_price_2=9.5,
            fixed_term_price=19.17,
            permanency=False,
            length=7,
            is_full_renewable=False,
        ),
    )

    rate = db_session.query(Rate).filter(Rate.id == 1).first()
    modifications_qs = db_session.query(HistoricalRate).filter(
        HistoricalRate.rate_id == 1
    )
    assert rate.id == 1
    assert rate.name == "Modified rate"
    assert rate.energy_price_2 == Decimal("9.5")
    assert not rate.fixed_term_price
    assert modifications_qs.filter(
        HistoricalRate.price_name == "energy_price_2"
    ).first().price == Decimal("9.5")
    assert modifications_qs.count() == 1


def test_rate_update_invalid_price_gas_ok(
    db_session: Session, gas_rate: RateType
) -> None:
    rate_update(
        db_session,
        2,
        RateUpdateRequest(
            name="Modified rate",
            client_types=["particular"],
            rate_type_id=2,
            energy_price_1=19.17,
            energy_price_2=9.5,
            fixed_term_price=32.14,
            permanency=False,
            length=7,
        ),
    )

    rate = db_session.query(Rate).filter(Rate.id == 2).first()
    modifications_qs = db_session.query(HistoricalRate).filter(
        HistoricalRate.rate_id == 2
    )
    assert rate.id == 2
    assert rate.name == "Modified rate"
    assert rate.energy_price_1 == Decimal("19.17")
    assert rate.energy_price_2 is None
    assert rate.fixed_term_price == Decimal("32.14")
    assert modifications_qs.filter(
        HistoricalRate.price_name == "energy_price_1"
    ).first().price == Decimal("19.17")
    assert modifications_qs.count() == 2


def test_rate_partial_update_ok(db_session: Session, electricity_rate: Rate) -> None:
    rate_partial_update(
        db_session,
        1,
        RatePartialUpdateRequest(
            is_active=False,
        ),
    )

    electricity_rate = db_session.query(Rate).filter(Rate.id == 1).first()
    assert electricity_rate.is_active is False


def test_rate_partial_update_not_exists(
    db_session: Session, electricity_rate: Rate
) -> None:
    with pytest.raises(HTTPException) as exc:
        rate_partial_update(
            db_session,
            2,
            RatePartialUpdateRequest(
                is_active=False,
            ),
        )

    assert exc.value.detail == ("rate_not_exist")

    electricity_rate = db_session.query(Rate).filter(Rate.id == 1).first()
    assert electricity_rate.is_active is True


def test_delete_rates_ok(
    db_session: Session,
    electricity_rate: Rate,
    electricity_rate_2: Rate,
    gas_rate: Rate,
    gas_rate_deleted: Rate,
) -> None:
    delete_rates(db_session, RateDeleteRequest(ids=[1, 2, 84]))

    assert db_session.query(Rate).filter(Rate.is_deleted == false()).count() == 1


def test_delete_rates_and_related_margins_ok(
    db_session: Session,
    electricity_rate: Rate,
    electricity_rate_2: Rate,
    gas_rate: Rate,
    gas_rate_deleted: Rate,
    margin: Margin,
) -> None:
    """
    If a rate is deleted then we need to delete its related margins as well
    """
    delete_rates(db_session, RateDeleteRequest(ids=[1, 2, 84]))

    assert db_session.query(Rate).filter(Rate.is_deleted == false()).count() == 1
    assert margin.is_deleted is True


def test_delete_rates_and_related_objects_ok(
    db_session: Session,
    electricity_rate: Rate,
    electricity_rate_2: Rate,
    gas_rate: Rate,
    gas_rate_deleted: Rate,
    commission: Commission,
    commission_2: Commission,
    other_cost: OtherCost,
    other_cost_2_rates: OtherCost,
) -> None:
    """
    If a rate is deleted then we need to delete its related margins as well
    """
    commission_2.rates.append(electricity_rate_2)
    other_cost_2_rates.rates.append(gas_rate)
    db_session.commit()
    db_session.refresh(commission_2)
    db_session.refresh(other_cost_2_rates)

    delete_rates(db_session, RateDeleteRequest(ids=[1, 2, 84]))

    assert db_session.query(Rate).filter(Rate.is_deleted == false()).count() == 1

    assert commission.is_deleted is True
    assert len(commission.rates) == 0
    assert commission_2.is_deleted is False
    assert len(commission_2.rates) == 1

    assert other_cost.is_deleted is True
    assert len(other_cost.rates) == 0
    assert other_cost_2_rates.is_deleted is False
    assert len(other_cost_2_rates.rates) == 1


def test_delete_rates_empty_ok(
    db_session: Session,
    electricity_rate: Rate,
    electricity_rate_2: Rate,
    gas_rate: Rate,
    gas_rate_deleted: Rate,
) -> None:
    delete_rates(db_session, RateDeleteRequest(ids=[]))

    assert db_session.query(Rate).filter(Rate.is_deleted == false()).count() == 3
