from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from src.modules.clients.models import Client, InvoiceNotificationType
from src.modules.rates.models import ClientType
from src.modules.users.models import Token


def test_client_create_endpoint_ok(
    test_client: TestClient, token_create: Token, db_session: Session
):
    response = test_client.post(
        "/api/clients",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "alias": "Alias",
            "client_type": ClientType.company,
            "fiscal_name": "Fiscal name",
            "cif": "123456789",
            "main_contact": {
                "name": "contact name",
                "email": "contasct@email.com",
                "phone": "666666666",
            },
            "invoice_notification_type": InvoiceNotificationType.email,
            "invoice_email": "test@test.com",
            "bank_account_holder": "Bank account holder",
            "bank_account_number": "Bank account number",
            "fiscal_address": "fiscal address",
            "is_renewable": "true",
        },
    )

    assert response.status_code == 201
    assert db_session.query(Client).count() == 1


def test_client_create_endpoint_empty_strings_ok(
    test_client: TestClient, token_create: Token, db_session: Session
):
    response = test_client.post(
        "/api/clients",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "alias": "",
            "client_type": ClientType.company,
            "fiscal_name": "Fiscal name",
            "cif": "123456789",
            "main_contact": {
                "name": "contact name",
                "email": "contasct@email.com",
                "phone": "666666666",
            },
            "invoice_notification_type": InvoiceNotificationType.email,
            "invoice_email": "test@test.com",
            "bank_account_holder": "Bank account holder",
            "bank_account_number": "Bank account number",
            "fiscal_address": "fiscal address",
            "is_renewable": "true",
        },
    )

    assert response.status_code == 201
    assert db_session.query(Client).count() == 1
    client = response.json()
    assert not client["alias"]


def test_client_create_endpoint_error_auth(
    test_client: TestClient, db_session: Session
):
    response = test_client.post(
        "/api/clients",
        headers={"Authorization": "token fake-token"},
        json={
            "alias": "Alias",
            "client_type": ClientType.company,
            "fiscal_name": "Fiscal name",
            "cif": "123456789",
            "main_contact": {
                "name": "contact name",
                "email": "contasct@email.com",
                "phone": "666666666",
            },
            "invoice_notification_type": InvoiceNotificationType.email,
            "invoice_email": "test@test.com",
            "bank_account_holder": "Bank account holder",
            "bank_account_number": "Bank account number",
            "fiscal_address": "fiscal address",
            "is_renewable": "true",
        },
    )
    assert response.status_code == 401
    assert db_session.query(Client).count() == 0


def test_client_list_endpoint_ok(
    test_client: TestClient, token_create: Token, db_session: Session, client: Client
):
    response = test_client.get(
        "/api/clients",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 1
    assert response_data["page"] == 1
    assert response_data["size"] == 50
    assert len(response_data["items"]) == 1
    assert response_data["items"][0]["id"] == 1


def test_client_update_endpoint_ok(
    test_client: TestClient,
    client: Client,
    token_create: Token,
):
    response = test_client.put(
        f"/api/clients/{client.id}",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "alias": "Alias nuevo",
            "client_type": ClientType.company,
            "fiscal_name": "Fiscal name",
            "cif": "123456781",
            "invoice_notification_type": InvoiceNotificationType.email,
            "invoice_email": "test@test.com",
            "bank_account_holder": "Bank account holder",
            "bank_account_number": "Bank account number",
            "fiscal_address": "fiscal address",
            "is_renewable": "true",
        },
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == 1
    assert response_data["alias"] == "Alias nuevo"


def test_client_update_endpoint_not_user_auth(
    test_client: TestClient,
    client: Client,
):
    response = test_client.put(
        "/api/clients/1",
        headers={"Authorization": "token fake_token"},
        json={
            "alias": "Alias",
            "client_type": ClientType.company,
            "fiscal_name": "Fiscal name",
            "cif": "123456789",
            "main_contact": {
                "name": "contact name",
                "email": "contasct@email.com",
                "phone": "666666666",
            },
            "invoice_notification_type": InvoiceNotificationType.email,
            "invoice_email": "test@test.com",
            "bank_account_holder": "Bank account holder",
            "bank_account_number": "Bank account number",
            "fiscal_address": "fiscal address",
            "is_renewable": "true",
        },
    )

    assert response.status_code == 401


def test_client_update_endpoint_not_exists(
    test_client: TestClient,
    token_create: Token,
):
    response = test_client.put(
        "/api/clients/10",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "alias": "Alias",
            "client_type": ClientType.company,
            "fiscal_name": "Fiscal name",
            "cif": "123456789",
            "main_contact": {
                "name": "contact name",
                "email": "contasct@email.com",
                "phone": "666666666",
            },
            "invoice_notification_type": InvoiceNotificationType.email,
            "invoice_email": "test@test.com",
            "bank_account_holder": "Bank account holder",
            "bank_account_number": "Bank account number",
            "fiscal_address": "fiscal address",
            "is_renewable": "true",
        },
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "client_not_exist"


def test_client_update_endpoint_deleted(
    test_client: TestClient,
    token_create: Token,
):
    response = test_client.put(
        "/api/clients/4",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "alias": "Alias",
            "client_type": ClientType.company,
            "fiscal_name": "Fiscal name",
            "cif": "123456789",
            "main_contact": {
                "name": "contact name",
                "email": "contasct@email.com",
                "phone": "666666666",
            },
            "invoice_notification_type": InvoiceNotificationType.email,
            "invoice_email": "test@test.com",
            "bank_account_holder": "Bank account holder",
            "bank_account_number": "Bank account number",
            "fiscal_address": "fiscal address",
            "is_renewable": "true",
        },
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "client_not_exist"


def test_client_update_endpoint_required_fields_ok(
    test_client: TestClient,
    client: Client,
    token_create: Token,
):
    response = test_client.put(
        "/api/clients/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "alias": "Alias",
            "client_type": ClientType.company,
            "fiscal_name": "Fiscal name",
            "cif": "123456789",
            "main_contact": {
                "name": "contact name",
                "email": "contasct@email.com",
                "phone": "666666666",
            },
            "invoice_notification_type": InvoiceNotificationType.email,
            "invoice_email": "test@test.com",
            "bank_account_holder": "Bank account holder",
            "bank_account_number": "Bank account number",
            "fiscal_address": "fiscal address",
            "is_renewable": "true",
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == 1
    assert response_data["fiscal_name"] == "Fiscal name"


def test_client_partial_update_endpoint_is_active_ok(
    test_client: TestClient,
    client: Client,
    token_create: Token,
):
    response = test_client.patch(
        "/api/clients/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={"is_active": False},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["is_active"] is False


def test_clients_details_endpoint_ok(
    test_client: TestClient, token_create: Token, client: Client
):
    response = test_client.get(
        "/api/clients/1",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == client.id
    assert response_data["fiscal_name"] == client.fiscal_name
    assert response_data["alias"] == client.alias
    assert response_data["cif"] == client.cif


def test_clients_details_endpoint_not_token(test_client: TestClient):
    response = test_client.get("/api/clients/1")
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_AUTHENTICATED"
    assert response_data["detail"][0]["message"] == "Not authenticated"


def test_clients_details_endpoint_wrong_token(
    test_client: TestClient, token_create: Token
):
    response = test_client.get(
        "/api/clients/1", headers={"Authorization": "token faketoken"}
    )
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "INVALID_CREDENTIALS"
    assert response_data["detail"][0]["message"] == "Invalid authentication credentials"


def test_clients_details_endpoint_not_exist(
    test_client: TestClient, token_create: Token
):
    response = test_client.get(
        "/api/clients/1",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "client_not_exist"


def test_clients_details_endpoint_deleted(test_client: TestClient, token_create: Token):
    response = test_client.get(
        "/api/clients/4",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "client_not_exist"


def test_clients_delete_clients_endpoint_ok(
    test_client: TestClient, db_session: Session, token_create: Token, client: Client
):
    response = test_client.post(
        "/api/clients/delete",
        headers={"Authorization": f"token {token_create.token}"},
        json={"ids": [1, 2, 125]},
    )

    assert response.status_code == 200
    assert db_session.query(Client).count() == 0
