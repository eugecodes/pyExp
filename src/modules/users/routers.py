from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import FileResponse
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.database import get_db
from src.modules.users import schemas
from src.modules.users.models import User
from src.services.common import generate_csv_file, get_current_user
from src.services.exceptions import RESPONSES
from src.services.users import (
    change_password,
    delete_users,
    forgot_password,
    get_user,
    list_users,
    login_user,
    logout_user,
    reset_password,
    user_create,
    user_update,
)

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get(
    "",
    response_model=Page[schemas.UserListResponse],
    dependencies=[Depends(get_current_user)],
)
def user_list_endpoint(
    user_filter: schemas.UserFilter = FilterDepends(
        schemas.UserFilter, use_cache=False
    ),
    current_user: User = Depends(get_current_user),
    params: Params = Depends(),
    db: Session = Depends(get_db),
) -> AbstractPage[schemas.UserListResponse]:
    return paginate(list_users(db, user_filter, current_user), params)


@router.post(
    "/login", response_model=schemas.UserLoginResponse, responses={**RESPONSES}
)
def user_login_endpoint(
    login_data: schemas.UserLoginRequest, db: Session = Depends(get_db)
) -> schemas.UserLoginResponse:
    return login_user(db, login_data)


@router.post(
    "/forgot-password", status_code=status.HTTP_204_NO_CONTENT, responses={**RESPONSES}
)
def user_forgot_password_endpoint(
    background_tasks: BackgroundTasks,
    user_email: schemas.ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    background_tasks.add_task(forgot_password, db, user_email)


@router.post(
    "/reset-password", status_code=status.HTTP_204_NO_CONTENT, responses={**RESPONSES}
)
def user_reset_password_endpoint(
    reset_password_request: schemas.ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    reset_password(db, reset_password_request)


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=schemas.UserMeDetailResponse,
    responses={**RESPONSES},
)
def user_me_endpoint(
    current_user: User = Depends(get_current_user),
) -> schemas.UserMeDetailResponse:
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, responses={**RESPONSES})
def user_logout_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logout_user(db, current_user)


@router.post(
    "/change-password", status_code=status.HTTP_204_NO_CONTENT, responses={**RESPONSES}
)
def user_change_password_endpoint(
    change_password_request: schemas.ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    change_password(
        db,
        current_user,
        change_password_request.old_password,
        change_password_request.new_password,
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.UserCreateResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def user_create_endpoint(
    user_data: schemas.UserCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.UserCreateResponse:
    return user_create(db, user_data, current_user, background_tasks)


@router.put(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.UserUpdateResponse,
    responses={**RESPONSES},
)
def user_update_endpoint(
    user_id: int,
    user_data: schemas.UserUpdateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.UserUpdateResponse:
    return user_update(
        db,
        user_id,
        user_data,
        partial=False,
        background_tasks=background_tasks,
        current_user=current_user,
    )


@router.patch(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.UserUpdateResponse,
    responses={**RESPONSES},
)
def user_update_partial_endpoint(
    user_id: int,
    user_data: schemas.UserUpdatePartialRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.UserUpdateResponse:
    return user_update(
        db,
        user_id,
        user_data,
        partial=True,
        background_tasks=background_tasks,
        current_user=current_user,
    )


@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.UserMeDetailResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def user_detail_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
) -> schemas.UserMeDetailResponse:
    return get_user(db, user_id)


@router.post(
    "/delete",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def delete_users_endpoint(
    users_data: schemas.UserDeleteRequest,
    db: Session = Depends(get_db),
):
    delete_users(db, users_data)


@router.post(
    "/export/csv",
    status_code=status.HTTP_200_OK,
    response_class=FileResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def user_export_endpoint(
    user_filter: schemas.UserFilter = FilterDepends(
        schemas.UserFilter, use_cache=False
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    return FileResponse(
        generate_csv_file(
            "users",
            schemas.user_export_headers,
            list_users(db, user_filter, current_user).all(),
        )
    )
