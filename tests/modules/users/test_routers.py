import datetime

from fastapi.testclient import TestClient
from sqlalchemy import false
from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.users import get_user_by
from src.modules.users.models import Token, User


def test_login_endpoint_ok(test_client: TestClient, user_create: User):
    response = test_client.post(
        "/api/users/login",
        json={
            "email": "test@user.com",
            "password": "Fakepassword1234",
        },
    )
    assert response.status_code == 200
    response_data = response.json()
    assert "token" in response_data
    assert "user" in response_data
    assert response_data["user"]["first_name"] == "John"
    assert response_data["user"]["last_name"] == "Graham"


def test_login_endpoint_error_NOT_EXIST(test_client: TestClient):
    response = test_client.post(
        "/api/users/login",
        json={
            "email": "test@user.com",
            "password": "Fakepassword1234",
        },
    )
    assert response.status_code == 422
    response_data = response.json()
    assert (
        response_data["detail"][0]["message"]
        == "There is an error with the login information"
    )
    assert response_data["detail"][0]["code"] == "LOGIN_ERROR"


def test_login_endpoint_error_password(test_client: TestClient, user_create: User):
    response = test_client.post(
        "/api/users/login",
        json={
            "email": "test@user.com",
            "password": "WrongFakepassword1234",
        },
    )
    assert response.status_code == 422
    response_data = response.json()
    assert (
        response_data["detail"][0]["message"]
        == "There is an error with the login information"
    )
    assert response_data["detail"][0]["code"] == "LOGIN_ERROR"


def test_users_forgot_password_ok(test_client: TestClient, user_create: User):
    response = test_client.post(
        "/api/users/forgot-password", json={"email": "test@user.com"}
    )
    assert response.status_code == 204


def test_users_forgot_password_user_not_found(
    test_client: TestClient, user_create: User
):
    response = test_client.post(
        "/api/users/forgot-password", json={"email": "not_existing@user.com"}
    )
    assert response.status_code == 204


def test_users_forgot_password_no_email(test_client: TestClient, user_create: User):
    response = test_client.post("/api/users/forgot-password", json={"email": None})
    assert response.status_code == 422
    assert response.json()["detail"][0]["message"] == "None is not an allowed value"


def test_users_forgot_password_no_arguments(test_client: TestClient, user_create: User):
    response = test_client.post("/api/users/forgot-password")
    assert response.status_code == 422
    assert response.json()["detail"][0]["message"] == "Field required"


def test_users_me_ok(test_client: TestClient, token_create: Token):
    response = test_client.get(
        "/api/users/me/", headers={"Authorization": f"token {token_create.token}"}
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["first_name"] == "John"
    assert response_data["last_name"] == "Graham"
    assert response_data["role"] == "admin"
    assert response_data["is_superadmin"] is False


def test_users_me_not_token(test_client: TestClient):
    response = test_client.get("/api/users/me/")
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["detail"][0]["message"] == "Not authenticated"
    assert response_data["detail"][0]["code"] == "NOT_AUTHENTICATED"


def test_users_me_wrong_token(test_client: TestClient, token_create: Token):
    response = test_client.get(
        "/api/users/me/", headers={"Authorization": "token faketoken"}
    )
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["detail"][0]["message"] == "Invalid authentication credentials"
    assert response_data["detail"][0]["code"] == "INVALID_CREDENTIALS"


def test_user_logout_endpoint(
    test_client: TestClient, token_create: Token, db_session: Session
):
    assert db_session.query(Token).count() == 1
    response = test_client.post(
        "/api/users/logout", headers={"Authorization": f"token {token_create.token}"}
    )
    assert response.status_code == 204
    assert db_session.query(Token).count() == 0


def test_user_reset_password_ok(
    test_client: TestClient,
    user_create: User,
    db_session: Session,
    fake_hash_sha256: str,
    expire_date_timestamp_valid: float,
):
    old_hash_password = user_create.hashed_password
    response = test_client.post(
        "/api/users/reset-password",
        json={
            "password": "NewFakePass1234",
            "user_id": 1,
            "hash": f"{expire_date_timestamp_valid}-{fake_hash_sha256}",
        },
    )
    assert response.status_code == 204
    modified_user = get_user_by(db_session, User.id == 1)
    assert modified_user.hashed_password != old_hash_password


def test_user_reset_password_invalid_password(
    test_client: TestClient,
    user_create: User,
    db_session: Session,
    fake_hash_sha256: str,
    expire_date_timestamp_valid: float,
):
    old_hash_password = user_create.hashed_password
    response = test_client.post(
        "/api/users/reset-password",
        json={
            "password": "fakepass",
            "user_id": 1,
            "hash": f"{expire_date_timestamp_valid}-{fake_hash_sha256}",
        },
    )
    assert response.status_code == 422
    response_data = response.json()
    assert (
        response_data["detail"][0]["message"] == "The password does not meet"
        " the password policy requirements"
    )
    assert response_data["detail"][0]["code"] == "INVALID_PASSWORD"
    modified_user = get_user_by(db_session, User.id == 1)
    assert modified_user.hashed_password == old_hash_password


def test_user_change_password(
    test_client: TestClient,
    user_create: User,
    token_create: Token,
    db_session: Session,
    hashed_password_example: str,
):
    response = test_client.post(
        "/api/users/change-password",
        headers={"Authorization": f"token {token_create.token}"},
        json={"old_password": "Fakepassword1234", "new_password": "Newfakepass1234"},
    )
    modified_user = get_user_by(db_session, User.id == 1)
    assert response.status_code == 204
    assert hashed_password_example != modified_user.hashed_password


def test_user_create_endpoint_error_email_already_exists(
    test_client: TestClient, token_create: Token, db_session: Session
):
    response = test_client.post(
        "/api/users",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "first_name": "Name",
            "last_name": "Surnames",
            "email": "test@user.com",
            "role": "admin",
        },
    )
    assert response.status_code == 422
    response_data = response.json()
    assert response_data["detail"][0]["message"] == "User email already exists"
    assert response_data["detail"][0]["code"] == "EMAIL_ALREADY_EXISTS"
    assert db_session.query(User).count() == 1


def test_user_create_endpoint_error_field_too_long(
    test_client: TestClient, token_create: Token, db_session: Session
):
    response = test_client.post(
        "/api/users",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "first_name": "Name qwertyqwertyqwertyqwertyqwertyqwertyqwertyqwertyqwerty "
            "qwertyqwertyqwertyqwertyqwertyqwertyqwertyqwertyqwerty "
            "qwertyqwertyqwertyqwertyqwertyqwertyqwertyqwertyqwerty",
            "last_name": "Surnames",
            "email": "test@user.com",
            "role": "admin",
        },
    )
    assert response.status_code == 422
    response_data = response.json()
    assert (
        response_data["detail"][0]["message"]
        == "ensure this value has at most 32 characters"
    )
    assert response_data["detail"][0]["code"] == "value_error.any_str.max_length"
    assert db_session.query(User).count() == 1


def test_user_create_endpoint_ok(
    test_client: TestClient, token_create: Token, db_session: Session
):
    response = test_client.post(
        "/api/users",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "first_name": "Name",
            "last_name": "Surnames",
            "email": "test2@user.com",
            "role": "admin",
        },
    )

    assert response.status_code == 201
    assert db_session.query(User).count() == 2


def test_user_update_endpoint_ok(test_client: TestClient, token_create: Token):
    response = test_client.put(
        f"/api/users/{token_create.user_id}",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "first_name": "Another name",
            "last_name": "Another surnames",
            "email": "another@email.com",
            "password": "AnotherPW123",
            "role": "super_admin",
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["first_name"] == "Another name"
    assert response_data["last_name"] == "Another surnames"
    assert response_data["email"] == "another@email.com"
    assert response_data["role"] == "super_admin"


def test_user_update_endpoint_without_password(
    test_client: TestClient, token_create: Token
):
    response = test_client.put(
        f"/api/users/{token_create.user_id}",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "first_name": "Another name",
            "last_name": "Another surnames",
            "email": "another@email.com",
            "role": "super_admin",
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["first_name"] == "Another name"
    assert response_data["last_name"] == "Another surnames"
    assert response_data["email"] == "another@email.com"
    assert response_data["role"] == "super_admin"


def test_user_update_endpoint_not_user_auth(
    test_client: TestClient, token_create: Token
):
    response = test_client.put(
        f"/api/users/{token_create.user_id}",
        headers={"Authorization": "token fake_token"},
        json={
            "first_name": "Another name",
            "last_name": "Another surnames",
            "email": "another@email.com",
            "password": "AnotherPW123",
            "role": "super_admin",
        },
    )

    assert response.status_code == 401


def test_user_update_endpoint_NOT_EXIST(test_client: TestClient, token_create: Token):
    response = test_client.put(
        "/api/users/99",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "first_name": "Another name",
            "last_name": "Another surnames",
            "email": "another@email.com",
            "password": "AnotherPW123",
            "role": "super_admin",
        },
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["message"] == "The user does not exist"
    assert response_data["detail"][0]["code"] == "NOT_EXIST"


def test_user_update_endpoint_bad_password(
    test_client: TestClient, token_create: Token
):
    response = test_client.put(
        f"/api/users/{token_create.user_id}",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "first_name": "Another name",
            "last_name": "Another sur   names",
            "email": "another@email.com",
            "password": "bad_password",
            "role": "super_admin",
        },
    )

    assert response.status_code == 422
    response_data = response.json()
    assert (
        response_data["detail"][0]["message"]
        == "The password does not meet the password policy requirements"
    )
    assert response_data["detail"][0]["code"] == "INVALID_PASSWORD"


def test_user_update_partial_endpoint_ok(test_client: TestClient, token_create: Token):
    response = test_client.patch(
        f"/api/users/{token_create.user_id}",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "first_name": "Another name",
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["first_name"] == "Another name"
    assert response_data["last_name"] == "Graham"
    assert response_data["email"] == "test@user.com"


def test_user_update_partial_endpoint_disable(
    test_client: TestClient, token_create: Token, db_session: Session
):
    response = test_client.patch(
        f"/api/users/{token_create.user_id}",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 200
    user = db_session.query(User).filter(User.id == 1).first()
    assert user.is_active is False


def test_user_update_partial_endpoint_delete(
    test_client: TestClient, token_create: Token, db_session: Session
):
    response = test_client.patch(
        f"/api/users/{token_create.user_id}",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "is_deleted": True,
        },
    )

    assert response.status_code == 200
    user = db_session.query(User).filter(User.id == 1).first()
    assert user.is_deleted is True
    assert user.email == "1test@user.com"
    assert (datetime.datetime.utcnow() - user.deleted_at).total_seconds() < 5


def test_user_update_partial_endpoint_not_user_auth(
    test_client: TestClient, token_create: Token, db_session: Session
):
    response = test_client.patch(
        f"/api/users/{token_create.user_id}",
        headers={"Authorization": "token fake_token"},
        json={
            "first_name": "Another name",
        },
    )

    assert response.status_code == 401


def test_user_update_partial_endpoint_NOT_EXIST(
    test_client: TestClient, token_create: Token, db_session: Session
):
    response = test_client.patch(
        "/api/users/99",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "first_name": "Another name",
        },
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["message"] == "The user does not exist"
    assert response_data["detail"][0]["code"] == "NOT_EXIST"


def test_user_update_partial_endpoint_user_deleted(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    user_deleted_create: User,
):
    response = test_client.patch(
        "/api/users/3",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "first_name": "Another name",
        },
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["message"] == "The user does not exist"
    assert response_data["detail"][0]["code"] == "NOT_EXIST"


def test_user_update_partial_endpoint_bad_password(
    test_client: TestClient, token_create: Token, db_session: Session
):
    response = test_client.patch(
        f"/api/users/{token_create.user_id}",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "password": "bad_password",
        },
    )

    assert response.status_code == 422
    response_data = response.json()
    assert (
        response_data["detail"][0]["message"]
        == "The password does not meet the password policy requirements"
    )
    assert response_data["detail"][0]["code"] == "INVALID_PASSWORD"


def test_user_detail_endpoint_ok(
    test_client: TestClient, token_create: Token, superadmin: User
):
    token_create.user.responsible = superadmin

    response = test_client.get(
        "/api/users/1", headers={"Authorization": f"token {token_create.token}"}
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["first_name"] == "John"
    assert response_data["last_name"] == "Graham"
    assert response_data["role"] == "admin"
    assert response_data["responsible"]["first_name"] == "super"
    assert response_data["responsible"]["last_name"] == "admin"
    assert response_data["is_superadmin"] is False


def test_user_detail_endpoint_deleted(
    test_client: TestClient, token_create: Token, user_deleted_create: User
):
    response = test_client.get(
        "/api/users/3", headers={"Authorization": f"token {token_create.token}"}
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["source"] == "path"
    assert response_data["detail"][0]["field"] == "path_param"
    assert response_data["detail"][0]["message"] == "The user does not exist"
    assert response_data["detail"][0]["code"] == "NOT_EXIST"


def test_user_detail_endpoint_does_not_exists(
    test_client: TestClient, token_create: Token
):
    response = test_client.get(
        "/api/users/99", headers={"Authorization": f"token {token_create.token}"}
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["source"] == "path"
    assert response_data["detail"][0]["field"] == "path_param"
    assert response_data["detail"][0]["message"] == "The user does not exist"
    assert response_data["detail"][0]["code"] == "NOT_EXIST"


def test_list_users_endpoint_ok(
    test_client: TestClient,
    user_create: User,
    user_create2: User,
    superadmin: User,
    user_deleted_create: User,
    token_create: Token,
):
    user_create2.responsible = user_create
    superadmin.responsible = user_deleted_create

    response = test_client.get(
        "/api/users/",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data["items"]) == 2
    assert response_data["total"] == 2
    assert response_data["page"] == 1
    assert response_data["size"] == 50
    assert response_data["items"][1]["id"] == 2
    assert response_data["items"][0]["id"] == 4
    assert response_data["items"][0]["first_name"]
    assert response_data["items"][0]["last_name"]
    assert response_data["items"][0]["email"]
    assert response_data["items"][0]["create_at"]
    assert response_data["items"][0]["is_active"]
    assert response_data["items"][0]["role"] == "super_admin"
    assert response_data["items"][0]["responsible"]
    assert response_data["items"][0]["responsible"]["id"]
    assert response_data["items"][0]["responsible"]["first_name"]
    assert response_data["items"][0]["responsible"]["last_name"]


def test_users_list_endpoint_filter_responsible_first_name_ok(
    test_client: TestClient,
    token_superadmin: Token,
    db_session: Session,
    user_create: User,
    user_create2: User,
):
    user_create.responsible = user_create2

    response = test_client.get(
        "/api/users?responsible__first_name__unaccent=JóhNa",
        headers={"Authorization": f"token {token_superadmin.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 1
    assert response_data["items"][0]["responsible"]["id"] == 2
    assert response_data["items"][0]["responsible"]["first_name"] == "Johnathan"


def test_users_list_endpoint_filter_create_at_like_ok(
    test_client: TestClient,
    token_superadmin: Token,
    db_session: Session,
    user_create: User,
    user_create2: User,
):
    user_create.create_at = datetime.datetime(2022, 1, 1, 16, 30)

    response = test_client.get(
        "/api/users?create_at__gte=2022-01-01T00:00:00.000Z&create_at__lt=2022-01-02T00:00:00.000Z",
        headers={"Authorization": f"token {token_superadmin.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 1
    response_data["items"][0]["create_at"] == "2022-01-01T16:30:00"


def test_users_list_endpoint_filter_order_by_responsible_first_name_ok(
    test_client: TestClient,
    token_create: Token,
    user_create2: User,
    user_create3: User,
    user_inactive_create: User,
    superadmin: User,
):
    user_create3.responsible = user_create2
    user_create2.responsible = superadmin
    user_inactive_create.responsible = user_create3

    response = test_client.get(
        "/api/users?page=1&size=50&order_by=responsible__first_name",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 4
    assert response_data["items"][0]["responsible"]["first_name"] == "Emma"
    assert response_data["items"][1]["responsible"]["first_name"] == "Johnathan"
    assert response_data["items"][2]["responsible"]["first_name"] == "super"
    assert not response_data["items"][3]["responsible"]


def test_users_list_endpoint_filter_order_by_desc_responsible_first_name_ok(
    test_client: TestClient,
    token_create: Token,
    user_create2: User,
    user_create3: User,
    user_inactive_create: User,
    superadmin: User,
):
    user_create3.responsible = user_create2
    user_create2.responsible = superadmin
    user_inactive_create.responsible = user_create3

    response = test_client.get(
        "/api/users?page=1&size=50&order_by=-responsible__first_name",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 4
    assert response_data["items"][3]["responsible"]["first_name"] == "Emma"
    assert response_data["items"][2]["responsible"]["first_name"] == "Johnathan"
    assert response_data["items"][1]["responsible"]["first_name"] == "super"
    assert not response_data["items"][0]["responsible"]


def test_users_list_endpoint_filter_order_by_first_name_ok(
    test_client: TestClient,
    token_create: Token,
    user_create2: User,
    user_create3: User,
    superadmin: User,
):
    response = test_client.get(
        "/api/users?order_by=first_name",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 3
    assert response_data["items"][0]["first_name"] == "Emma"
    assert response_data["items"][1]["first_name"] == "Johnathan"
    assert response_data["items"][2]["first_name"] == "super"


def test_users_list_endpoints_after_delete_ok(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    user_create2: User,
    user_create3: User,
    superadmin: User,
):
    response_first_list = test_client.get(
        "/api/users",
        headers={
            "authorization": f"token {token_create.token}",
            "accept": "application/json, text/plain, */*",
            "accept-language": "es-ES,es;q=0.9",
            "sec-ch-ua": "Chromium';v='110', 'Not A(Brand';v='24', 'Google Chrome';v='110'",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Linux",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safar)i/537.36"
            ),
        },
    )

    response_delete_user = test_client.patch(
        "/api/users/2",
        headers={
            "authorization": f"token {token_create.token}",
            "accept": "application/json, text/plain, */*",
            "accept-language": "es-ES,es;q=0.9",
            "sec-ch-ua": "Chromium';v='110', 'Not A(Brand';v='24', 'Google Chrome';v='110'",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Linux",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safar)i/537.36"
            ),
        },
        json={
            "is_deleted": True,
        },
    )

    response_list_after_delete = test_client.get(
        "/api/users",
        headers={
            "authorization": f"token {token_create.token}",
            "accept": "application/json, text/plain, */*",
            "accept-language": "es-ES,es;q=0.9",
            "sec-ch-ua": "Chromium';v='110', 'Not A(Brand';v='24', 'Google Chrome';v='110'",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Linux",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safar)i/537.36"
            ),
        },
    )

    response_data_first_list = response_first_list.json()
    response_data_delete_user = response_delete_user.json()
    response_data_list_after_delete = response_list_after_delete.json()
    deleted_user = db_session.query(User).filter(User.id == 2).first()

    assert response_first_list.status_code == 200
    assert response_data_first_list["total"] == 3
    assert response_delete_user.status_code == 200
    assert response_data_delete_user["id"] == 2
    assert deleted_user.is_deleted is True
    assert response_list_after_delete.status_code == 200
    assert response_data_list_after_delete["total"] == 2


def test_users_list_endpoint_filter_search_foreign_key_ok(
    test_client: TestClient,
    token_create: Token,
    user_create: User,
    user_create2: User,
    user_inactive_create: User,
    superadmin: User,
):
    user_inactive_create.responsible = user_create
    user_create2.responsible = superadmin

    response = test_client.get(
        "/api/users?responsible__search=joh",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 1
    assert response_data["items"][0]["id"] == 5
    assert response_data["items"][0]["responsible"]["first_name"] == "John"
    assert response_data["items"][0]["first_name"] == "Inactivename"


def test_users_delete_users_endpoint_ok(
    test_client: TestClient,
    db_session: Session,
    token_create: Token,
    user_create: User,
    user_create2: User,
    user_inactive_create: User,
):
    response = test_client.post(
        "/api/users/delete",
        headers={"Authorization": f"token {token_create.token}"},
        json={"ids": [1, 5, 125]},
    )

    assert response.status_code == 200
    assert db_session.query(User).filter(User.is_deleted == false()).count() == 1


def test_users_export_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    user_create: User,
    user_create2: User,
    user_inactive_create: User,
):
    response = test_client.post(
        "/api/users/export/csv",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    # Check the begining of the file until the create_at value
    lines = response.text.split("\r\n")
    assert len(lines) == 4
    assert len(lines[0].split(";")) == 9
    assert len(lines[1].split(";")) == 9
    assert len(lines[2].split(";")) == 9
    assert lines[3].split(";")[0] == ""
    print(response.text)
    assert response.text.startswith(
        "Id;First name;last name;Email address;Role;Is active;"
        "Responsible first name;Responsible last name;Date"
    )


def test_users_export_endpoint_by_ids_ok(
    test_client: TestClient,
    token_create: Token,
    user_create: User,
    user_create2: User,
    user_inactive_create: User,
):
    response = test_client.post(
        "/api/users/export/csv?id__in=1,5",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    # Check the begining of the file until the create_at value filtering by ids
    lines = response.text.split("\r\n")
    assert len(lines) == 3
    assert len(lines[0].split(";")) == 9
    assert len(lines[1].split(";")) == 9
    assert lines[2].split(";")[0] == ""
    assert response.text.startswith(
        "Id;First name;last name;Email address;Role;Is active;"
        "Responsible first name;Responsible last name;Date\r\n5;Inactivename;"
        "Inactivesurname;inactive@user.com;admin;False;;;"
    )
