from sqlalchemy import false
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from src.modules.margins.models import Margin
from src.modules.rates.models import Rate
from src.modules.users.models import Token


def test_margin_create_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    gas_rate: Rate,
):
    response = test_client.post(
        "/api/marketer-margins",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "type": "consume_range",
            "rate_id": 2,
            "min_consumption": 3.24,
            "max_consumption": 18.56,
            "min_margin": 28.3,
            "max_margin": 38.2,
        },
    )
    assert response.status_code == 201
    assert db_session.query(Margin).count() == 1


def test_margin_create_endpoint_error_auth(
    test_client: TestClient,
    db_session: Session,
    gas_rate: Rate,
):
    response = test_client.post(
        "/api/marketer-margins",
        headers={"Authorization": "token fake-token"},
        json={
            "type": "consume_range",
            "rate_id": 2,
            "min_consumption": 3.24,
            "max_consumption": 18.56,
            "min_margin": 28.3,
            "max_margin": 38.2,
        },
    )
    assert response.status_code == 401
    assert db_session.query(Margin).count() == 0


def test_margin_update_endpoint_ok(
    test_client: TestClient,
    margin: Margin,
    token_create: Token,
):
    response = test_client.put(
        "/api/marketer-margins/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "min_consumption": 2.62,
            "max_consumption": 6.22,
            "min_margin": 5.8,
            "max_margin": 8.5,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == 1
    assert response_data["type"] == "consume_range"
    assert response_data["min_consumption"] == 2.62
    assert response_data["max_consumption"] == 6.22
    assert response_data["min_margin"] == 5.8
    assert response_data["max_margin"] == 8.5
    assert response_data["rate_id"] == 2
    assert response_data["create_at"]


def test_margin_update_endpoint_rate_type_margin_ok(
    test_client: TestClient,
    margin_rate_type: Margin,
    token_create: Token,
):
    response = test_client.put(
        "/api/marketer-margins/2",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "min_margin": 5.8,
            "max_margin": 8.5,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == 2
    assert response_data["type"] == "rate_type"
    assert response_data["min_consumption"] is None
    assert response_data["max_consumption"] is None
    assert response_data["min_margin"] == 5.8
    assert response_data["max_margin"] == 8.5
    assert response_data["rate_id"] == 1
    assert response_data["create_at"]


def test_margin_update_endpoint_not_user_auth(
    test_client: TestClient,
    margin: Margin,
    token_create: Token,
):
    response = test_client.put(
        "/api/marketer-margins/1",
        headers={"Authorization": "token fake_token"},
        json={
            "min_consumption": 2.62,
            "max_consumption": 6.22,
            "min_margin": 5.8,
            "max_margin": 8.5,
        },
    )

    assert response.status_code == 401


def test_margin_update_endpoint_not_exists(
    test_client: TestClient,
    token_create: Token,
):
    response = test_client.put(
        "/api/marketer-margins/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "min_consumption": 2.62,
            "max_consumption": 6.22,
            "min_margin": 5.8,
            "max_margin": 8.5,
        },
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["message"] == "Margin does not exist"
    assert response_data["detail"][0]["code"] == "NOT_EXIST"


def test_margin_update_endpoint_deleted(
    test_client: TestClient,
    token_create: Token,
    margin: Margin,
):
    margin.is_deleted = True

    response = test_client.put(
        "/api/marketer-margins/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "min_consumption": 2.62,
            "max_consumption": 6.22,
            "min_margin": 5.8,
            "max_margin": 8.5,
        },
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["message"] == "Margin does not exist"
    assert response_data["detail"][0]["code"] == "NOT_EXIST"


def test_margin_update_endpoint_min_consumption_ok(
    test_client: TestClient,
    margin: Margin,
    token_create: Token,
):
    response = test_client.put(
        "/api/marketer-margins/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "min_consumption": 2.62,
            "max_consumption": 23.39,
            "min_margin": 16.3,
            "max_margin": 61.2,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["min_consumption"] == 2.62


def test_margin_update_endpoint_max_consumption_ok(
    test_client: TestClient,
    margin: Margin,
    token_create: Token,
):
    response = test_client.put(
        "/api/marketer-margins/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "min_consumption": 12.5,
            "max_consumption": 23.82,
            "min_margin": 16.3,
            "max_margin": 61.2,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["max_consumption"] == 23.82


def test_margin_update_endpoint_min_margin_ok(
    test_client: TestClient,
    margin: Margin,
    token_create: Token,
):
    response = test_client.put(
        "/api/marketer-margins/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "min_consumption": 12.5,
            "max_consumption": 23.39,
            "min_margin": 3.3,
            "max_margin": 61.2,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["min_margin"] == 3.3


def test_margin_update_endpoint_max_margin_ok(
    test_client: TestClient,
    margin: Margin,
    token_create: Token,
):
    response = test_client.put(
        "/api/marketer-margins/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "min_consumption": 12.5,
            "max_consumption": 23.39,
            "min_margin": 16.3,
            "max_margin": 36.2,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["max_margin"] == 36.2


def test_margin_update_endpoint_one_of_two_fields_ok(
    test_client: TestClient,
    margin: Margin,
    token_create: Token,
):
    response = test_client.put(
        "/api/marketer-margins/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "min_consumption": 12.5,
            "max_consumption": 23.39,
            "min_margin": 16.3,
            "max_margin": 36.2,
            "type": "rate_type",
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["max_margin"] == 36.2
    assert response_data["type"] == "consume_range"


def test_margin_update_endpoint_rate_type_margin_consumption_range_ok(
    test_client: TestClient,
    margin_rate_type: Margin,
    token_create: Token,
):
    response = test_client.put(
        "/api/marketer-margins/2",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "min_consumption": 12.5,
            "max_consumption": 23.39,
            "min_margin": 16.3,
            "max_margin": 36.2,
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["min_consumption"] is None
    assert response_data["max_consumption"] is None
    assert response_data["max_margin"] == 36.2


def test_margin_list_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    margin: Margin,
    margin_consume_range: Margin,
    margin_rate_type: Margin,
):
    margin_rate_type.is_deleted = True

    response = test_client.get(
        "/api/marketer-margins",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 2
    assert response_data["page"] == 1
    assert response_data["size"] == 50
    assert len(response_data["items"]) == 2
    assert response_data["items"][0]["id"] == 3


def test_margin_list_endpoint_sort_by_ok(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    margin: Margin,
    margin_rate_type: Margin,
):
    response = test_client.get(
        "/api/marketer-margins?order_by=-rate__name",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 2
    assert response_data["items"][0]["rate"]["name"] == "Gas rate name"
    assert response_data["items"][1]["rate"]["name"] == "Electricity rate"


def test_margin_list_endpoint_sort_by_double_relation_ok(
    test_client: TestClient,
    token_create: Token,
    margin: Margin,
    margin_rate_type: Margin,
):
    response = test_client.get(
        "/api/marketer-margins?order_by=-rate__rate_type__name",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 2
    assert response_data["items"][0]["rate"]["rate_type"]["name"] == "Gas rate type"
    assert (
        response_data["items"][1]["rate"]["rate_type"]["name"]
        == "Electricity rate type"
    )


def test_margin_list_endpoint_filter_margin_rate_name_ok(
    test_client: TestClient,
    token_create: Token,
    margin: Margin,
    margin_rate_type: Margin,
):
    response = test_client.get(
        "/api/marketer-margins?rate__name__unaccent=elÉc",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 1
    assert response_data["items"][0]["rate"]["name"] == "Electricity rate"


def test_margin_list_endpoint_filter_margin_rate_type_name_ok(
    test_client: TestClient,
    token_create: Token,
    margin: Margin,
    margin_rate_type: Margin,
):
    response = test_client.get(
        "/api/marketer-margins?rate__rate_type__name__unaccent=elÉc",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 1
    assert (
        response_data["items"][0]["rate"]["rate_type"]["name"]
        == "Electricity rate type"
    )


def test_margin_details_endpoint_ok(
    test_client: TestClient, token_create: Token, margin: Margin
):
    response = test_client.get(
        "/api/marketer-margins/1",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == 1
    assert response_data["type"] == "consume_range"
    assert response_data["min_margin"] == 16.3
    assert response_data["max_margin"] == 61.2
    assert response_data["min_consumption"] == 12.5
    assert response_data["max_consumption"] == 23.39
    assert response_data["rate"]["id"] == 2
    assert response_data["rate"]["name"] == "Gas rate name"
    assert response_data["rate"]["marketer_id"] == 1
    assert response_data["rate"]["price_type"] == "fixed_base"
    assert response_data["rate"]["rate_type"]["id"] == 2
    assert response_data["rate"]["rate_type"]["name"] == "Gas rate type"
    assert response_data["rate"]["rate_type"]["energy_type"] == "gas"
    assert response_data["create_at"]


def test_margin_details_endpoint_not_token(test_client: TestClient):
    response = test_client.get("/api/marketer-margins/1")
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_AUTHENTICATED"
    assert response_data["detail"][0]["message"] == "Not authenticated"


def test_margin_details_endpoint_wrong_token(
    test_client: TestClient, token_create: Token
):
    response = test_client.get(
        "/api/marketer-margins/1", headers={"Authorization": "token faketoken"}
    )
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "INVALID_CREDENTIALS"
    assert response_data["detail"][0]["message"] == "Invalid authentication credentials"


def test_margin_details_endpoint_not_exist(
    test_client: TestClient, token_create: Token
):
    response = test_client.get(
        "/api/marketer-margins/1",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_EXIST"
    assert response_data["detail"][0]["message"] == "Margin does not exist"


def test_margin_details_endpoint_deleted(
    test_client: TestClient, token_create: Token, margin: Margin
):
    margin.is_deleted = True

    response = test_client.get(
        "/api/marketer-margins/1",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_EXIST"
    assert response_data["detail"][0]["message"] == "Margin does not exist"


def test_margin_partial_update_endpoint_is_deleted_ok(
    test_client: TestClient,
    db_session: Session,
    margin: Margin,
    token_create: Token,
):
    response = test_client.patch(
        "/api/marketer-margins/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "is_deleted": True,
        },
    )

    assert response.status_code == 200
    margin = db_session.query(Margin).filter(Margin.id == 1).first()
    assert margin.is_deleted is True


def test_margins_delete_margins_endpoint_ok(
    test_client: TestClient,
    db_session: Session,
    token_create: Token,
    margin: Margin,
    margin_consume_range: Margin,
    margin_rate_type: Margin,
):
    """
    margin: 1
    margin_consume_range: 3
    margin_rate_type: 2
    """
    response = test_client.post(
        "/api/marketer-margins/delete",
        headers={"Authorization": f"token {token_create.token}"},
        json={"ids": [1, 2, 125]},
    )

    assert response.status_code == 200
    assert db_session.query(Margin).filter(Margin.is_deleted == false()).count() == 1


def test_margins_export_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    margin: Margin,
    margin_consume_range: Margin,
    margin_rate_type: Margin,
):
    response = test_client.post(
        "/api/marketer-margins/export/csv",
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
        "Id;Type;Rate;Rate type;Minimum consumption;Maximum consumption;"
        "Minimum margin;Maximum margin;Date\r\n3;"
    )
