from sqlalchemy import false
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from src.infrastructure.sqlalchemy.costs import get_energy_cost_by
from src.modules.costs.models import EnergyCost, OtherCost
from src.modules.rates.models import Rate
from src.modules.users.models import Token, User


def test_energy_cost_create_endpoint_ok(
    test_client: TestClient, token_create: Token, db_session: Session
):
    response = test_client.post(
        "/api/energy-costs",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "concept": "Concept",
            "amount": 23.68,
        },
    )

    assert response.status_code == 201
    assert db_session.query(EnergyCost).count() == 1


def test_energy_cost_create_endpoint_error_auth(
    test_client: TestClient, db_session: Session
):
    response = test_client.post(
        "/api/energy-costs",
        headers={"Authorization": "token fake-token"},
        json={
            "concept": "Concept",
            "amount": 23.68,
        },
    )

    assert response.status_code == 401
    assert db_session.query(EnergyCost).count() == 0


def test_energy_cost_create_endpoint_error_invalid_amount(
    test_client: TestClient, token_create: Token, db_session: Session
):
    response = test_client.post(
        "/api/energy-costs",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "concept": "New concept",
            "amount": -23.68,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["message"] == (
        "ensure this value is greater than or equal to 0"
    )


def test_energy_costs_list_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    energy_cost: EnergyCost,
    energy_cost_deleted: EnergyCost,
):
    response = test_client.get(
        "/api/energy-costs",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 1
    assert response_data["page"] == 1
    assert response_data["size"] == 50
    assert len(response_data["items"]) == 1
    assert response_data["items"][0]["concept"] == "gas installation"
    assert response_data["items"][0]["amount"] == 56.28


def test_energy_costs_list_endpoint_sort_by_ok(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    energy_cost: EnergyCost,
    energy_cost2: EnergyCost,
):
    response = test_client.get(
        "/api/energy-costs?order_by=-concept",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 2
    assert response_data["items"][0]["id"] < response_data["items"][1]["id"]


def test_energy_costs_list_endpoint_filter_user_first_name_ok(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    energy_cost: EnergyCost,
    energy_cost2: EnergyCost,
):
    response = test_client.get(
        "/api/energy-costs?user__first_name__unaccent=óhNa",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 1
    assert response_data["items"][0]["user"]["first_name"] == "Johnathan"


def test_energy_cost_partial_update_endpoint_ok(
    test_client: TestClient,
    energy_cost: EnergyCost,
    db_session: Session,
    token_create: Token,
):
    response = test_client.patch(
        "/api/energy-costs/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "concept": "New concept",
            "amount": 15.3,
            "is_active": False,
            "is_deleted": True,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["concept"] == "New concept"
    assert response_data["amount"] == 15.3
    assert response_data["is_active"] is False
    assert response_data["is_deleted"] is True
    assert response_data["is_protected"] is False


def test_energy_cost_partial_update_endpoint_not_user_auth(
    test_client: TestClient,
    energy_cost: EnergyCost,
    db_session: Session,
    token_create: Token,
):
    response = test_client.patch(
        "/api/energy-costs/1",
        headers={"Authorization": "token fake_token"},
        json={"concept": "New concept", "amount": 15.3},
    )

    assert response.status_code == 401


def test_energy_cost_partial_update_endpoint_not_exists(
    test_client: TestClient,
    db_session: Session,
    token_create: Token,
):
    response = test_client.patch(
        "/api/energy-costs/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={"concept": "New concept", "amount": 15.3},
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["message"] == "Energy cost does not exist"
    assert response_data["detail"][0]["code"] == "NOT_EXIST"


def test_energy_cost_partial_update_endpoint_deleted(
    test_client: TestClient,
    db_session: Session,
    token_create: Token,
    energy_cost_deleted: EnergyCost,
):
    response = test_client.patch(
        "/api/energy-costs/4",
        headers={"Authorization": f"token {token_create.token}"},
        json={"concept": "New concept", "amount": 15.3},
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["message"] == "Energy cost does not exist"
    assert response_data["detail"][0]["code"] == "NOT_EXIST"


def test_energy_cost_partial_update_endpoint_concept_ok(
    test_client: TestClient,
    energy_cost: EnergyCost,
    db_session: Session,
    token_create: Token,
):
    response = test_client.patch(
        "/api/energy-costs/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={"concept": "New concept"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["concept"] == "New concept"


def test_energy_cost_partial_update_endpoint_concept_is_protected_error(
    test_client: TestClient,
    energy_cost_protected: EnergyCost,
    db_session: Session,
    token_create: Token,
):
    response = test_client.patch(
        "/api/energy-costs/3",
        headers={"Authorization": f"token {token_create.token}"},
        json={"concept": "New concept"},
    )

    assert response.status_code == 403
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "ENERGY_COST_MODIFICATION_NOT_ALLOWED"
    assert (
        response_data["detail"][0]["message"]
        == "Modify energy cost without user is not allowed"
    )


def test_energy_cost_partial_update_endpoint_concept_is_protected_superadmin_ok(
    test_client: TestClient,
    energy_cost_protected: EnergyCost,
    db_session: Session,
    token_superadmin: Token,
):
    response = test_client.patch(
        "/api/energy-costs/3",
        headers={"Authorization": f"token {token_superadmin.token}"},
        json={"concept": "New concept"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["concept"] == "New concept"


def test_energy_cost_partial_update_endpoint_amount_ok(
    test_client: TestClient,
    energy_cost: EnergyCost,
    db_session: Session,
    token_create: Token,
):
    response = test_client.patch(
        "/api/energy-costs/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={"amount": 15.3},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["amount"] == 15.3


def test_energy_cost_partial_update_endpoint_amount_is_protected_ok(
    test_client: TestClient,
    energy_cost_protected: EnergyCost,
    db_session: Session,
    token_create: Token,
):
    response = test_client.patch(
        "/api/energy-costs/3",
        headers={"Authorization": f"token {token_create.token}"},
        json={"amount": 15.3},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["amount"] == 15.3


def test_energy_cost_partial_update_endpoint_is_active_ok(
    test_client: TestClient,
    energy_cost: EnergyCost,
    db_session: Session,
    token_create: Token,
):
    response = test_client.patch(
        "/api/energy-costs/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={"is_active": False},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["is_active"] is False


def test_energy_cost_partial_update_endpoint_is_active_is_protected_ok(
    test_client: TestClient,
    energy_cost_protected: EnergyCost,
    db_session: Session,
    token_create: Token,
):
    response = test_client.patch(
        "/api/energy-costs/3",
        headers={"Authorization": f"token {token_create.token}"},
        json={"is_active": False},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["is_active"] is False


def test_energy_cost_partial_update_endpoint_is_deleted_ok(
    test_client: TestClient,
    energy_cost: EnergyCost,
    db_session: Session,
    token_create: Token,
):
    response = test_client.patch(
        "/api/energy-costs/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={"is_deleted": True},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["is_deleted"] is True


def test_energy_cost_partial_update_endpoint_is_deleted_is_protected_superadmin_ok(
    test_client: TestClient,
    energy_cost_protected: EnergyCost,
    db_session: Session,
    token_superadmin: Token,
):
    response = test_client.patch(
        "/api/energy-costs/3",
        headers={"Authorization": f"token {token_superadmin.token}"},
        json={"is_deleted": True},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["is_deleted"] is True


def test_energy_cost_partial_update_endpoint_is_deleted_is_protected_error(
    test_client: TestClient,
    energy_cost_protected: EnergyCost,
    db_session: Session,
    token_create: Token,
):
    response = test_client.patch(
        "/api/energy-costs/3",
        headers={"Authorization": f"token {token_create.token}"},
        json={"is_deleted": True},
    )

    assert response.status_code == 403
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "ENERGY_COST_MODIFICATION_NOT_ALLOWED"
    assert (
        response_data["detail"][0]["message"]
        == "Modify energy cost without user is not allowed"
    )


def test_energy_cost_partial_update_endpoint_user(
    test_client: TestClient,
    energy_cost: EnergyCost,
    db_session: Session,
    user_create2: User,
    token_create: Token,
):
    response = test_client.patch(
        "/api/energy-costs/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={"user_id": 2},
    )

    assert response.status_code == 200
    energy_cost = get_energy_cost_by(db_session, EnergyCost.id == 1)
    assert energy_cost.user_id == 1


def test_energy_cost_partial_update_endpoint_one_of_two_fields_ok(
    test_client: TestClient,
    energy_cost: EnergyCost,
    db_session: Session,
    user_create2: User,
    token_create: Token,
):
    response = test_client.patch(
        "/api/energy-costs/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={"user_id": 2, "concept": "New concept"},
    )

    assert response.status_code == 200
    energy_cost = get_energy_cost_by(db_session, EnergyCost.id == 1)
    assert energy_cost.user_id == 1
    assert energy_cost.concept == "New concept"


def test_energy_cost_partial_update_endpoint_invalid_amount(
    test_client: TestClient,
    energy_cost: EnergyCost,
    db_session: Session,
    token_create: Token,
):
    response = test_client.patch(
        "/api/energy-costs/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={"amount": -50.23},
    )

    assert response.status_code == 422
    response_data = response.json()
    assert (
        response_data["detail"][0]["message"]
        == "ensure this value is greater than or equal to 0"
    )


def test_energy_cost_partial_update_endpoint_delete_protected_cost_ok(
    test_client: TestClient,
    energy_cost_protected: EnergyCost,
    db_session: Session,
    token_superadmin: Token,
):
    response = test_client.patch(
        "/api/energy-costs/3",
        headers={"Authorization": f"token {token_superadmin.token}"},
        json={"is_deleted": True},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["is_deleted"] is True


def test_energy_cost_partial_update_endpoint_delete_protected_cost_error(
    test_client: TestClient,
    energy_cost_protected: EnergyCost,
    db_session: Session,
    token_create: Token,
):
    response = test_client.patch(
        "/api/energy-costs/3",
        headers={"Authorization": f"token {token_create.token}"},
        json={"is_deleted": True},
    )

    assert response.status_code == 403

    response_data = response.json()
    assert response_data["detail"][0]["code"] == "ENERGY_COST_MODIFICATION_NOT_ALLOWED"
    assert (
        response_data["detail"][0]["message"]
        == "Modify energy cost without user is not allowed"
    )


def test_energy_costs_detail_endpoint_ok(
    test_client: TestClient, token_create: Token, energy_cost: EnergyCost
):
    response = test_client.get(
        "/api/energy-costs/1",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == 1
    assert response_data["concept"] == "gas installation"
    assert response_data["amount"] == 56.28
    assert response_data["is_active"] is True
    assert response_data["is_deleted"] is False
    assert response_data["is_protected"] is False
    assert response_data["create_at"]
    assert response_data["user"]["id"] == 1
    assert response_data["user"]["first_name"] == "John"
    assert response_data["user"]["last_name"] == "Graham"
    assert response_data["user"]["email"] == "test@user.com"
    assert response_data["user"]["create_at"]
    assert response_data["user"]["is_active"] is True
    assert response_data["user"]["is_deleted"] is False


def test_energy_costs_details_endpoint_not_token(test_client: TestClient):
    response = test_client.get("/api/energy-costs/1")
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_AUTHENTICATED"
    assert response_data["detail"][0]["message"] == "Not authenticated"


def test_energy_costs_details_endpoint_wrong_token(
    test_client: TestClient, token_create: Token
):
    response = test_client.get(
        "/api/energy-costs/1", headers={"Authorization": "token faketoken"}
    )
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "INVALID_CREDENTIALS"
    assert response_data["detail"][0]["message"] == "Invalid authentication credentials"


def test_energy_costs_details_endpoint_not_exist(
    test_client: TestClient, token_create: Token
):
    response = test_client.get(
        "/api/energy-costs/1",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_EXIST"
    assert response_data["detail"][0]["message"] == "Energy cost does not exist"


def test_energy_costs_details_endpoint_deleted(
    test_client: TestClient, token_create: Token, energy_cost_deleted: EnergyCost
):
    response = test_client.get(
        "/api/energy-costs/4",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_EXIST"
    assert response_data["detail"][0]["message"] == "Energy cost does not exist"


def test_energy_costs_amount_ranges_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    energy_cost: EnergyCost,
    energy_cost2: EnergyCost,
):
    response = test_client.get(
        "/api/energy-costs/amount-range",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["minimum_amount"] == 26.32
    assert response_data["maximum_amount"] == 56.28


def test_energy_cost_delete_energy_cost_endpoint_ok(
    test_client: TestClient,
    db_session: Session,
    token_create: Token,
    energy_cost: EnergyCost,
    energy_cost2: EnergyCost,
    energy_cost_protected: EnergyCost,
    energy_cost_deleted: EnergyCost,
):
    """
    energy_cost: 1
    energy_cost2: 2
    energy_cost_protected: 3
    energy_cost_deleted: 4
    """
    response = test_client.post(
        "/api/energy-costs/delete",
        headers={"Authorization": f"token {token_create.token}"},
        json={"ids": [1, 2, 3, 125]},
    )

    assert response.status_code == 200
    assert (
        db_session.query(EnergyCost).filter(EnergyCost.is_deleted == false()).count()
        == 1
    )


def test_energy_cost_delete_energy_cost_endpoint_superadmin_ok(
    test_client: TestClient,
    db_session: Session,
    token_superadmin: Token,
    energy_cost: EnergyCost,
    energy_cost2: EnergyCost,
    energy_cost_protected: EnergyCost,
    energy_cost_deleted: EnergyCost,
):
    """
    energy_cost: 1
    energy_cost2: 2
    energy_cost_protected: 3
    energy_cost_deleted: 4
    """
    response = test_client.post(
        "/api/energy-costs/delete",
        headers={"Authorization": f"token {token_superadmin.token}"},
        json={"ids": [1, 2, 3, 125]},
    )

    assert response.status_code == 200
    assert (
        db_session.query(EnergyCost).filter(EnergyCost.is_deleted == false()).count()
        == 0
    )


def test_energy_costs_export_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    energy_cost: EnergyCost,
    energy_cost2: EnergyCost,
    energy_cost_protected: EnergyCost,
    energy_cost_deleted: EnergyCost,
):
    response = test_client.post(
        "/api/energy-costs/export/csv",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    lines = response.text.split("\r\n")
    assert len(lines) == 5
    assert len(lines[0].split(";")) == 7
    assert len(lines[1].split(";")) == 7
    assert len(lines[2].split(";")) == 7
    assert len(lines[3].split(";")) == 7
    assert lines[4].split(";")[0] == ""
    assert response.text.startswith(
        "Id;Concept;Amount;Is active;User first name;User last name;Date\r\n3;"
    )


def test_other_cost_create_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    electricity_rate: Rate,
):
    response = test_client.post(
        "/api/costs",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Other cost",
            "mandatory": True,
            "client_types": ["particular", "company"],
            "min_power": 3.5,
            "max_power": 23.5,
            "type": "eur/month",
            "quantity": 32,
            "extra_fee": 17.1,
            "rates": [1],
        },
    )
    assert response.status_code == 201
    assert db_session.query(OtherCost).count() == 1


def test_other_cost_create_endpoint_error_auth(
    test_client: TestClient,
    db_session: Session,
    electricity_rate: Rate,
):
    response = test_client.post(
        "/api/costs",
        headers={"Authorization": "token fake-token"},
        json={
            "name": "Other cost",
            "mandatory": True,
            "client_types": ["particular", "company"],
            "min_power": 3.5,
            "max_power": 23.5,
            "type": "eur/month",
            "quantity": 32,
            "extra_fee": 17.1,
            "rates": [1],
        },
    )
    assert response.status_code == 401
    assert db_session.query(OtherCost).count() == 0


def test_other_cost_update_endpoint_ok(
    test_client: TestClient,
    other_cost: OtherCost,
    token_create: Token,
    electricity_rate_2: Rate,
):
    response = test_client.put(
        "/api/costs/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Modified cost",
            "mandatory": False,
            "client_types": ["company"],
            "min_power": 56.65,
            "max_power": 65.56,
            "type": "percentage",
            "quantity": 16.28,
            "extra_fee": 33.33,
            "rates": [4],
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == 1
    assert response_data["name"] == "Modified cost"
    assert response_data["mandatory"] is False
    assert response_data["client_types"] == ["company"]
    assert response_data["min_power"] == 56.65
    assert response_data["max_power"] == 65.56
    assert response_data["type"] == "percentage"
    assert response_data["quantity"] == 16.28
    assert response_data["extra_fee"] == 33.33
    assert response_data["is_active"] is True
    assert response_data["is_deleted"] is False
    assert response_data["create_at"]
    assert response_data["rates"][0]["id"] == 4
    assert response_data["rates"][0]["marketer"]["id"] == 1
    assert response_data["rates"][0]["marketer"]["name"] == "Marketer"
    assert response_data["rates"][0]["rate_type"]["id"] == 1
    assert response_data["rates"][0]["rate_type"]["name"] == "Electricity rate type"
    assert response_data["rates"][0]["rate_type"]["energy_type"] == "electricity"


def test_other_cost_update_endpoint_not_user_auth(
    test_client: TestClient,
    other_cost: OtherCost,
    token_create: Token,
):
    response = test_client.put(
        "/api/costs/1",
        headers={"Authorization": "token fake_token"},
        json={
            "name": "Modified cost",
            "mandatory": False,
            "client_types": ["company"],
            "min_power": 56.65,
            "max_power": 65.56,
            "type": "percentage",
            "quantity": 16.28,
            "extra_fee": 33.33,
            "rates": [2],
        },
    )

    assert response.status_code == 401


def test_other_cost_update_endpoint_not_exists(
    test_client: TestClient,
    token_create: Token,
):
    response = test_client.put(
        "/api/costs/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Modified cost",
            "mandatory": False,
            "client_types": ["company"],
            "min_power": 56.65,
            "max_power": 65.56,
            "type": "percentage",
            "quantity": 16.28,
            "extra_fee": 33.33,
            "rates": [2],
        },
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["message"] == "Other cost does not exist"
    assert response_data["detail"][0]["code"] == "NOT_EXIST"


def test_other_cost_update_endpoint_deleted(
    test_client: TestClient,
    token_create: Token,
    other_cost: OtherCost,
):
    other_cost.is_deleted = True

    response = test_client.put(
        "/api/costs/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Modified cost",
            "mandatory": False,
            "client_types": ["company"],
            "min_power": 56.65,
            "max_power": 65.56,
            "type": "percentage",
            "quantity": 16.28,
            "extra_fee": 33.33,
            "rates": [1],
        },
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["message"] == "Other cost does not exist"
    assert response_data["detail"][0]["code"] == "NOT_EXIST"


def test_other_cost_update_endpoint_one_of_two_fields_ok(
    test_client: TestClient,
    other_cost: OtherCost,
    token_create: Token,
):
    response = test_client.put(
        "/api/costs/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Modified cost",
            "mandatory": True,
            "client_types": ["particular", "company"],
            "min_power": 3.5,
            "max_power": 23.5,
            "type": "eur/month",
            "quantity": 32,
            "extra_fee": 17.1,
            "rates": [1],
            "is_active": False,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == "Modified cost"
    assert response_data["is_active"] is True


def test_other_cost_list_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    other_cost: OtherCost,
    other_cost_2_rates: OtherCost,
    other_cost_disabled: OtherCost,
):
    response = test_client.get(
        "/api/costs",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 3
    assert response_data["page"] == 1
    assert response_data["size"] == 50
    assert len(response_data["items"]) == 3


def test_other_list_endpoint_filter_rates_id_in_ok(
    test_client: TestClient,
    token_create: Token,
    other_cost: OtherCost,
    other_cost_2_rates: OtherCost,
    other_cost_disabled: OtherCost,
):
    response = test_client.get(
        "/api/costs?rates__id__in=4",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 1
    assert response_data["items"][0]["name"] == "Other cost 2"
    assert len(response_data["items"][0]["rates"]) == 2


def test_other_cost_update_endpoint_extra_fee_ok(
    test_client: TestClient,
    other_cost: OtherCost,
    token_create: Token,
):
    response = test_client.put(
        "/api/costs/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Other cost",
            "mandatory": True,
            "client_types": ["particular", "company"],
            "min_power": 3.5,
            "max_power": 23.5,
            "type": "eur/month",
            "quantity": 32,
            "extra_fee": 0.78,
            "rates": [1],
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["extra_fee"] == 0.78


def test_other_cost_update_endpoint_rates_ok(
    test_client: TestClient,
    other_cost: OtherCost,
    token_create: Token,
    electricity_rate_2: Rate,
):
    response = test_client.put(
        "/api/costs/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Other cost",
            "mandatory": True,
            "client_types": ["particular", "company"],
            "min_power": 3.5,
            "max_power": 23.5,
            "type": "eur/month",
            "quantity": 32,
            "extra_fee": 17.1,
            "rates": [1, 4],
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data["rates"]) == 2


def test_other_cost_details_endpoint_ok(
    test_client: TestClient, token_create: Token, other_cost: OtherCost
):
    response = test_client.get(
        "/api/costs/1",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == 1
    assert response_data["name"] == "Other cost"
    assert response_data["mandatory"] is True
    assert response_data["client_types"] == ["particular", "company"]
    assert response_data["min_power"] == 3.5
    assert response_data["max_power"] == 23.5
    assert response_data["type"] == "eur/month"
    assert response_data["quantity"] == 32
    assert response_data["extra_fee"] == 17.1
    assert response_data["is_active"] is True
    assert response_data["is_deleted"] is False
    assert response_data["create_at"]
    assert response_data["rates"][0]["id"] == 1
    assert response_data["rates"][0]["marketer"]["id"] == 1
    assert response_data["rates"][0]["marketer"]["name"] == "Marketer"
    assert response_data["rates"][0]["rate_type"]["id"] == 1
    assert response_data["rates"][0]["rate_type"]["name"] == "Electricity rate type"
    assert response_data["rates"][0]["rate_type"]["energy_type"] == "electricity"


def test_other_cost_details_endpoint_not_token(test_client: TestClient):
    response = test_client.get("/api/costs/1")
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_AUTHENTICATED"
    assert response_data["detail"][0]["message"] == "Not authenticated"


def test_other_cost_details_endpoint_wrong_token(
    test_client: TestClient, token_create: Token
):
    response = test_client.get(
        "/api/costs/1", headers={"Authorization": "token faketoken"}
    )
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "INVALID_CREDENTIALS"
    assert response_data["detail"][0]["message"] == "Invalid authentication credentials"


def test_other_cost_details_endpoint_not_exist(
    test_client: TestClient, token_create: Token
):
    response = test_client.get(
        "/api/costs/1",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_EXIST"
    assert response_data["detail"][0]["message"] == "Other cost does not exist"


def test_other_cost_details_endpoint_deleted(
    test_client: TestClient, token_create: Token, other_cost: OtherCost
):
    other_cost.is_deleted = True

    response = test_client.get(
        "/api/costs/1",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_EXIST"
    assert response_data["detail"][0]["message"] == "Other cost does not exist"


def test_other_cost_partial_update_endpoint_is_active_ok(
    test_client: TestClient,
    db_session: Session,
    other_cost: OtherCost,
    token_create: Token,
):
    response = test_client.patch(
        "/api/costs/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 200
    other_cost = db_session.query(OtherCost).filter(OtherCost.id == 1).first()
    assert other_cost.is_active is False


def test_other_cost_partial_update_endpoint_is_deleted_ok(
    test_client: TestClient,
    db_session: Session,
    other_cost: OtherCost,
    token_create: Token,
):
    response = test_client.patch(
        "/api/costs/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "is_deleted": True,
        },
    )

    assert response.status_code == 200
    other_cost = db_session.query(OtherCost).filter(OtherCost.id == 1).first()
    assert other_cost.is_deleted is True


def test_other_cost_delete_other_cost_endpoint_ok(
    test_client: TestClient,
    db_session: Session,
    token_create: Token,
    other_cost: OtherCost,
    other_cost_2_rates: OtherCost,
    other_cost_disabled: OtherCost,
):
    """
    other_cost: 1
    other_cost_2_rates: 2
    other_cost_disabled: 3
    """
    response = test_client.post(
        "/api/costs/delete",
        headers={"Authorization": f"token {token_create.token}"},
        json={"ids": [1, 3, 125]},
    )

    assert response.status_code == 200
    assert (
        db_session.query(OtherCost).filter(OtherCost.is_deleted == false()).count() == 1
    )


def test_costs_export_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    other_cost: OtherCost,
    other_cost_2_rates: OtherCost,
    other_cost_disabled: OtherCost,
):
    response = test_client.post(
        "/api/costs/export/csv",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    lines = response.text.split("\r\n")
    assert len(lines) == 5
    assert len(lines[0].split(";")) == 12
    assert len(lines[1].split(";")) == 12
    assert len(lines[2].split(";")) == 12
    assert len(lines[3].split(";")) == 12
    assert lines[4].split(";")[0] == ""
    assert response.text.startswith(
        "Id;Is active;Rates;Name;Mandatory;Client types;Minimum power;Maximum power;"
        "Type;Quantity;Extra fee;Date\r\n3;"
    )
