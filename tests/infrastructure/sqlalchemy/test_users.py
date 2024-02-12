from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.users import (
    create_user_db,
    delete_token,
    get_or_create_token,
    get_token_by,
    get_user_by,
    get_users_queryset,
)
from src.modules.users.models import Token, User


def test_get_user_by_one_field(user_create: User, db_session: Session):
    user = get_user_by(db_session, User.email == "test@user.com")
    assert user.email == "test@user.com"


def test_get_user_by_multiple_fields(user_create: User, db_session: Session):
    user = get_user_by(
        db_session,
        User.email == "test@user.com",
        User.first_name == "John",
        User.last_name == "Graham",
    )
    assert user.email == "test@user.com"
    assert user.first_name == "John"
    assert user.last_name == "Graham"


def test_get_user_by_without_fields(
    user_create: User, user_create2: User, db_session: Session
):
    user = get_user_by(db_session)
    assert user.email == "test@user.com"
    assert user.first_name == "John"
    assert user.last_name == "Graham"


def test_get_user_by_none(user_create: User, db_session: Session):
    user = get_user_by(db_session, User.email == "test2@user.com")
    assert user is None


def test_get_users_queryset_user_created_by(
    user_create: User, db_session: Session, user_create2: User
):
    user_create2.responsible = user_create
    db_session.commit()
    users_qs = get_users_queryset(db_session, [User.responsible])
    assert users_qs.count() == 2
    users = users_qs.order_by(User.id).all()
    assert users[1].responsible_id == 1
    assert users[1].responsible == user_create


def test_get_users_queryset_without_fields(
    user_create: User, db_session: Session, user_create2: User
):
    users_qs = get_users_queryset(db_session)
    assert users_qs.count() == 2


def test_get_users_queryset_one_field(
    user_create: User, db_session: Session, user_create2: User
):
    users_qs = get_users_queryset(db_session, None, User.email == "test@user.com")
    assert users_qs.count() == 1


def test_get_users_queryset_multiple_fields(
    user_create: User, db_session: Session, user_create2: User
):
    users_qs = get_users_queryset(
        db_session,
        None,
        User.email == "test@user.com",
        User.first_name == "John",
        User.last_name == "Graham",
    )
    assert users_qs.count() == 1
    users = users_qs.all()
    assert users[0].email == "test@user.com"
    assert users[0].first_name == "John"
    assert users[0].last_name == "Graham"


def test_get_users_queryset_none(user_create: User, db_session: Session):
    users_qs = get_users_queryset(db_session, None, User.email == "test2@user.com")
    assert users_qs.count() == 0


def test_get_users_queryset_with_join_list(db_session: Session, user_create: User):
    assert get_users_queryset(db_session, [User.responsible]).count() == 1


def test_get_users_queryset_with_filter(
    db_session: Session, user_create: User, user_create2: User
):
    assert get_users_queryset(db_session, None, User.id == 1).count() == 1


def test_get_users_queryset_with_filter_and_join_list(
    db_session: Session, user_create: User, user_create2: User
):
    assert get_users_queryset(db_session, [User.responsible], User.id == 1).count() == 1


def test_get_token_by_one_field(token_create: Token, db_session: Session):
    token = get_token_by(db_session, Token.user_id == token_create.user_id)
    assert token.token == "SDFGegwew56452367"
    assert token.user == token_create.user


def test_get_token_by_multiple_fields(token_create: Token, db_session: Session):
    token = get_token_by(
        db_session,
        Token.user_id == token_create.user_id,
        Token.token == "SDFGegwew56452367",
    )
    assert token.token == "SDFGegwew56452367"
    assert token.user == token_create.user


def test_get_token_by_none(token_create: Token, db_session: Session):
    token = get_token_by(db_session, Token.token == "another-token")
    assert token is None


def test_get_or_create_token_without_token(user_create: User, db_session: Session):
    token = get_or_create_token(db_session, user_create)
    assert token


def test_get_or_create_token_with_token(token_create: Token, db_session: Session):
    token = get_or_create_token(db_session, token_create.user)
    assert token == token_create


def test_delete_token_with_one_token(token_create: Token, db_session: Session):
    assert db_session.query(Token).count() == 1
    delete_token(db_session)
    assert db_session.query(Token).count() == 0


def test_delete_token_with_conditions(
    token_create: Token, db_session: Session, user_create2: User
):
    token = Token(
        token="another_token",
        user_id=user_create2.id,
    )
    db_session.add(token)
    db_session.commit()

    assert db_session.query(Token).count() == 2
    delete_token(db_session, Token.user_id == token_create.user_id)
    assert db_session.query(Token).count() == 1


def test_create_user_db_no_created_by_ok(db_session: Session):
    user = User(
        email="TesT@email.COM",
        first_name="Name",
        last_name="Surnames",
    )

    db_user = create_user_db(db_session, user)
    assert db_user.id
    assert db_session.query(User).count() == 1


def test_create_user_db_ok(db_session: Session, user_create):
    user = User(
        email="TesT@email.COM",
        first_name="Name",
        last_name="Surnames",
        responsible_id=1,
    )

    db_user = create_user_db(db_session, user)
    assert db_user.id
    assert db_user.responsible_id == 1
    assert db_session.query(User).count() == 2


def test_create_user_db_admin_ok(db_session: Session, user_create):
    user = User(
        email="TesT@email.COM",
        first_name="Name",
        last_name="Surnames",
        responsible_id=1,
        role="admin",
    )

    db_user = create_user_db(db_session, user)
    assert db_user.id
    assert db_user.role == "admin"
    assert db_session.query(User).count() == 2
