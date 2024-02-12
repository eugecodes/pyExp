from sqlalchemy import false
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from src.infrastructure.sqlalchemy.rates import get_rate_by
from src.modules.commissions.models import Commission
from src.modules.costs.models import OtherCost
from src.modules.marketers.models import Marketer
from src.modules.rates.models import Rate, RateType
from src.modules.users.models import Token


def test_rate_type_create_endpoint_gas_ok(
    test_client: TestClient, token_create: Token, db_session: Session
):
    response = test_client.post(
        "/api/rate-types",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Name",
            "energy_type": "gas",
        },
    )

    assert response.status_code == 201
    rate_type = db_session.query(RateType).all()
    assert len(rate_type) == 1
    assert rate_type[0].is_deleted is False


def test_rate_type_create_endpoint_electricity_ok(
    test_client: TestClient, token_create: Token, db_session: Session
):
    response = test_client.post(
        "/api/rate-types",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Name",
            "energy_type": "electricity",
            "min_power": 0.0,
            "max_power": 10.0,
        },
    )

    assert response.status_code == 201
    assert db_session.query(RateType).count() == 1


def test_rate_type_create_endpoint_electricity_no_power_ok(
    test_client: TestClient, token_create: Token, db_session: Session
):
    response = test_client.post(
        "/api/rate-types",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Name",
            "energy_type": "electricity",
        },
    )

    assert response.status_code == 201
    assert db_session.query(RateType).count() == 1


def test_rate_type_create_endpoint_already_exists_error(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    electricity_rate_type: RateType,
):
    response = test_client.post(
        "/api/rate-types",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Electricity rate type",
            "energy_type": "electricity",
        },
    )

    assert response.status_code == 409
    json_response = response.json()
    assert json_response["detail"][0]["code"] == "RESOURCE_ALREADY_EXISTS"
    assert (
        json_response["detail"][0]["message"]
        == "Another resource already exists with the same data"
    )


def test_rate_type_create_endpoint_error_auth(
    test_client: TestClient, db_session: Session
):
    response = test_client.post(
        "/api/rate-types",
        headers={"Authorization": "token fake-token"},
        json={
            "name": "Name",
            "energy_type": "gas",
        },
    )

    assert response.status_code == 401


def test_rate_type_create_endpoint_error_power_gas(
    test_client: TestClient, token_create: Token, db_session: Session
):
    response = test_client.post(
        "/api/rate-types",
        headers={"Authorization": f"token {token_create.token}"},
        json={"name": "Name", "energy_type": "gas", "min_power": 0.0, "max_power": 0.0},
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["message"] == (
        "Power range can only be defined for electricity type"
    )


def test_rate_type_list_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    gas_rate_type: RateType,
    deleted_rate_type: RateType,
):
    response = test_client.get(
        "/api/rate-types",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 1
    assert response_data["page"] == 1
    assert response_data["size"] == 50


def test_rate_type_partial_update_endpoint_ok(
    test_client: TestClient,
    electricity_rate_type: RateType,
    db_session: Session,
    token_create: Token,
):
    response = test_client.patch(
        "/api/rate-types/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "max_power": 25.15,
            "min_power": 3.2,
            "enable": False,
            "is_deleted": True,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == "Electricity rate type"
    assert response_data["energy_type"] == "electricity"
    assert response_data["max_power"] == 25.15
    assert response_data["min_power"] == 3.2
    assert response_data["enable"] is False
    assert response_data["is_deleted"] is True


def test_rate_type_partial_update_endpoint_not_user_auth(
    test_client: TestClient,
    electricity_rate_type: RateType,
    db_session: Session,
    token_create: Token,
):
    response = test_client.patch(
        "/api/rate-types/1",
        headers={"Authorization": "token fake_token"},
        json={"max_power": 25.15, "min_power": 3.2},
    )

    assert response.status_code == 401


def test_rate_type_partial_update_endpoint_not_exists(
    test_client: TestClient,
    db_session: Session,
    token_create: Token,
):
    response = test_client.patch(
        "/api/rate-types/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={"max_power": 25.15, "min_power": 3.2},
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["message"] == "Rate type does not exist"
    assert response_data["detail"][0]["code"] == "NOT_EXIST"


def test_rate_type_partial_update_endpoint_deleted(
    test_client: TestClient,
    db_session: Session,
    deleted_rate_type: RateType,
    token_create: Token,
):
    response = test_client.patch(
        "/api/rate-types/4",
        headers={"Authorization": f"token {token_create.token}"},
        json={"max_power": 25.15, "min_power": 3.2},
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["message"] == "Rate type does not exist"
    assert response_data["detail"][0]["code"] == "NOT_EXIST"


def test_rate_type_partial_update_endpoint_power_range_ok(
    test_client: TestClient,
    electricity_rate_type: RateType,
    db_session: Session,
    token_create: Token,
):
    response = test_client.patch(
        "/api/rate-types/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={"min_power": 18.26, "max_power": 25.15},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == "Electricity rate type"
    assert response_data["max_power"] == 25.15
    assert response_data["min_power"] == 18.26


def test_rate_type_partial_update_endpoint_enable_ok(
    test_client: TestClient,
    electricity_rate_type: RateType,
    db_session: Session,
    token_create: Token,
):
    response = test_client.patch(
        "/api/rate-types/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={"enable": False},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == "Electricity rate type"
    assert response_data["enable"] is False


def test_rate_type_partial_update_endpoint_is_deleted_ok(
    test_client: TestClient,
    electricity_rate_type: RateType,
    db_session: Session,
    token_create: Token,
):
    response = test_client.patch(
        "/api/rate-types/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={"is_deleted": True},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == "Electricity rate type"
    assert response_data["is_deleted"] is True


def test_rate_type_partial_update_endpoint_readonly_field(
    test_client: TestClient,
    electricity_rate_type: RateType,
    db_session: Session,
    token_create: Token,
):
    response = test_client.patch(
        "/api/rate-types/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={"name": "Modified rate"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == "Electricity rate type"
    assert response_data["max_power"] == 30.30
    assert response_data["min_power"] == 1.5


def test_rate_type_partial_update_endpoint_invalid_power_range(
    test_client: TestClient,
    electricity_rate_type: RateType,
    db_session: Session,
    token_create: Token,
):
    response = test_client.patch(
        "/api/rate-types/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={"min_power": 50.23, "max_power": 32.23},
    )

    assert response.status_code == 422
    response_data = response.json()
    assert (
        response_data["detail"][0]["message"]
        == "min_power cannot be greater than max_power"
    )
    assert response_data["detail"][0]["code"] == "POWER_RANGE_INVALID_RANGE"


def test_rate_type_detail_endpoint_ok(
    test_client: TestClient, token_create: Token, electricity_rate_type: RateType
):
    response = test_client.get(
        "/api/rate-types/1",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == "Electricity rate type"
    assert response_data["energy_type"] == "electricity"
    assert response_data["max_power"] == 30.3
    assert response_data["min_power"] == 1.5
    assert response_data["enable"] is True
    assert response_data["is_deleted"] is False
    assert response_data["create_at"]
    assert response_data["user"]["id"] == 1
    assert response_data["user"]["first_name"] == "John"
    assert response_data["user"]["last_name"] == "Graham"
    assert response_data["user"]["email"] == "test@user.com"
    assert response_data["user"]["create_at"]
    assert response_data["user"]["is_active"] is True
    assert response_data["user"]["is_deleted"] is False


def test_rate_type_details_endpoint_not_token(test_client: TestClient):
    response = test_client.get("/api/rate-types/1")
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_AUTHENTICATED"
    assert response_data["detail"][0]["message"] == "Not authenticated"


def test_rate_type_details_endpoint_wrong_token(
    test_client: TestClient, token_create: Token
):
    response = test_client.get(
        "/api/rate-types/1", headers={"Authorization": "token faketoken"}
    )
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "INVALID_CREDENTIALS"
    assert response_data["detail"][0]["message"] == "Invalid authentication credentials"


def test_rate_type_details_endpoint_not_exist(
    test_client: TestClient, token_create: Token
):
    response = test_client.get(
        "/api/rate-types/1",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_EXIST"
    assert response_data["detail"][0]["message"] == "Rate type does not exist"


def test_rate_type_details_endpoint_deleted(
    test_client: TestClient, token_create: Token, deleted_rate_type: RateType
):
    response = test_client.get(
        "/api/rate-types/4",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_EXIST"
    assert response_data["detail"][0]["message"] == "Rate type does not exist"


def test_rate_type_power_ranges_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    electricity_rate_type: RateType,
    disable_rate_type: RateType,
):
    response = test_client.get(
        "/api/rate-types/power-ranges",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["minimum_min_power"] == 0
    assert response_data["maximum_min_power"] == 1.5
    assert response_data["minimum_max_power"] == 21.54
    assert response_data["maximum_max_power"] == 30.3


def test_rate_types_delete_rate_types_endpoint_ok(
    test_client: TestClient,
    db_session: Session,
    token_create: Token,
    electricity_rate_type: RateType,
    gas_rate_type: RateType,
    disable_rate_type: RateType,
    deleted_rate_type: RateType,
):
    response = test_client.post(
        "/api/rate-types/delete",
        headers={"Authorization": f"token {token_create.token}"},
        json={"ids": [1, 3, 125]},
    )

    assert response.status_code == 200
    assert (
        db_session.query(RateType).filter(RateType.is_deleted == false()).count() == 1
    )


def test_rate_types_delete_rate_types_endpoint_with_related_rates_ok(
    test_client: TestClient,
    db_session: Session,
    token_create: Token,
    electricity_rate_type: RateType,
    gas_rate_type: RateType,
    disable_rate_type: RateType,
    deleted_rate_type: RateType,
    electricity_rate: Rate,
    electricity_rate_2: Rate,
):
    electricity_rate_id = electricity_rate.id
    electricity_rate_2_id = electricity_rate_2.id
    response = test_client.post(
        "/api/rate-types/delete",
        headers={"Authorization": f"token {token_create.token}"},
        json={"ids": [1, 3, 125]},
    )

    electricity_rate = (
        db_session.query(Rate).filter(Rate.id == electricity_rate_id).first()
    )
    electricity_rate_2 = (
        db_session.query(Rate).filter(Rate.id == electricity_rate_2_id).first()
    )

    assert response.status_code == 200
    assert (
        db_session.query(RateType).filter(RateType.is_deleted == false()).count() == 1
    )
    assert electricity_rate.is_active is False
    assert electricity_rate_2.is_active is False


def test_rate_types_export_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    electricity_rate_type: RateType,
    gas_rate_type: RateType,
    disable_rate_type: RateType,
    deleted_rate_type: RateType,
):
    response = test_client.post(
        "/api/rate-types/export/csv",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    lines = response.text.split("\r\n")
    assert len(lines) == 5
    assert len(lines[0].split(";")) == 9
    assert len(lines[1].split(";")) == 9
    assert len(lines[2].split(";")) == 9
    assert len(lines[3].split(";")) == 9
    assert lines[4].split(";")[0] == ""
    assert response.text.startswith(
        "Id;Name;Energy type;Minimum power;Maximum power;Enable;User first name;"
        "User last name;Date\r\n3"
    )


def test_rate_create_endpoint_client_types_order_ok(
    test_client: TestClient,
    token_create: Token,
    marketer: Marketer,
    gas_rate_type: RateType,
):
    response = test_client.post(
        "/api/rates",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "gas rate",
            "price_type": "fixed_fixed",
            "client_types": [
                "particular",
                "company",
                "community_owners",
                "self-employed",
            ],
            "energy_price_1": 22.5,
            "fixed_term_price": 22.5,
            "permanency": True,
            "length": 12,
            "rate_type_id": 2,
            "marketer_id": 1,
        },
    )

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["client_types"] == [
        "community_owners",
        "company",
        "particular",
        "self-employed",
    ]


def test_rate_create_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    marketer: Marketer,
    gas_rate_type: RateType,
):
    response = test_client.post(
        "/api/rates",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "gas rate",
            "price_type": "fixed_fixed",
            "client_types": ["particular"],
            "energy_price_1": 22.5,
            "fixed_term_price": 22.5,
            "permanency": True,
            "length": 12,
            "rate_type_id": 2,
            "marketer_id": 1,
        },
    )
    assert response.status_code == 201
    assert db_session.query(Rate).count() == 1


def test_rate_create_endpoint_error_auth(
    test_client: TestClient,
    db_session: Session,
    marketer: Marketer,
    gas_rate_type: RateType,
):
    response = test_client.post(
        "/api/rates",
        headers={"Authorization": "token fake-token"},
        json={
            "name": "gas rate",
            "price_type": "fixed_fixed",
            "client_types": ["particular"],
            "energy_price_1": 22.5,
            "fixed_term_price": 22.5,
            "rate_type_id": 2,
            "marketer_id": 1,
        },
    )
    assert response.status_code == 401
    assert db_session.query(Rate).count() == 0


def test_rate_update_endpoint_ok(
    test_client: TestClient,
    electricity_rate: Rate,
    disable_rate_type: RateType,
    token_create: Token,
):
    response = test_client.put(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "New rate name",
            "client_types": ["company"],
            "rate_type_id": 3,
            "min_power": 5.8,
            "max_power": 15.36,
            "energy_price_1": 19.17,
            "energy_price_2": 9.5,
            "energy_price_3": 73.87,
            "energy_price_4": 43.2,
            "energy_price_5": 23.12,
            "energy_price_6": 55.9,
            "power_price_1": 17.19,
            "power_price_2": 5.9,
            "power_price_3": 87.73,
            "power_price_4": 2.43,
            "power_price_5": 12.23,
            "power_price_6": 9.55,
            "permanency": True,
            "length": 12,
            "is_full_renewable": False,
            "compensation_surplus": False,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == "New rate name"
    assert response_data["client_types"] == ["company"]
    assert response_data["rate_type"]["id"] == 3
    assert response_data["rate_type"]["name"] == "Disable rate type"
    assert response_data["rate_type"]["energy_type"] == "electricity"
    assert response_data["marketer"]["id"] == 1
    assert response_data["marketer"]["name"] == "Marketer"
    assert response_data["min_power"] == 5.8
    assert response_data["max_power"] == 15.36
    assert response_data["energy_price_1"] == 19.17
    assert response_data["energy_price_2"] == 9.5
    assert response_data["energy_price_3"] == 73.87
    assert response_data["energy_price_4"] == 43.2
    assert response_data["energy_price_5"] == 23.12
    assert response_data["energy_price_6"] == 55.9
    assert response_data["power_price_1"] == 17.19
    assert response_data["power_price_2"] == 5.9
    assert response_data["power_price_3"] == 87.73
    assert response_data["power_price_4"] == 2.43
    assert response_data["power_price_5"] == 12.23
    assert response_data["power_price_6"] == 9.55
    assert response_data["permanency"] is True
    assert response_data["length"] == 12
    assert response_data["is_full_renewable"] is False
    assert response_data["compensation_surplus"] is False
    assert response_data["compensation_surplus_value"] is None


def test_rate_update_endpoint_gas_rate_ok(
    test_client: TestClient,
    gas_rate: Rate,
    gas_rate_type_2: RateType,
    token_create: Token,
):
    response = test_client.put(
        "/api/rates/2",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "New rate name",
            "client_types": ["company"],
            "rate_type_id": 5,
            "min_consumption": 5.8,
            "max_consumption": 15.36,
            "energy_price_1": 19.17,
            "fixed_term_price": 36.63,
            "permanency": False,
            "length": 7,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == "New rate name"
    assert response_data["client_types"] == ["company"]
    assert response_data["rate_type"]["id"] == 5
    assert response_data["rate_type"]["name"] == "Gas rate type 2"
    assert response_data["rate_type"]["energy_type"] == "gas"
    assert response_data["marketer"]["id"] == 1
    assert response_data["marketer"]["name"] == "Marketer"
    assert response_data["min_consumption"] == 5.8
    assert response_data["max_consumption"] == 15.36
    assert response_data["energy_price_1"] == 19.17
    assert response_data["fixed_term_price"] == 36.63
    assert response_data["permanency"] is False
    assert response_data["length"] == 7


def test_rate_update_endpoint_not_user_auth(
    test_client: TestClient,
    electricity_rate: Rate,
    token_create: Token,
):
    response = test_client.put(
        "/api/rates/1",
        headers={"Authorization": "token fake_token"},
        json={
            "name": "New rate name",
            "client_types": ["company"],
            "rate_type_id": 1,
            "energy_price_1": 17.19,
            "permanency": False,
            "length": 7,
            "is_full_renewable": False,
        },
    )

    assert response.status_code == 401


def test_rate_update_endpoint_not_exists(
    test_client: TestClient,
    token_create: Token,
):
    response = test_client.put(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "New rate name",
            "client_types": ["company"],
            "rate_type_id": 1,
            "energy_price_1": 17.19,
            "permanency": False,
            "length": 7,
            "is_full_renewable": False,
        },
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["message"] == "Rate does not exist"
    assert response_data["detail"][0]["code"] == "NOT_EXIST"


def test_rate_update_endpoint_deleted(
    test_client: TestClient,
    token_create: Token,
    electricity_rate: Rate,
):
    electricity_rate.is_deleted = True

    response = test_client.put(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "New rate name",
            "client_types": ["company"],
            "rate_type_id": 1,
            "energy_price_1": 17.19,
            "permanency": False,
            "length": 7,
            "is_full_renewable": False,
        },
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["message"] == "Rate does not exist"
    assert response_data["detail"][0]["code"] == "NOT_EXIST"


def test_rate_update_endpoint_required_fields_ok(
    test_client: TestClient,
    electricity_rate: Rate,
    token_create: Token,
):
    response = test_client.put(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "New rate name",
            "client_types": ["particular"],
            "rate_type_id": 1,
            "energy_price_1": 17.19,
            "permanency": False,
            "length": 7,
            "is_full_renewable": False,
        },
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == "New rate name"
    assert response_data["client_types"] == ["particular"]
    assert response_data["rate_type"]["id"] == 1
    assert response_data["energy_price_1"] == 17.19
    assert response_data["permanency"] is False
    assert response_data["length"] == 7
    assert response_data["is_full_renewable"] is False


def test_rate_update_endpoint_min_power_ok(
    test_client: TestClient,
    electricity_rate: Rate,
    token_create: Token,
):
    response = test_client.put(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Electricity rate",
            "client_types": ["particular"],
            "rate_type_id": 1,
            "energy_price_1": 17.19,
            "min_power": 5.8,
            "max_power": 23.39,
            "permanency": False,
            "length": 7,
            "is_full_renewable": False,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["min_power"] == 5.8
    assert response_data["min_power"] == 5.8


def test_rate_update_endpoint_max_power_ok(
    test_client: TestClient,
    electricity_rate: Rate,
    token_create: Token,
):
    response = test_client.put(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Electricity rate",
            "client_types": ["particular"],
            "rate_type_id": 1,
            "energy_price_1": 10.5,
            "min_power": 10.5,
            "max_power": 15.36,
            "permanency": False,
            "length": 7,
            "is_full_renewable": False,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["max_power"] == 15.36


def test_rate_update_endpoint_energy_price_1_ok(
    test_client: TestClient,
    electricity_rate: Rate,
    token_create: Token,
):
    response = test_client.put(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Electricity rate",
            "client_types": ["particular"],
            "rate_type_id": 1,
            "energy_price_1": 19.17,
            "permanency": False,
            "length": 7,
            "is_full_renewable": False,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["energy_price_1"] == 19.17


def test_rate_update_endpoint_energy_price_2_ok(
    test_client: TestClient,
    electricity_rate: Rate,
    token_create: Token,
):
    response = test_client.put(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Electricity rate",
            "client_types": ["particular"],
            "rate_type_id": 1,
            "energy_price_1": 10.5,
            "energy_price_2": 9.5,
            "permanency": False,
            "length": 7,
            "is_full_renewable": False,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["energy_price_2"] == 9.5


def test_rate_update_endpoint_energy_price_3_ok(
    test_client: TestClient,
    electricity_rate: Rate,
    token_create: Token,
):
    response = test_client.put(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Electricity rate",
            "client_types": ["particular"],
            "rate_type_id": 1,
            "energy_price_1": 10.5,
            "energy_price_3": 73.87,
            "permanency": False,
            "length": 7,
            "is_full_renewable": False,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["energy_price_3"] == 73.87


def test_rate_update_endpoint_energy_price_4_ok(
    test_client: TestClient,
    electricity_rate: Rate,
    token_create: Token,
):
    response = test_client.put(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Electricity rate",
            "client_types": ["particular"],
            "rate_type_id": 1,
            "energy_price_1": 10.5,
            "energy_price_4": 43.2,
            "permanency": False,
            "length": 7,
            "is_full_renewable": False,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["energy_price_4"] == 43.2


def test_rate_update_endpoint_energy_price_5_ok(
    test_client: TestClient,
    electricity_rate: Rate,
    token_create: Token,
):
    response = test_client.put(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Electricity rate",
            "client_types": ["particular"],
            "rate_type_id": 1,
            "energy_price_1": 10.5,
            "energy_price_5": 23.12,
            "permanency": False,
            "length": 7,
            "is_full_renewable": False,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["energy_price_5"] == 23.12


def test_rate_update_endpoint_energy_price_6_ok(
    test_client: TestClient,
    electricity_rate: Rate,
    token_create: Token,
):
    response = test_client.put(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Electricity rate",
            "client_types": ["particular"],
            "rate_type_id": 1,
            "energy_price_1": 10.5,
            "energy_price_6": 55.9,
            "permanency": False,
            "length": 7,
            "is_full_renewable": False,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["energy_price_6"] == 55.9


def test_rate_update_endpoint_power_price_1_ok(
    test_client: TestClient,
    electricity_rate: Rate,
    token_create: Token,
):
    response = test_client.put(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Electricity rate",
            "client_types": ["particular"],
            "rate_type_id": 1,
            "energy_price_1": 10.5,
            "power_price_1": 17.19,
            "permanency": False,
            "length": 7,
            "is_full_renewable": False,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["power_price_1"] == 17.19


def test_rate_update_endpoint_power_price_2_ok(
    test_client: TestClient,
    electricity_rate: Rate,
    token_create: Token,
):
    response = test_client.put(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Electricity rate",
            "client_types": ["particular"],
            "rate_type_id": 1,
            "energy_price_1": 10.5,
            "power_price_2": 5.9,
            "permanency": False,
            "length": 7,
            "is_full_renewable": False,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["power_price_2"] == 5.9


def test_rate_update_endpoint_power_price_3_ok(
    test_client: TestClient,
    electricity_rate: Rate,
    token_create: Token,
):
    response = test_client.put(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Electricity rate",
            "client_types": ["particular"],
            "rate_type_id": 1,
            "energy_price_1": 10.5,
            "power_price_3": 87.73,
            "permanency": False,
            "length": 7,
            "is_full_renewable": False,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["power_price_3"] == 87.73


def test_rate_update_endpoint_power_price_4_ok(
    test_client: TestClient,
    electricity_rate: Rate,
    token_create: Token,
):
    response = test_client.put(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Electricity rate",
            "client_types": ["particular"],
            "rate_type_id": 1,
            "energy_price_1": 10.5,
            "power_price_4": 2.43,
            "permanency": False,
            "length": 7,
            "is_full_renewable": False,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["power_price_4"] == 2.43


def test_rate_update_endpoint_power_price_5_ok(
    test_client: TestClient,
    electricity_rate: Rate,
    token_create: Token,
):
    response = test_client.put(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Electricity rate",
            "client_types": ["particular"],
            "rate_type_id": 1,
            "energy_price_1": 10.5,
            "power_price_5": 12.23,
            "permanency": False,
            "length": 7,
            "is_full_renewable": False,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["power_price_5"] == 12.23


def test_rate_update_endpoint_power_price_6_ok(
    test_client: TestClient,
    electricity_rate: Rate,
    token_create: Token,
):
    response = test_client.put(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Electricity rate",
            "client_types": ["particular"],
            "rate_type_id": 1,
            "energy_price_1": 10.5,
            "power_price_6": 9.55,
            "permanency": False,
            "length": 7,
            "is_full_renewable": False,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["power_price_6"] == 9.55


def test_rate_partial_update_endpoint_compensation_surplus_ok(
    test_client: TestClient,
    electricity_rate: Rate,
    token_create: Token,
):
    response = test_client.put(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Electricity rate",
            "client_types": ["particular"],
            "rate_type_id": 1,
            "energy_price_1": 10.5,
            "permanency": False,
            "length": 7,
            "is_full_renewable": False,
            "compensation_surplus": False,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["compensation_surplus"] is False
    assert not response_data["compensation_surplus_value"]


def test_rate_partial_update_endpoint_compensation_surplus_value_ok(
    test_client: TestClient,
    electricity_rate: Rate,
    token_create: Token,
):
    response = test_client.put(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Electricity rate",
            "client_types": ["particular"],
            "rate_type_id": 1,
            "energy_price_1": 10.5,
            "permanency": False,
            "length": 7,
            "is_full_renewable": False,
            "compensation_surplus": True,
            "compensation_surplus_value": 82.23,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["compensation_surplus_value"] == 82.23


def test_rate_update_endpoint_one_of_two_fields_ok(
    test_client: TestClient,
    electricity_rate: Rate,
    db_session: Session,
    token_create: Token,
):
    response = test_client.put(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "New rate name",
            "client_types": ["particular"],
            "rate_type_id": 1,
            "energy_price_1": 10.5,
            "permanency": False,
            "length": 7,
            "is_full_renewable": False,
            "fixed_term_price": 22.3,
        },
    )

    assert response.status_code == 200
    rate = get_rate_by(db_session, Rate.id == 1)
    assert rate.name == "New rate name"
    assert not rate.fixed_term_price


def test_rate_partial_update_endpoint_is_deleted_ok(
    test_client: TestClient,
    db_session: Session,
    electricity_rate: Rate,
    token_create: Token,
):
    response = test_client.patch(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "is_deleted": True,
        },
    )

    assert response.status_code == 200
    rate = db_session.query(Rate).filter(Rate.id == 1).first()
    assert rate.is_deleted is True


def test_rate_partial_update_endpoint_is_active_ok(
    test_client: TestClient,
    electricity_rate: Rate,
    token_create: Token,
):
    response = test_client.patch(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["is_active"] is False


def test_rate_list_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    electricity_rate: Rate,
    gas_rate_deleted: Rate,
):
    response = test_client.get(
        "/api/rates",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 1
    assert response_data["page"] == 1
    assert response_data["size"] == 50
    assert len(response_data["items"]) == 1
    assert response_data["items"][0]["id"] == 1
    assert response_data["items"][0]["name"] == "Electricity rate"
    assert response_data["items"][0]["price_type"] == "fixed_fixed"
    assert response_data["items"][0]["client_types"] == ["particular"]
    assert response_data["items"][0]["min_power"] == 10.5
    assert response_data["items"][0]["max_power"] == 23.39
    assert response_data["items"][0]["energy_price_1"] == 17.19
    assert response_data["items"][0]["energy_price_2"] == 5.9
    assert response_data["items"][0]["energy_price_3"] == 87.73
    assert response_data["items"][0]["energy_price_4"] == 2.43
    assert response_data["items"][0]["energy_price_5"] == 12.23
    assert response_data["items"][0]["energy_price_6"] == 9.55
    assert response_data["items"][0]["power_price_1"] == 19.17
    assert response_data["items"][0]["power_price_2"] == 9.5
    assert response_data["items"][0]["power_price_3"] == 73.87
    assert response_data["items"][0]["power_price_4"] == 43.2
    assert response_data["items"][0]["power_price_5"] == 23.12
    assert response_data["items"][0]["power_price_6"] == 55.9
    assert response_data["items"][0]["permanency"] is True
    assert response_data["items"][0]["length"] == 12
    assert response_data["items"][0]["is_full_renewable"] is True
    assert response_data["items"][0]["compensation_surplus"] is True
    assert response_data["items"][0]["compensation_surplus_value"] == 28.32
    assert response_data["items"][0]["rate_type"]["id"] == 1
    assert response_data["items"][0]["rate_type"]["name"] == "Electricity rate type"
    assert response_data["items"][0]["rate_type"]["energy_type"] == "electricity"
    assert response_data["items"][0]["marketer"]["id"] == 1
    assert response_data["items"][0]["marketer"]["name"] == "Marketer"
    assert response_data["items"][0]["is_active"] is True
    assert response_data["items"][0]["create_at"]


def test_rate_list_endpoint_sort_by_ok(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    electricity_rate: Rate,
    gas_rate: Rate,
):
    response = test_client.get(
        "/api/rates?order_by=-name",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 2
    assert response_data["items"][0]["name"] == "Gas rate name"
    assert response_data["items"][1]["name"] == "Electricity rate"


def test_rate_list_endpoint_filter_user_first_name_ok(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    electricity_rate: Rate,
    gas_rate: Rate,
):
    response = test_client.get(
        "/api/rates?rate_type__name__unaccent=elÉc",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 1
    assert response_data["items"][0]["rate_type"]["name"] == "Electricity rate type"


def test_rate_list_endpoint_filter_client_types_ok(
    test_client: TestClient,
    token_create: Token,
    electricity_rate: Rate,
    electricity_rate_2: Rate,
    gas_rate: Rate,
):
    """
    All rates have are for particular except "electricity_rate_2" that also include
    "self-employed" in client_types
    """

    response = test_client.get(
        "/api/rates?client_types__contains=self-employed",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 1
    assert response_data["items"][0]["name"] == "Electricity rate 2"
    assert response_data["items"][0]["rate_type"]["name"] == "Electricity rate type"
    assert response_data["items"][0]["client_types"] == ["particular", "self-employed"]


def test_rates_details_endpoint_ok(
    test_client: TestClient, token_create: Token, electricity_rate: Rate
):
    response = test_client.get(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == 1
    assert response_data["name"] == "Electricity rate"
    assert response_data["price_type"] == "fixed_fixed"
    assert response_data["client_types"] == ["particular"]
    assert response_data["min_power"] == 10.5
    assert response_data["max_power"] == 23.39
    assert response_data["min_consumption"] == 12.5
    assert response_data["max_consumption"] == 23.39
    assert response_data["energy_price_1"] == 17.19
    assert response_data["energy_price_2"] == 5.9
    assert response_data["energy_price_3"] == 87.73
    assert response_data["energy_price_4"] == 2.43
    assert response_data["energy_price_5"] == 12.23
    assert response_data["energy_price_6"] == 9.55
    assert response_data["power_price_1"] == 19.17
    assert response_data["power_price_2"] == 9.5
    assert response_data["power_price_3"] == 73.87
    assert response_data["power_price_4"] == 43.2
    assert response_data["power_price_5"] == 23.12
    assert response_data["power_price_6"] == 55.9
    assert response_data["permanency"] is True
    assert response_data["length"] == 12
    assert response_data["is_full_renewable"] is True
    assert response_data["compensation_surplus"] is True
    assert response_data["compensation_surplus_value"] == 28.32
    assert not response_data["fixed_term_price"]
    assert response_data["rate_type"]["id"] == 1
    assert response_data["rate_type"]["name"] == "Electricity rate type"
    assert response_data["rate_type"]["energy_type"] == "electricity"
    assert response_data["marketer"]["id"] == 1
    assert response_data["marketer"]["name"] == "Marketer"
    assert response_data["is_active"] is True
    assert response_data["create_at"]


def test_rates_details_endpoint_not_token(test_client: TestClient):
    response = test_client.get("/api/rates/1")
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_AUTHENTICATED"
    assert response_data["detail"][0]["message"] == "Not authenticated"


def test_rates_details_endpoint_wrong_token(
    test_client: TestClient, token_create: Token
):
    response = test_client.get(
        "/api/rates/1", headers={"Authorization": "token faketoken"}
    )
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "INVALID_CREDENTIALS"
    assert response_data["detail"][0]["message"] == "Invalid authentication credentials"


def test_rates_details_endpoint_not_exist(test_client: TestClient, token_create: Token):
    response = test_client.get(
        "/api/rates/1",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_EXIST"
    assert response_data["detail"][0]["message"] == "Rate does not exist"


def test_rates_details_endpoint_deleted(
    test_client: TestClient, token_create: Token, gas_rate_deleted: Rate
):
    response = test_client.get(
        "/api/rates/4",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_EXIST"
    assert response_data["detail"][0]["message"] == "Rate does not exist"


def test_rates_delete_rates_endpoint_ok(
    test_client: TestClient,
    db_session: Session,
    token_create: Token,
    electricity_rate: Rate,
    electricity_rate_2: Rate,
    gas_rate: Rate,
    gas_rate_deleted: Rate,
):
    response = test_client.post(
        "/api/rates/delete",
        headers={"Authorization": f"token {token_create.token}"},
        json={"ids": [1, 4, 125]},
    )

    assert response.status_code == 200
    assert db_session.query(Rate).filter(Rate.is_deleted == false()).count() == 1


def test_rates_delete_rates_endpoint_with_related_objects_ok(
    test_client: TestClient,
    db_session: Session,
    token_create: Token,
    electricity_rate: Rate,
    electricity_rate_2: Rate,
    gas_rate: Rate,
    gas_rate_deleted: Rate,
    commission: Commission,
    commission_2: Commission,
    other_cost: OtherCost,
    other_cost_2_rates: OtherCost,
):
    commission_2.rates.append(electricity_rate_2)
    other_cost_2_rates.rates.append(gas_rate)
    db_session.commit()
    db_session.refresh(commission_2)
    db_session.refresh(other_cost_2_rates)

    commission_id = commission.id
    commission_2_id = commission_2.id
    other_cost_id = other_cost.id
    other_cost_2_rates_id = other_cost_2_rates.id

    response = test_client.post(
        "/api/rates/delete",
        headers={"Authorization": f"token {token_create.token}"},
        json={"ids": [1, 2, 125]},
    )

    commission = (
        db_session.query(Commission).filter(Commission.id == commission_id).first()
    )
    commission_2 = (
        db_session.query(Commission).filter(Commission.id == commission_2_id).first()
    )

    other_cost = (
        db_session.query(OtherCost).filter(OtherCost.id == other_cost_id).first()
    )
    other_cost_2_rates = (
        db_session.query(OtherCost)
        .filter(OtherCost.id == other_cost_2_rates_id)
        .first()
    )

    assert response.status_code == 200
    assert db_session.query(Rate).filter(Rate.is_deleted == false()).count() == 1

    assert commission.is_deleted is True
    assert len(commission.rates) == 0
    assert commission_2.is_deleted is False
    assert len(commission_2.rates) == 1

    assert other_cost.is_deleted is True
    assert len(other_cost.rates) == 0
    assert other_cost_2_rates.is_deleted is False
    assert len(other_cost_2_rates.rates) == 1


def test_rates_export_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    electricity_rate: Rate,
    electricity_rate_2: Rate,
    gas_rate: Rate,
    gas_rate_deleted: Rate,
):
    response = test_client.post(
        "/api/rates/export/csv",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    lines = response.text.split("\r\n")
    assert len(lines) == 5
    assert len(lines[0].split(";")) == 29
    assert len(lines[1].split(";")) == 29
    assert len(lines[2].split(";")) == 29
    assert len(lines[3].split(";")) == 29
    assert lines[4].split(";")[0] == ""
    assert response.text.startswith(
        "Name;Price type;Client types;Rate type;energy type;Minimum power;"
        "Maximum power;Minimum consumption;Maximum consumption;Energy price 1;"
        "Energy price 2;Energy price 3;Energy price 4;Energy price 5;"
        "Energy price 6;Power price 1;Power price 2;Power price 3;Power price 4;"
        "Power price 5;Power price 6;Fixed term price;Permanency;Length;"
        "Is full renewable;Compensation surplus;Compensation surplus value;"
        "Status;Date\r\n"
    )
