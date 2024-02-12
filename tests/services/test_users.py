import pytest
from pytest_mock import MockFixture
from sqlalchemy import false
from sqlalchemy.orm import Session
from starlette.background import BackgroundTasks
from starlette.exceptions import HTTPException

from src.infrastructure.email.email_config import EmailMessageSchema
from src.modules.users.models import Token, User
from src.modules.users.schemas import (
    ResetPasswordRequest,
    UserCreateRequest,
    UserDeleteRequest,
    UserFilter,
    UserLoginRequest,
    UserUpdatePartialRequest,
    UserUpdateRequest,
)
from src.services.users import (
    change_password,
    delete_users,
    forgot_password,
    generate_password_hash,
    get_or_create_user_token,
    get_user,
    list_users,
    login_user,
    logout_user,
    reset_password,
)
from src.services.users import user_create as user_create_service
from src.services.users import user_update, validate_password, verification_account
from utils.i18n import trans as _


def test_generate_password_hash(hashed_password_example: str):
    hashed_password = generate_password_hash("Fakepassword1234")
    assert hashed_password == hashed_password_example


def test_validate_password_true(hashed_password_example: str):
    assert validate_password("Fakepassword1234", hashed_password_example)


def test_validate_password_false(hashed_password_example: str):
    assert not validate_password("Anotherfakepassword1234", hashed_password_example)


def test_get_or_create_user_token(db_session: Session, user_create: User):
    token = get_or_create_user_token(db_session, user_create)
    assert token
    assert token.user == user_create


def test_login_user(db_session: Session, user_create: User):
    token = login_user(
        db_session,
        UserLoginRequest(email=user_create.email, password="Fakepassword1234"),
    )
    assert token


def test_login_user_wrong_password(db_session: Session, user_create: User):
    with pytest.raises(HTTPException) as exc:
        login_user(
            db_session,
            UserLoginRequest(email=user_create.email, password="WrongFakepassword1234"),
        )
    assert exc.value.status_code == 422
    assert exc.value.detail == "login_error"


def test_login_user_wrong_user(db_session: Session):
    with pytest.raises(HTTPException) as exc:
        login_user(
            db_session,
            UserLoginRequest(email="test@user.com", password="WrongFakepassword1234"),
        )
    assert exc.value.status_code == 422
    assert exc.value.detail == "login_error"


def test_login_user_inactive(db_session: Session, user_inactive_create: User):
    with pytest.raises(HTTPException) as exc:
        login_user(
            db_session,
            UserLoginRequest(email="test@user.com", password="Fakepassword1234"),
        )
    assert exc.value.status_code == 422
    assert exc.value.detail == "login_error"


def test_login_user_deleted(db_session: Session, user_deleted_create: User):
    with pytest.raises(HTTPException) as exc:
        login_user(
            db_session,
            UserLoginRequest(email="test@user.com", password="Fakepassword1234"),
        )
    assert exc.value.status_code == 422
    assert exc.value.detail == "login_error"


def test_logout_user(db_session: Session, token_create: Token):
    assert db_session.query(Token).count() == 1
    logout_user(db_session, token_create.user)
    assert db_session.query(Token).count() == 0


def test_verification_account_ok(user_create: User, mocker: MockFixture):
    email_message = EmailMessageSchema(
        subject=_("Test account created"),
        recipients=[user_create.email],
        parameters={
            "content_1": _("Hi"),
            "content_2": user_create.first_name,
            "content_3": _("You have requested a password change."),
            "content_4": _("to reset your password click on the following link:"),
            "content_5": _("Reset password"),
            "content_6": _("Thank you."),
            "content_7": _("Regards"),
        },
    )
    my_mock = mocker.patch("src.services.users.send_email")
    verification_account(user_create, email_message)
    my_mock.assert_called_once()


def test_forgot_password_ok(
    user_create: User, db_session: Session, mocker: MockFixture
):
    my_mock = mocker.patch("src.services.users.verification_account")
    forgot_password(db_session, user_create)
    my_mock.assert_called_once()


def test_forgot_password_user_not_found(
    user_create: User, db_session: Session, mocker: MockFixture
):
    my_mock = mocker.patch("src.services.users.verification_account")
    user = User()
    user.email = "not_existing@user.com"
    forgot_password(db_session, user)
    my_mock.assert_not_called()


def test_forgot_password_inactive_user(
    user_inactive_create: User, db_session: Session, mocker: MockFixture
):
    my_mock = mocker.patch("src.services.users.verification_account")
    forgot_password(db_session, user_inactive_create)
    my_mock.assert_not_called()


def test_forgot_password_deleted_user(
    user_deleted_create: User, db_session: Session, mocker: MockFixture
):
    my_mock = mocker.patch("src.services.users.verification_account")
    forgot_password(db_session, user_deleted_create)
    my_mock.assert_not_called()


def test_reset_password_ok(
    user_create: User,
    db_session: Session,
    fake_hash_sha256: str,
    expire_date_timestamp_valid: float,
):
    old_hash_pass = user_create.hashed_password

    reset_password(
        db_session,
        ResetPasswordRequest(
            password="FakeNewPass1234",
            user_id=user_create.id,
            hash=f"{expire_date_timestamp_valid}-{fake_hash_sha256}",
        ),
    )
    db_session.refresh(user_create)
    assert old_hash_pass != user_create.hashed_password


def test_reset_password_invalid_timestamp(
    user_create: User,
    db_session: Session,
    fake_hash_sha256: str,
):
    with pytest.raises(HTTPException) as exc:
        reset_password(
            db_session,
            ResetPasswordRequest(
                password="fakepass",
                user_id=user_create.id,
                hash=f"invalid_timestamp-{fake_hash_sha256}",
            ),
        )
    assert exc.value.detail == "timestamp_invalid"


def test_reset_password_incorrect_password(
    user_create: User,
    db_session: Session,
    fake_hash_sha256: str,
    expire_date_timestamp_valid: float,
):
    with pytest.raises(HTTPException) as exc:
        reset_password(
            db_session,
            ResetPasswordRequest(
                password="fakepass",
                user_id=user_create.id,
                hash=f"{expire_date_timestamp_valid}-{fake_hash_sha256}",
            ),
        )
    assert exc.value.detail == "invalid_password"


def test_reset_password_user_does_not_exist(
    db_session: Session, fake_hash_sha256: str, expire_date_timestamp_valid: float
):
    with pytest.raises(HTTPException) as exc:
        reset_password(
            db_session,
            ResetPasswordRequest(
                password="FakeNewPass1234",
                user_id=365,
                hash=f"{expire_date_timestamp_valid}-{fake_hash_sha256}",
            ),
        )
    assert exc.value.detail == "user_not_exist"


def test_reset_password_user_is_deleted(
    user_deleted_create: User,
    db_session: Session,
    fake_hash_sha256: str,
    expire_date_timestamp_valid: float,
):
    with pytest.raises(HTTPException) as exc:
        reset_password(
            db_session,
            ResetPasswordRequest(
                password="FakeNewPass1234",
                user_id=user_deleted_create.id,
                hash=f"{expire_date_timestamp_valid}-{fake_hash_sha256}",
            ),
        )
    assert exc.value.detail == "user_not_exist"


def test_reset_password_user_is_inactive(
    user_inactive_create: User,
    db_session: Session,
    fake_hash_sha256: str,
    expire_date_timestamp_valid: float,
):
    with pytest.raises(HTTPException) as exc:
        reset_password(
            db_session,
            ResetPasswordRequest(
                password="FakeNewPass1234",
                user_id=user_inactive_create.id,
                hash=f"{expire_date_timestamp_valid}-{fake_hash_sha256}",
            ),
        )
    assert exc.value.detail == "user_not_exist"


def test_reset_password_invalid_hash(
    user_create: User,
    db_session: Session,
    expire_date_timestamp_valid: float,
):
    with pytest.raises(HTTPException) as exc:
        reset_password(
            db_session,
            ResetPasswordRequest(
                password="FakeNewPass1234",
                user_id=user_create.id,
                hash=f"{expire_date_timestamp_valid}-invalid_hash",
            ),
        )
    assert exc.value.detail == "invalid_token"


def test_reset_password_invalid_url(
    user_create: User,
    db_session: Session,
    expire_date_timestamp_valid: float,
    fake_hash_sha256_invalid: str,
):
    with pytest.raises(HTTPException) as exc:
        reset_password(
            db_session,
            ResetPasswordRequest(
                password="FakeNewPass1234",
                user_id=user_create.id,
                hash=f"{expire_date_timestamp_valid}-{fake_hash_sha256_invalid}",
            ),
        )
    assert exc.value.detail == "invalid_url"


def test_reset_password_url_expired(
    user_create: User,
    db_session: Session,
    fake_hash_sha256: str,
    expire_date_timestamp_invalid: float,
):
    with pytest.raises(HTTPException) as exc:
        reset_password(
            db_session,
            ResetPasswordRequest(
                password="FakeNewPass1234",
                user_id=user_create.id,
                hash=f"{expire_date_timestamp_invalid}-{fake_hash_sha256}",
            ),
        )
    assert exc.value.detail == "expired_url"


def test_user_create_ok(db_session: Session, user_create: User, mocker: MockFixture):
    background_tasks = BackgroundTasks()
    my_mock = mocker.spy(background_tasks, "add_task")

    user = user_create_service(
        db_session,
        UserCreateRequest(
            email="TesT@Email.COM", first_name="Test", last_name="Test", role="admin"
        ),
        user_create,
        background_tasks,
    )
    my_mock.assert_called_once()
    assert user.id
    assert db_session.query(User).count() == 2
    assert user.email == "test@email.com"
    assert user.responsible_id == user_create.id


def test_user_create_email_ip_domain_ok(
    db_session: Session, user_create: User, mocker: MockFixture
):
    background_tasks = BackgroundTasks()
    my_mock = mocker.spy(background_tasks, "add_task")

    user = user_create_service(
        db_session,
        UserCreateRequest(
            email="email@111.222.333.44444",
            first_name="Test",
            last_name="Test",
            role="admin",
        ),
        user_create,
        background_tasks,
    )
    my_mock.assert_called_once()
    assert user.id
    assert db_session.query(User).count() == 2
    assert user.email == "email@111.222.333.44444"
    assert user.responsible_id == 1


def test_user_create_email_already_exists(
    db_session: Session, user_create: User, mocker: MockFixture
):
    background_tasks = BackgroundTasks()
    my_mock = mocker.spy(background_tasks, "add_task")

    with pytest.raises(HTTPException) as exc:
        user_create_service(
            db_session,
            UserCreateRequest(
                email="TEST@USER.COM", first_name="Test", last_name="Test", role="admin"
            ),
            user_create,
            background_tasks,
        )

    my_mock.assert_not_called()
    assert exc.value.detail == "email_already_exists"
    assert db_session.query(User).count() == 1


def test_user_update_ok(db_session: Session, user_create: User, mocker: MockFixture):
    background_tasks = BackgroundTasks()
    my_mock = mocker.spy(background_tasks, "add_task")
    user_update(
        db_session,
        user_create.id,
        UserUpdateRequest(
            first_name="Another Name",
            last_name="Another surnames",
            email="another@email.com",
            password="AnotherPW123",
            role="admin",
        ),
        False,
        background_tasks,
        user_create,
    )

    my_mock.assert_called_once()
    user = db_session.query(User).filter(User.id == user_create.id).first()
    assert user.first_name == "Another Name"
    assert user.last_name == "Another surnames"
    assert user.email == "another@email.com"
    assert user.role == "admin"
    assert user.hashed_password == (
        "$argon2id$v=19$m=65536,t=2,p=4$RHVtbXktU2VjcmV0LUtFWQ$k8O/ijxW6nhjmM+96nSGW5C86WMzePGQa+vBRB4dvIA"
    )


def test_user_update_without_password(
    db_session: Session,
    user_create: User,
    hashed_password_example: str,
    mocker: MockFixture,
):
    background_tasks = BackgroundTasks()
    my_mock = mocker.spy(background_tasks, "add_task")
    user_update(
        db_session,
        user_create.id,
        UserUpdateRequest(
            first_name="Another Name",
            last_name="Another surnames",
            email="another@email.com",
            role="admin",
        ),
        False,
        background_tasks,
        user_create,
    )

    my_mock.assert_not_called()
    user = db_session.query(User).filter(User.id == user_create.id).first()
    assert user.first_name == "Another Name"
    assert user.last_name == "Another surnames"
    assert user.email == "another@email.com"
    assert user.role == "admin"
    assert user.hashed_password == hashed_password_example


def test_user_update_partial(
    db_session: Session, user_create: User, mocker: MockFixture
):
    background_tasks = BackgroundTasks()
    my_mock = mocker.spy(background_tasks, "add_task")
    user_update(
        db_session,
        user_create.id,
        UserUpdatePartialRequest(
            email="another@email.com",
        ),
        True,
        background_tasks,
        user_create,
    )

    my_mock.assert_not_called()
    user = db_session.query(User).filter(User.id == user_create.id).first()
    assert user.email == "another@email.com"


def test_user_update_partial_bad_password(db_session: Session, user_create: User):
    with pytest.raises(HTTPException) as exc:
        user_update(
            db_session,
            user_create.id,
            UserUpdatePartialRequest(
                password="bad_password",
            ),
            True,
            BackgroundTasks(),
            user_create,
        )
    assert exc.value.detail == ("invalid_password")


def test_user_update_partial_not_exists(db_session: Session, user_create2: User):
    with pytest.raises(HTTPException) as exc:
        user_update(
            db_session,
            1,
            UserUpdatePartialRequest(
                password="bad_password",
            ),
            True,
            BackgroundTasks(),
            user_create2,
        )
    assert exc.value.detail == "user_not_exist"


def test_user_update_partial_deleted(db_session: Session, user_deleted_create: User):
    with pytest.raises(HTTPException) as exc:
        user_update(
            db_session,
            1,
            UserUpdatePartialRequest(
                password="bad_password",
            ),
            True,
            BackgroundTasks(),
            user_deleted_create,
        )
    assert exc.value.detail == "user_not_exist"


def test_user_update_partial_email_already_exists(
    db_session: Session, user_create: User, user_create2: User
):
    with pytest.raises(HTTPException) as exc:
        user_update(
            db_session,
            1,
            UserUpdatePartialRequest(
                email="test2@user.com",
            ),
            True,
            BackgroundTasks(),
            user_create2,
        )
    assert exc.value.detail == "email_already_exists"


def test_user_update_partial_change_same_email(
    db_session: Session, user_create: User, user_create2: User
):
    user_update(
        db_session,
        1,
        UserUpdatePartialRequest(
            email="test@user.com",
            first_name="Another name",
        ),
        True,
        BackgroundTasks(),
        user_create2,
    )

    user = db_session.query(User).filter(User.id == user_create.id).first()
    assert user.email == "test@user.com"
    assert user.first_name == "Another name"


def test_get_user_ok(db_session: Session, user_create: User):
    user = get_user(db_session, 1)

    assert user


def test_get_user_deleted(db_session: Session, user_deleted_create: User):
    with pytest.raises(HTTPException) as exc:
        get_user(db_session, 3)

    assert exc.value.status_code == 404
    assert exc.value.detail == "user_not_exist"


def test_get_user_does_not_exists(db_session: Session, user_create: User):
    with pytest.raises(HTTPException) as exc:
        get_user(db_session, 2)

    assert exc.value.status_code == 404
    assert exc.value.detail == "user_not_exist"


def test_change_password_ok(
    user_create: User, db_session: Session, hashed_password_example: str
):
    change_password(db_session, user_create, "Fakepassword1234", "Newfakepass1234")
    db_session.refresh(user_create)
    assert hashed_password_example != user_create.hashed_password


def test_change_password_incorrect_old_password(
    user_create: User, db_session: Session, hashed_password_example: str
):
    with pytest.raises(HTTPException) as exc:
        change_password(
            db_session, user_create, "Notoldpassword1234", "Newfakepass1234"
        )
        assert exc.value.detail == "incorrect_old_password"
    db_session.refresh(user_create)
    assert hashed_password_example == user_create.hashed_password


def test_change_password_invalid_new_password(
    user_create: User, db_session: Session, hashed_password_example: str
):
    with pytest.raises(HTTPException) as exc:
        change_password(db_session, user_create, "Fakepassword1234", "fakepass1234")
        assert exc.value.detail == ("invalid_password")
    db_session.refresh(user_create)
    assert hashed_password_example == user_create.hashed_password


def test_list_users_ok(
    user_create: User,
    db_session: Session,
    user_create2: User,
    user_inactive_create: User,
    user_deleted_create: User,
):
    """
    user_create and user_create2 are two regular users
    user_inactive_create is an inactive user
    user_deleted_create is a deleted user

    The result should exclude the deleted user and the user that
    sent the request
    """
    user_create2.responsible = user_inactive_create

    users_qs = list_users(db_session, UserFilter(), user_create)
    assert users_qs.count() == 2
    users = users_qs.order_by(User.id).all()
    assert users[1].id == 2
    assert users[0].id == 5
    assert users[1].first_name == "Johnathan"
    assert users[1].last_name == "Smith"
    assert users[1].email == "test2@user.com"
    assert users[1].role == "admin"
    assert users[1].create_at
    assert users[1].is_active is True
    assert users[1].responsible.first_name == "Inactivename"
    assert users[1].responsible.last_name == "Inactivesurname"


def test_delete_users_ok(
    db_session: Session,
    user_create: User,
    user_create2: User,
    user_create3: User,
    user_inactive_create: User,
):
    delete_users(db_session, UserDeleteRequest(ids=[1, 2, 6, 84]))

    assert db_session.query(User).filter(User.is_deleted == false()).count() == 1


def test_delete_users_empty_ok(
    db_session: Session,
    user_create: User,
    user_create2: User,
    user_create3: User,
    user_inactive_create: User,
):
    delete_users(db_session, UserDeleteRequest(ids=[]))

    assert db_session.query(User).filter(User.is_deleted == false()).count() == 4
