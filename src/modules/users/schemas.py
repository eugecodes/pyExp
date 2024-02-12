from datetime import datetime
from typing import List, Optional

from fastapi_filter import FilterDepends, with_prefix
from pydantic import BaseModel, constr, validator

from src.infrastructure.sqlalchemy.filters import Filter
from src.modules.users.models import User, UserRole
from utils.i18n import trans as _


class BaseUserResponsible(BaseModel):
    id: int
    first_name: constr(max_length=32)
    last_name: constr(max_length=64)

    class Config:
        orm_mode = True


class UserMeDetailResponse(BaseModel):
    id: int
    first_name: constr(max_length=32)
    last_name: constr(max_length=64)
    email: constr(
        strip_whitespace=True,
        to_lower=True,
        max_length=256,
        regex=(r"^(?:\w+[+\-\.])*\w+@(?:\w+[\-\.])*\w+\.\w+$"),  # noqa F722
    )
    create_at: Optional[datetime]
    is_active: bool
    is_deleted: bool
    is_superadmin: bool
    responsible: BaseUserResponsible | None
    role: UserRole | None

    class Config:
        orm_mode = True


class UserLoginRequest(BaseModel):
    email: constr(
        strip_whitespace=True,
        to_lower=True,
        max_length=256,
        regex=(r"^(?:\w+[+\-\.])*\w+@(?:\w+[\-\.])*\w+\.\w+$"),  # noqa F722
    )
    password: str


class UserLoginResponse(BaseModel):
    token: str
    user: UserMeDetailResponse

    class Config:
        orm_mode = True


class ForgotPasswordRequest(BaseModel):
    email: constr(
        strip_whitespace=True,
        to_lower=True,
        max_length=256,
        regex=(r"^(?:\w+[+\-\.])*\w+@(?:\w+[\-\.])*\w+\.\w+$"),  # noqa F722
    )


class ResetPasswordRequest(BaseModel):
    password: str
    user_id: int
    hash: str


class BaseUserCreateUpdate(BaseModel):
    first_name: constr(max_length=32)
    last_name: constr(max_length=64)
    role: UserRole | None


class UserCreateRequest(BaseUserCreateUpdate):
    email: constr(
        strip_whitespace=True,
        to_lower=True,
        max_length=256,
        regex=(r"^(?:\w+[+\-\.])*\w+@(?:\w+[\-\.])*\w+\.\w+$"),  # noqa F722
    )

    @validator("email")
    def validate_email(
        cls,
        email: str,
    ) -> str:
        email = email.lower()
        return email


class UserCreateResponse(BaseUserCreateUpdate):
    id: int
    email: constr(
        strip_whitespace=True,
        to_lower=True,
        regex=(r"^(?:\w+[+\-\.])*\w+@(?:\w+[\-\.])*\w+\.\w+$"),  # noqa F722
    )
    create_at: Optional[datetime]
    is_active: bool

    class Config:
        orm_mode = True


class UserUpdateRequest(UserCreateRequest):
    password: Optional[str]


class UserUpdatePartialRequest(UserUpdateRequest):
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[
        constr(
            strip_whitespace=True,
            to_lower=True,
            max_length=256,
            regex=(r"^(?:\w+[+\-\.])*\w+@(?:\w+[\-\.])*\w+\.\w+$"),  # noqa F722
        )
    ]
    role: UserRole | None
    password: Optional[str]
    is_active: Optional[bool]
    is_deleted: Optional[bool]


class UserUpdateResponse(UserCreateResponse):
    pass


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class UserListResponse(UserCreateResponse):
    responsible: Optional[BaseUserResponsible]

    class Config:
        orm_mode = True


class UserDeleteRequest(BaseModel):
    ids: list[int]


class RelatedUserFilter(Filter):
    first_name__unaccent: Optional[str]
    last_name__unaccent: Optional[str]

    order_by: List[str] = ["-id"]
    search: str | None

    class Constants(Filter.Constants):
        model = User
        search_model_fields = ["first_name", "last_name"]


class UserFilter(Filter):
    id: Optional[int]
    id__in: list[int] | None
    first_name__unaccent: Optional[str]
    last_name__unaccent: Optional[str]
    role__unaccent: constr(max_length=32) | None
    email__unaccent: Optional[str]
    is_active: Optional[bool]
    is_deleted: Optional[bool]
    create_at__gte: Optional[datetime]
    create_at__lt: Optional[datetime]
    responsible: Optional[RelatedUserFilter] = FilterDepends(
        with_prefix("responsible", RelatedUserFilter), use_cache=False
    )

    order_by: List[str] = ["-create_at"]

    class Constants(Filter.Constants):
        model = User


user_export_headers = {
    "id": _("Id"),
    "first_name": _("First name"),
    "last_name": _("last name"),
    "email": _("Email address"),
    "role": _("Role"),
    "is_active": _("Is active"),
    "responsible.first_name": _("Responsible first name"),
    "responsible.last_name": _("Responsible last name"),
    "create_at": _("Date"),
}
