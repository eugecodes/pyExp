from sqlalchemy import false
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from src.modules.marketers.models import Marketer
from src.modules.users.models import Token


def test_marketer_create_endpoint_ok(
    test_client: TestClient, token_create: Token, db_session: Session
):
    response = test_client.post(
        "/api/marketers",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Electrical marketer",
            "fiscal_name": "Electrical marketer Inc.",
            "cif": "QWERTY123",
            "email": "elecmarketer@test.com",
        },
    )

    assert response.status_code == 201
    assert db_session.query(Marketer).count() == 1


def test_marketer_create_endpoint_empty_strings_ok(
    test_client: TestClient, token_create: Token, db_session: Session
):
    response = test_client.post(
        "/api/marketers",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Electrical marketer",
            "fiscal_name": "",
            "cif": "",
            "email": "",
        },
    )

    assert response.status_code == 201
    assert db_session.query(Marketer).count() == 1
    marketer = response.json()
    assert not marketer["fiscal_name"]
    assert not marketer["cif"]
    assert not marketer["email"]


def test_marketer_create_endpoint_error_auth(
    test_client: TestClient, db_session: Session
):
    response = test_client.post(
        "/api/marketers",
        headers={"Authorization": "token fake-token"},
        json={
            "name": "Electrical marketer",
            "fiscal_name": "Electrical marketer Inc.",
            "cif": "QWERTY123",
            "email": "elecmarketer@test.com",
        },
    )
    assert response.status_code == 401
    assert db_session.query(Marketer).count() == 0


def test_marketer_list_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    marketer: Marketer,
    marketer_deleted: Marketer,
):
    response = test_client.get(
        "/api/marketers",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 1
    assert response_data["page"] == 1
    assert response_data["size"] == 50
    assert len(response_data["items"]) == 1
    assert response_data["items"][0]["id"] == 1
    assert response_data["items"][0]["name"] == "Marketer"
    assert response_data["items"][0]["fiscal_name"] == "Marketer official"
    assert response_data["items"][0]["is_active"] is False
    assert response_data["items"][0]["create_at"]
    assert response_data["items"][0]["user"]["id"] == 1
    assert response_data["items"][0]["user"]["first_name"] == "John"
    assert response_data["items"][0]["user"]["last_name"] == "Graham"


def test_marketer_list_endpoint_filters_working_ok(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    marketer: Marketer,
    marketer2: Marketer,
    marketer_deleted: Marketer,
):
    """
    This tests ensures that the filters keep working even after calling another endpoint that
    initializes the filter we are currently working. In this case, we first call to the rates endpoint filtering
    by marketer name, which initializes the MarketerFilter, and then call the list marketers endpoint.
    If the filters are not working this call would return 2 marketers (all of them) instead of 1
    """
    _ = test_client.get(
        "api/rates?marketer__name__unaccent=marketer",
        headers={"Authorization": f"token {token_create.token}"},
    )
    response = test_client.get(
        "/api/marketers?name__unaccent=secondary",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 1
    assert response_data["page"] == 1
    assert response_data["size"] == 50
    assert len(response_data["items"]) == 1
    assert response_data["items"][0]["id"] == 2
    assert response_data["items"][0]["name"] == "Marketer secondary"
    assert response_data["items"][0]["fiscal_name"] == "Official second marketer"
    assert response_data["items"][0]["is_active"] is False
    assert response_data["items"][0]["create_at"]
    assert response_data["items"][0]["user"]["id"] == 2
    assert response_data["items"][0]["user"]["first_name"] == "Johnathan"
    assert response_data["items"][0]["user"]["last_name"] == "Smith"


def test_marketer_list_endpoint_sort_by_ok(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    marketer: Marketer,
    marketer2: Marketer,
):
    response = test_client.get(
        "/api/marketers?order_by=-fiscal_name",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 2
    assert response_data["items"][0]["fiscal_name"] == "Official second marketer"
    assert response_data["items"][1]["fiscal_name"] == "Marketer official"


def test_marketer_list_endpoint_filter_user_first_name_ok(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    marketer: Marketer,
    marketer2: Marketer,
):
    response = test_client.get(
        "/api/marketers?user__first_name__unaccent=jóhNa",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 1
    assert response_data["items"][0]["user"]["first_name"] == "Johnathan"


def test_marketer_update_endpoint_ok(
    test_client: TestClient,
    marketer: Marketer,
    token_create: Token,
):
    response = test_client.put(
        "/api/marketers/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Modified Name",
            "fiscal_name": "Fiscal Modified Name",
            "cif": "123QWERTY",
            "email": "modified_marketer@test.com",
            "fee": 14.3,
            "max_consume": 280.63,
            "consume_range_datetime": "2023-01-01 00:00:00",
            "surplus_price": 8.25,
            "address": {
                "type": "Street",
                "name": "Lincoln",
                "number": 3,
                "subdivision": "Block 3",
                "others": "Second door",
                "postal_code": "1H1J5J",
                "city": "Los Angeles",
                "province": "California",
            },
        },
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == 1
    assert response_data["name"] == "Modified Name"
    assert response_data["fiscal_name"] == "Fiscal Modified Name"
    assert response_data["cif"] == "123QWERTY"
    assert response_data["email"] == "modified_marketer@test.com"
    assert response_data["fee"] == 14.3
    assert response_data["max_consume"] == 280.63
    assert response_data["consume_range_datetime"] == "2023-01-01T00:00:00"
    assert response_data["surplus_price"] == 8.25
    assert response_data["address"]["id"] == 1
    assert response_data["address"]["type"] == "Street"
    assert response_data["address"]["name"] == "Lincoln"
    assert response_data["address"]["number"] == 3
    assert response_data["address"]["subdivision"] == "Block 3"
    assert response_data["address"]["others"] == "Second door"
    assert response_data["address"]["postal_code"] == "1H1J5J"
    assert response_data["address"]["city"] == "Los Angeles"
    assert response_data["address"]["province"] == "California"


def test_marketer_update_endpoint_not_user_auth(
    test_client: TestClient,
    marketer: Marketer,
):
    response = test_client.put(
        "/api/marketers/1",
        headers={"Authorization": "token fake_token"},
        json={
            "name": "Modified Name",
            "fiscal_name": "Fiscal Modified Name",
            "cif": "123QWERTY",
            "email": "modified_marketer@test.com",
        },
    )

    assert response.status_code == 401


def test_marketer_update_endpoint_not_exists(
    test_client: TestClient,
    token_create: Token,
):
    response = test_client.put(
        "/api/marketers/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Modified Name",
            "fiscal_name": "Fiscal Modified Name",
            "cif": "123QWERTY",
            "email": "modified_marketer@test.com",
        },
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["message"] == "Marketer does not exist"
    assert response_data["detail"][0]["code"] == "NOT_EXIST"


def test_marketer_update_endpoint_deleted(
    test_client: TestClient,
    token_create: Token,
    marketer_deleted: Marketer,
):
    response = test_client.put(
        "/api/marketers/4",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Modified Name",
            "fiscal_name": "Fiscal Modified Name",
            "cif": "123QWERTY",
            "email": "modified_marketer@test.com",
        },
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["message"] == "Marketer does not exist"
    assert response_data["detail"][0]["code"] == "NOT_EXIST"


def test_marketer_update_endpoint_required_fields_ok(
    test_client: TestClient,
    marketer: Marketer,
    token_create: Token,
):
    response = test_client.put(
        "/api/marketers/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "name": "Modified Name",
            "fiscal_name": "Fiscal Modified Name",
            "cif": "123QWERTY",
            "email": "modified_marketer@test.com",
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == 1
    assert response_data["name"] == "Modified Name"


def test_marketer_partial_update_endpoint_is_active_ok(
    test_client: TestClient,
    marketer: Marketer,
    token_create: Token,
):
    response = test_client.patch(
        "/api/marketers/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={"is_active": False},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["is_active"] is False


def test_marketer_partial_update_endpoint_is_deleted_ok(
    test_client: TestClient,
    marketer: Marketer,
    token_create: Token,
):
    response = test_client.patch(
        "/api/marketers/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={"is_deleted": True},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["is_deleted"] is True


def test_marketers_details_endpoint_ok(
    test_client: TestClient, token_create: Token, marketer: Marketer
):
    response = test_client.get(
        "/api/marketers/1",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == 1
    assert response_data["name"] == "Marketer"
    assert response_data["fiscal_name"] == "Marketer official"
    assert response_data["cif"] == "QWERTY123"
    assert response_data["email"] == "marketer@test.com"
    assert response_data["fee"] == 15.4
    assert response_data["max_consume"] == 150.8
    assert response_data["consume_range_datetime"]
    assert response_data["surplus_price"] == 22.5
    assert response_data["is_active"] is False
    assert response_data["create_at"]
    assert response_data["user"]["id"] == 1
    assert response_data["user"]["first_name"] == "John"
    assert response_data["user"]["last_name"] == "Graham"
    assert response_data["address"]["id"] == 1
    assert response_data["address"]["type"] == "Avenue"
    assert response_data["address"]["name"] == "Fifth"
    assert response_data["address"]["number"] == 1
    assert not response_data["address"]["subdivision"]
    assert not response_data["address"]["others"]
    assert response_data["address"]["postal_code"] == "10021"
    assert response_data["address"]["city"] == "New York"
    assert response_data["address"]["province"] == "New York State"


def test_marketers_details_endpoint_not_token(test_client: TestClient):
    response = test_client.get("/api/marketers/1")
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_AUTHENTICATED"
    assert response_data["detail"][0]["message"] == "Not authenticated"


def test_marketers_details_endpoint_wrong_token(
    test_client: TestClient, token_create: Token
):
    response = test_client.get(
        "/api/marketers/1", headers={"Authorization": "token faketoken"}
    )
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "INVALID_CREDENTIALS"
    assert response_data["detail"][0]["message"] == "Invalid authentication credentials"


def test_marketers_details_endpoint_not_exist(
    test_client: TestClient, token_create: Token
):
    response = test_client.get(
        "/api/marketers/1",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_EXIST"
    assert response_data["detail"][0]["message"] == "Marketer does not exist"


def test_marketers_details_endpoint_deleted(
    test_client: TestClient, token_create: Token, marketer_deleted: Marketer
):
    response = test_client.get(
        "/api/marketers/4",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_EXIST"
    assert response_data["detail"][0]["message"] == "Marketer does not exist"


def test_marketers_delete_marketers_endpoint_ok(
    test_client: TestClient,
    db_session: Session,
    token_create: Token,
    marketer: Marketer,
    marketer2: Marketer,
    marketer_disabled: Marketer,
    marketer_deleted: Marketer,
):
    response = test_client.post(
        "/api/marketers/delete",
        headers={"Authorization": f"token {token_create.token}"},
        json={"ids": [1, 2, 125]},
    )

    assert response.status_code == 200
    assert (
        db_session.query(Marketer).filter(Marketer.is_deleted == false()).count() == 1
    )


def test_marketers_export_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    marketer: Marketer,
    marketer2: Marketer,
    marketer_disabled: Marketer,
    marketer_deleted: Marketer,
):
    response = test_client.post(
        "/api/marketers/export/csv",
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
        "Id;Name;Fiscal Name;Is active;User first name;User last name;Date"
    )
