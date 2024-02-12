import pytest
from fastapi import HTTPException, Request
from fastapi_pagination import Params
from sqlalchemy import false
from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.commissions import get_commission_queryset
from src.modules.commissions.models import Commission
from src.modules.commissions.schemas import CommissionFilter, commission_export_headers
from src.modules.rates.models import Rate
from src.modules.rates.schemas import rate_export_headers
from src.services.common import (
    generate_csv_file,
    get_current_user,
    paginate_queryset_with_n_to_many,
    update_from_dict,
)


@pytest.mark.asyncio
async def test_get_current_user(db_session, token_create):
    request = Request(scope={"type": "http"})
    request._headers = {"Authorization": f"token {token_create.token}"}

    user = await get_current_user(request, db_session)
    assert user == token_create.user


@pytest.mark.asyncio
async def test_get_current_user_error_not_token_prefix(db_session, token_create):
    request = Request(scope={"type": "http"})
    request._headers = {"Authorization": f"Bearer {token_create.token}"}

    with pytest.raises(HTTPException) as exc:
        await get_current_user(request, db_session)

    assert exc.value.detail == "not_authenticated"
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_error_token_not_exists(db_session, token_create):
    request = Request(scope={"type": "http"})
    request._headers = {"Authorization": "token 234234qf4325g34uy34"}

    with pytest.raises(HTTPException) as exc:
        await get_current_user(request, db_session)

    assert exc.value.detail == "invalid_credentials"
    assert exc.value.status_code == 401


def test_update_from_dict(user_create):
    user = update_from_dict(user_create, {"first_name": "Another name"})

    assert user.first_name == "Another name"


def test_update_from_dict_key_not_in_fields(user_create):
    user = update_from_dict(
        user_create, {"first_name": "Another name", "test_field": "test_value"}
    )

    assert user.first_name == "Another name"
    assert hasattr(user, "test_field")


def test_generate_csv_file_ok(
    db_session: Session,
    electricity_rate: Rate,
    gas_rate: Rate,
):
    rates = db_session.query(Rate).order_by(Rate.id).all()
    file_name = generate_csv_file("test_rates", rate_export_headers, rates)
    with open(file_name, "r") as f:
        assert f.readline() == (
            "Name;Price type;Client types;Rate type;energy type;Minimum power;Maximum power;"
            "Minimum consumption;Maximum consumption;Energy price 1;Energy price 2;"
            "Energy price 3;Energy price 4;Energy price 5;Energy price 6;Power price 1;"
            "Power price 2;Power price 3;Power price 4;Power price 5;Power price 6;"
            "Fixed term price;Permanency;Length;Is full renewable;Compensation surplus;"
            "Compensation surplus value;Status;Date\n"
        )
        assert f.readline().startswith(
            "Electricity rate;fixed_fixed;particular;Electricity rate type;electricity;10.50;"
            "23.39;12.50;23.39;17.190000;5.900000;87.730000;2.430000;12.230000;9.550000;19.170000;9.500000;"
            "73.870000;43.200000;23.120000;55.900000;;True;12;True;True;28.320000;True;"
        )
        assert f.readline().startswith(
            "Gas rate name;fixed_base;particular;Gas rate type;gas;;;;;17.190000;;;;;;;;;;;;;"
            "False;24;;;;True;"
        )


def test_generate_csv_file_list_of_objects_ok(
    db_session: Session,
    commission: Commission,
    commission_fixed_base: Commission,
):
    commissions = db_session.query(Commission).all()
    filename = generate_csv_file(
        "test_commissions", commission_export_headers, commissions
    )
    with open(filename, "r") as f:
        assert f.readline() == (
            "Id;Name;Range type;Minimum consumption;Maximum consumption;"
            "Minimum power;Maximum power;Percentage Test commission;"
            "Rate type segmentation;Test commission;Rates;Rate type;Date\n"
        )
        assert f.readline().startswith(
            "1;Commission name;consumption;3.50;11.50;;;;True;12.00;"
            "Electricity rate;Electricity rate type;"
        )
        assert f.readline().startswith(
            "2;Commission fixed base;;;;;;12;;;Gas rate name;;"
        )


def test_paginate_queryset_with_n_to_many_ok(
    db_session: Session,
    commission: Commission,
    commission_fixed_base: Commission,
    electricity_rate_2: Rate,
):
    commission.rates.append(electricity_rate_2)
    db_session.add(commission)

    commission_filter = CommissionFilter()
    qs = commission_filter.filter(
        get_commission_queryset(db_session, None, Commission.is_deleted == false())
    )

    paginated_result = paginate_queryset_with_n_to_many(
        qs, params=Params(page=1, size=20)
    )

    assert len(qs.all()) == 2
    assert qs.count() == 2
    assert paginated_result.total == 2
    assert len(paginated_result.items) == 2
