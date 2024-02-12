import datetime
import re
from typing import List
from urllib import parse

from fastapi import HTTPException, status
from passlib.handlers.argon2 import argon2
from passlib.hash import pbkdf2_sha256
from sqlalchemy import false, true
from sqlalchemy.orm import Session
from starlette.background import BackgroundTasks

from config.settings import settings
from src.infrastructure.email.email_config import EmailMessageSchema
from src.infrastructure.email.email_manager import send_email
from src.infrastructure.sqlalchemy.common import update_obj_db
from src.infrastructure.sqlalchemy.users import (
    create_user_db,
    delete_token,
    get_or_create_token,
    get_user_by,
    get_users_queryset,
)
from src.modules.users import schemas
from src.modules.users.models import Token, User
from src.modules.users.schemas import (
    ForgotPasswordRequest,
    UserCreateRequest,
    UserDeleteRequest,
    UserFilter,
    UserLoginRequest,
    UserUpdatePartialRequest,
    UserUpdateRequest,
)
from src.services.common import update_from_dict
from utils.i18n import trans as _


def generate_password_hash(password: str) -> str:
    return argon2.using(rounds=2, salt=bytes(settings.SECRET_KEY, "UTF-8")).hash(
        password
    )


def validate_password(password: str, hashed_password) -> bool:
    return argon2.verify(password, hashed_password)


def check_password_policy(password: str) -> bool:
    return re.fullmatch(settings.RESET_PASS_PASSWORD_POLICY, password)


def get_or_create_user_token(db: Session, user: User) -> Token:
    return get_or_create_token(db, user)


def login_user(db: Session, login_data: UserLoginRequest) -> Token:
    user = get_user_by(
        db,
        User.email == login_data.email,
        User.is_active == true(),
        User.is_deleted == false(),
    )
    if not user or not validate_password(login_data.password, user.hashed_password):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "login_error")
    token = get_or_create_user_token(db, user)
    return token


def logout_user(db: Session, user: User) -> None:
    delete_token(db, Token.user_id == user.id)


def forgot_password(db: Session, user_email: ForgotPasswordRequest):
    user = get_user_by(
        db,
        User.email == user_email.email,
        User.is_active == true(),
        User.is_deleted == false(),
    )

    if not user:
        return

    email_message = EmailMessageSchema(
        subject=_("Test reset password"),
        recipients=[user.email],
        parameters={
            "content_1": _("Hi"),
            "content_2": user.first_name,
            "content_3": _("You have requested a password change."),
            "content_4": _("to reset your password click on the following link:"),
            "content_5": _("Reset password"),
            "content_6": _("Thank you."),
            "content_7": _("Regards"),
        },
    )
    verification_account(user, email_message)


def verification_account(user: User, email_message: EmailMessageSchema):
    expiration_datetime = datetime.datetime.utcnow() + datetime.timedelta(
        seconds=settings.RESET_PASSWORD_TOKEN_LIFETIME_SECONDS
    )

    expiration_timestamp = datetime.datetime.timestamp(expiration_datetime)
    user_info = f"{user.id}{user.email}{expiration_timestamp}{settings.SECRET_KEY}"
    hash = pbkdf2_sha256.hash(user_info)
    encoded_token = parse.quote(hash.encode("utf-8"), safe="")

    email_message.parameters["verification_url"] = (
        f"{settings.RESET_PASSWORD_URL}"
        f"/{user.id}?token={encoded_token}&timestamp={expiration_timestamp}/"
    )
    email_message.template_id = settings.TEMPLATE_EMAIL_RESET_PASSWORD_ID
    send_email(email_message)


def reset_password(db: Session, reset_password_request: schemas.ResetPasswordRequest):
    hash_list = reset_password_request.hash.split("-")
    try:
        timestamp = float(hash_list[0])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="timestamp_invalid"
        )
    token = "-".join(hash_list[1:])
    if datetime.datetime.utcnow() > datetime.datetime.fromtimestamp(timestamp):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="expired_url"
        )
    user = get_user_by(
        db,
        User.id == reset_password_request.user_id,
        User.is_deleted == false(),
        User.is_active == true(),
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="user_not_exist"
        )

    user_info = f"{user.id}{user.email}{timestamp}{settings.SECRET_KEY}"

    try:
        hash_verified = pbkdf2_sha256.verify(user_info, token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="invalid_token",
        )
    if not hash_verified:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="invalid_url",
        )

    if not check_password_policy(reset_password_request.password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="invalid_password",
        )

    new_pass = generate_password_hash(reset_password_request.password)
    user.hashed_password = new_pass
    db.commit()


def user_create(
    db: Session,
    user_data: UserCreateRequest,
    creator_user: User,
    background_tasks: BackgroundTasks,
) -> User:
    user = get_user_by(db, User.email == user_data.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="email_already_exists",
        )
    created_user = create_user_db(
        db, User(**user_data.dict(), responsible_id=creator_user.id)
    )

    email_message = EmailMessageSchema(
        subject=_("Test account created"),
        recipients=[created_user.email],
        parameters={
            "content_1": _("Hi"),
            "content_2": created_user.first_name,
            "content_3": _("Welcome to Test."),
            "content_4": _(
                "To start click on the following link and create a new password"
            ),
            "content_5": _("Create password"),
            "content_6": _("Thank you."),
            "content_7": _("Regards"),
        },
    )
    background_tasks.add_task(verification_account, created_user, email_message)

    return created_user


def get_user(db: Session, user_id: int) -> User:
    user = get_user_by(db, User.id == user_id, User.is_deleted == false())

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user_not_exist"
        )

    return user


def send_password_changed_email(user: User, current_user_email: str):
    email_message = EmailMessageSchema(
        subject=_("Test password changed"),
        recipients=[user.email],
        template_id=settings.TEMPLATE_EMAIL_PASSWORD_CHANGED_ID,
        parameters={
            "content_1": _("Hi"),
            "content_2": user.first_name,
            "content_3": _("Your password has been changed."),
            "content_4": _("Thank you."),
            "content_5": _("Regards."),
        },
    )
    send_email(email_message)


def user_update(
    db: Session,
    user_id: int,
    user_data: UserUpdateRequest | UserUpdatePartialRequest,
    partial: bool,
    background_tasks: BackgroundTasks,
    current_user: User,
) -> User:
    has_password_changed_email = False
    user = get_user(db, user_id)

    if get_user_by(db, User.id != user_id, User.email == user_data.email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="email_already_exists",
        )

    user_data_request = user_data.dict(exclude_unset=partial)
    is_deleted = user_data_request.get("is_deleted")

    if is_deleted:
        original_email = user.email
        update_from_dict(user, user_data_request)
        user.email = f"{user.id}{user.email}"
        user.deleted_at = datetime.datetime.utcnow()
        user = update_obj_db(db, user)
        user.email = original_email
        return user

    password = user_data_request.pop("password", None)

    if password:
        if not check_password_policy(password):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="invalid_password",
            )
        hashed_password = generate_password_hash(password)
        if hashed_password != user.hashed_password:
            user_data_request["hashed_password"] = hashed_password
            has_password_changed_email = True

    update_from_dict(user, user_data_request)

    user = update_obj_db(db, user)
    if has_password_changed_email:
        background_tasks.add_task(send_password_changed_email, user, current_user.email)

    return user


def change_password(db: Session, user: User, old_password: str, new_password: str):
    if not user or not validate_password(old_password, user.hashed_password):
        raise HTTPException(status_code=422, detail="incorrect_old_password")
    if not check_password_policy(new_password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="invalid_password",
        )
    new_hashed_password = generate_password_hash(new_password)
    user.hashed_password = new_hashed_password
    db.commit()


def list_users(db: Session, users_filter: UserFilter, current_user: User) -> List[User]:
    return users_filter.sort(
        users_filter.filter(
            get_users_queryset(
                db,
                None,
                User.is_deleted == false(),
                User.id != current_user.id,
            )
        )
    )


def delete_users(db: Session, users_data: UserDeleteRequest):
    db.query(User).filter(User.id.in_(users_data.ids)).update({"is_deleted": True})
    db.commit()
