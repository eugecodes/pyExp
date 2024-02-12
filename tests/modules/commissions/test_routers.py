from sqlalchemy import false
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from src.modules.commissions.models import Commission
from src.modules.rates.models import Rate
from src.modules.users.models import Token


def test_commission_create_endpoint_ok(
    test_client: TestClient, token_create: Token, db_session: Session, gas_rate: Rate
):
    response = test_client.post(
        "/api/commissions",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Commission name",
            "percentage_Test_commission": 12,
            "rate_type_id": 2,
            "rates": [2],
        },
    )

    assert response.status_code == 201
    assert db_session.query(Commission).count() == 1


def test_commission_create_endpoint_error(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    electricity_rate: Rate,
    commission: Commission,
):
    response = test_client.post(
        "/api/commissions",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Commission name",
            "Test_commission": 10,
            "rate_type_segmentation": False,
            "range_type": "consumption",
            "rates": [1],
            "min_consumption": 7,
            "max_consumption": 11.5,
        },
    )

    assert response.status_code == 422
    response_json = response.json()
    assert response_json["detail"][0]["code"] == "CONSUMPTION_RANGE_OVERLAP"


def test_commission_create_endpoint_error_overlapping(
    test_client: TestClient,
    db_session: Session,
    token_create: Token,
    commission_2: Commission,
):
    response = test_client.post(
        "/api/commissions",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Commission name 2",
            "rate_type_segmentation": False,
            "range_type": "consumption",
            "Test_commission": 0,
            "min_consumption": 7,
            "max_consumption": 11.5,
            "rates": [4],
        },
    )

    assert response.status_code == 422
    response_json = response.json()
    assert response_json["detail"][0]["code"] == "CONSUMPTION_RANGE_OVERLAP"
    assert (
        response_json["detail"][0]["message"]
        == "Overlap in the consuption range with existing resource"
    )
    assert db_session.query(Commission).count() == 1


def test_commission_create_endpoint_error_auth(
    test_client: TestClient, db_session: Session
):
    response = test_client.post(
        "/api/commissions",
        headers={"Authorization": "token fake-token"},
        json={
            "name": "Commission name",
            "percentage_Test_commission": 12,
            "rate_type_id": 2,
            "rates": [2],
        },
    )

    assert response.status_code == 401
    assert db_session.query(Commission).count() == 0


def test_commission_update_endpoint_ok(
    test_client: TestClient,
    commission: Commission,
    token_create: Token,
    electricity_rate_2: Rate,
):
    response = test_client.put(
        "/api/commissions/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Commission modified",
            "min_consumption": 28.2,
            "max_consumption": 32.8,
            "Test_commission": 8,
            "rates": [4],
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == 1
    assert response_data["name"] == "Commission modified"
    assert response_data["range_type"] == "consumption"
    assert response_data["min_consumption"] == 28.2
    assert response_data["max_consumption"] == 32.8
    assert response_data["min_power"] is None
    assert response_data["max_power"] is None
    assert response_data["percentage_Test_commission"] is None
    assert response_data["rate_type_segmentation"] is True
    assert response_data["Test_commission"] == 8
    assert response_data["create_at"]
    assert response_data["rates"][0]["id"] == 4
    assert response_data["rates"][0]["name"] == "Electricity rate 2"
    assert response_data["rates"][0]["rate_type"]["id"] == 1
    assert response_data["rates"][0]["rate_type"]["name"] == "Electricity rate type"
    assert response_data["rates"][0]["rate_type"]["energy_type"] == "electricity"
    assert response_data["rates"][0]["marketer_id"] == 1
    assert response_data["rates"][0]["price_type"] == "fixed_fixed"
    assert response_data["rate_type"]["id"] == 1
    assert response_data["rate_type"]["name"] == "Electricity rate type"
    assert response_data["rate_type"]["energy_type"] == "electricity"


def test_commission_update_endpoint_rate_type_segmentation_false(
    test_client: TestClient,
    commission_2: Commission,
    token_create: Token,
    electricity_rate: Rate,
):
    """
    Update a commission which have rate_type_segmentation field as false
    """
    response = test_client.put(
        "/api/commissions/4",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Commission modified",
            "min_consumption": 28.2,
            "max_consumption": 32.8,
            "Test_commission": 8,
            "rates": [4],
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == 4
    assert response_data["name"] == "Commission modified"
    assert response_data["range_type"] == "consumption"
    assert response_data["min_consumption"] == 28.2
    assert response_data["max_consumption"] == 32.8
    assert response_data["min_power"] is None
    assert response_data["max_power"] is None
    assert response_data["percentage_Test_commission"] is None
    assert response_data["rate_type_segmentation"] is False
    assert response_data["Test_commission"] == 8
    assert response_data["create_at"]
    assert response_data["rates"][0]["id"] == 4
    assert response_data["rates"][0]["name"] == "Electricity rate 2"
    assert response_data["rates"][0]["rate_type"]["id"] == 1
    assert response_data["rates"][0]["rate_type"]["name"] == "Electricity rate type"
    assert response_data["rates"][0]["rate_type"]["energy_type"] == "electricity"
    assert response_data["rates"][0]["marketer_id"] == 1
    assert response_data["rates"][0]["price_type"] == "fixed_fixed"
    assert response_data["rate_type"] is None


def test_commission_update_endpoint_not_user_auth(
    test_client: TestClient,
    commission: Commission,
    token_create: Token,
):
    response = test_client.put(
        "/api/commissions/1",
        headers={"Authorization": "token fake_token"},
        json={
            "name": "Commission modified",
            "min_consumption": 28.2,
            "max_consumption": 32.8,
            "Test_commission": 8,
            "rates": [2],
        },
    )

    assert response.status_code == 401


def test_commission_update_endpoint_not_exists(
    test_client: TestClient,
    token_create: Token,
):
    response = test_client.put(
        "/api/commissions/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Commission modified",
            "min_consumption": 28.2,
            "max_consumption": 32.8,
            "Test_commission": 8,
            "rates": [2],
        },
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["message"] == "Commission does not exist"
    assert response_data["detail"][0]["code"] == "NOT_EXIST"


def test_commission_update_endpoint_deleted(
    test_client: TestClient,
    token_create: Token,
    commission: Commission,
):
    commission.is_deleted = True

    response = test_client.put(
        "/api/commissions/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Commission modified",
            "min_consumption": 28.2,
            "max_consumption": 32.8,
            "Test_commission": 8,
            "rates": [1],
        },
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["message"] == "Commission does not exist"
    assert response_data["detail"][0]["code"] == "NOT_EXIST"


def test_commission_update_endpoint_one_of_two_fields_ok(
    test_client: TestClient,
    commission: Commission,
    token_create: Token,
    electricity_rate_2: Rate,
):
    response = test_client.put(
        "/api/commissions/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Commission modified",
            "min_consumption": 28.2,
            "max_consumption": 32.8,
            "Test_commission": 8,
            "rates": [4],
            "create_at": "2022-01-01",
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == "Commission modified"
    assert response_data["create_at"] != "2022-01-01"


def test_commission_details_endpoint_ok(
    test_client: TestClient, token_create: Token, commission: Commission
):
    response = test_client.get(
        "/api/commissions/1",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == 1
    assert response_data["name"] == "Commission name"
    assert response_data["range_type"] == "consumption"
    assert response_data["min_consumption"] == 3.5
    assert response_data["max_consumption"] == 11.5
    assert response_data["min_power"] is None
    assert response_data["max_power"] is None
    assert response_data["percentage_Test_commission"] is None
    assert response_data["rate_type_segmentation"] is True
    assert response_data["Test_commission"] == 12
    assert response_data["create_at"]
    assert response_data["rates"][0]["id"] == 1
    assert response_data["rates"][0]["name"] == "Electricity rate"
    assert response_data["rates"][0]["rate_type"]["id"] == 1
    assert response_data["rates"][0]["rate_type"]["name"] == "Electricity rate type"
    assert response_data["rates"][0]["rate_type"]["energy_type"] == "electricity"
    assert response_data["rates"][0]["marketer_id"] == 1
    assert response_data["rates"][0]["price_type"] == "fixed_fixed"
    assert response_data["rate_type"]["id"] == 1
    assert response_data["rate_type"]["name"] == "Electricity rate type"
    assert response_data["rate_type"]["energy_type"] == "electricity"


def test_commission_details_endpoint_not_token(test_client: TestClient):
    response = test_client.get("/api/commissions/1")
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_AUTHENTICATED"
    assert response_data["detail"][0]["message"] == "Not authenticated"


def test_commission_details_endpoint_wrong_token(
    test_client: TestClient, token_create: Token
):
    response = test_client.get(
        "/api/commissions/1", headers={"Authorization": "token faketoken"}
    )
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "INVALID_CREDENTIALS"
    assert response_data["detail"][0]["message"] == "Invalid authentication credentials"


def test_commission_details_endpoint_not_exist(
    test_client: TestClient, token_create: Token
):
    response = test_client.get(
        "/api/commissions/1",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_EXIST"
    assert response_data["detail"][0]["message"] == "Commission does not exist"


def test_commission_details_endpoint_deleted(
    test_client: TestClient, token_create: Token, commission: Commission
):
    commission.is_deleted = True

    response = test_client.get(
        "/api/commissions/1",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_EXIST"
    assert response_data["detail"][0]["message"] == "Commission does not exist"


def test_commission_partial_update_endpoint_is_deleted_ok(
    test_client: TestClient,
    db_session: Session,
    commission: Commission,
    token_create: Token,
):
    response = test_client.patch(
        "/api/commissions/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "is_deleted": True,
        },
    )

    assert response.status_code == 200
    commission = db_session.query(Commission).filter(Commission.id == 1).first()
    assert commission.is_deleted is True


def test_commission_list_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    commission: Commission,
    commission_fixed_base: Commission,
):
    response = test_client.get(
        "/api/commissions",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 2
    assert response_data["page"] == 1
    assert response_data["size"] == 50
    assert len(response_data["items"]) == 2
    assert response_data["items"][0]["id"] == 2


def test_commission_list_endpoint_several_rates_ok(
    db_session: Session,
    test_client: TestClient,
    token_create: Token,
    commission: Commission,
    commission_fixed_base: Commission,
    electricity_rate_2: Rate,
):
    commission.rates.append(electricity_rate_2)
    db_session.add(commission)
    db_session.commit()

    response = test_client.get(
        "/api/commissions",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 2
    assert response_data["page"] == 1
    assert response_data["size"] == 50
    assert len(response_data["items"]) == 2


def test_commission_list_endpoint_filter_rate_type_energy_type_ok(
    db_session: Session,
    test_client: TestClient,
    token_create: Token,
    commission: Commission,
    commission_fixed_base: Commission,
    electricity_rate_2: Rate,
):
    commission.rates.append(electricity_rate_2)
    db_session.add(commission)
    db_session.commit()

    response = test_client.get(
        "/api/commissions?rate_type__energy_type=electricity",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 1
    assert response_data["page"] == 1
    assert response_data["size"] == 50
    assert len(response_data["items"]) == 1
    assert response_data["items"][0]["id"] == 1
    assert response_data["items"][0]["name"] == "Commission name"
    assert len(response_data["items"][0]["rates"]) == 2
    # TODO --> Check the order of the rates depends on the execution order of tests
    # assert response_data["items"][0]["rates"][0]["id"] == 1
    # assert response_data["items"][0]["rates"][1]["id"] == 4


def test_commissions_delete_users_endpoint_ok(
    test_client: TestClient,
    db_session: Session,
    token_create: Token,
    commission: Commission,
    commission_fixed_base: Commission,
):
    """
    commission: 1
    commission_fixed_base: 2
    """
    response = test_client.post(
        "/api/commissions/delete",
        headers={"Authorization": f"token {token_create.token}"},
        json={"ids": [1, 2, 125]},
    )

    assert response.status_code == 200
    assert (
        db_session.query(Commission).filter(Commission.is_deleted == false()).count()
        == 0
    )


def test_commissions_export_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    commission: Commission,
    commission_fixed_base: Commission,
):
    response = test_client.post(
        "/api/commissions/export/csv",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    lines = response.text.split("\r\n")
    assert len(lines) == 4
    assert len(lines[0].split(";")) == 13
    assert len(lines[1].split(";")) == 13
    assert len(lines[2].split(";")) == 13
    assert lines[3].split(";")[0] == ""
    assert response.text.startswith(
        "Id;Name;Range type;Minimum consumption;Maximum consumption;Minimum power;"
        "Maximum power;Percentage Test commission;Rate type segmentation;"
        "Test commission;Rates;Rate type;Date\r\n2;"
    )
