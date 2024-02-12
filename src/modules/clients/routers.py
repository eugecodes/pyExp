from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.database import get_db
from src.modules.clients import schemas
from src.modules.users.models import User
from src.services.clients import (
    client_create,
    client_partial_update,
    client_update,
    delete_clients,
    get_client,
    list_client,
)
from src.services.common import (
    generate_csv_file,
    get_current_user,
    paginate_queryset_with_n_to_many,
)
from src.services.exceptions import RESPONSES

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.ClientCreateResponse,
    responses={**RESPONSES},
)
def client_create_endpoint(
    client_data: schemas.ClientCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.ClientCreateResponse:
    return client_create(db, client_data, current_user)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=Page[schemas.ClientListResponse],
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def client_list_endpoint(
    client_filter: schemas.ClientFilter = FilterDepends(
        schemas.ClientFilter, use_cache=False
    ),
    params: Params = Depends(),
    db: Session = Depends(get_db),
) -> AbstractPage[schemas.ClientListResponse]:
    return paginate_queryset_with_n_to_many(list_client(db, client_filter), params)


@router.patch(
    "/{client_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.ClientUpdateDetailResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def client_update_partial_endpoint(
    client_id: int,
    client_data: schemas.ClientPartialUpdateRequest,
    db: Session = Depends(get_db),
) -> schemas.ClientUpdateDetailResponse:
    return client_partial_update(db, client_id, client_data)


@router.get(
    "/{client_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.ClientUpdateDetailResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def user_detail_endpoint(
    client_id: int,
    db: Session = Depends(get_db),
) -> schemas.ClientUpdateDetailResponse:
    return get_client(db, client_id)


@router.put(
    "/{client_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.ClientUpdateDetailResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def client_update_endpoint(
    client_id: int,
    client_data: schemas.ClientUpdateRequest,
    db: Session = Depends(get_db),
) -> schemas.ClientUpdateDetailResponse:
    return client_update(db, client_id, client_data)


@router.post(
    "/delete",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def delete_client_endpoint(
    clients_data: schemas.ClientDeleteRequest,
    db: Session = Depends(get_db),
):
    delete_clients(db, clients_data)


@router.post(
    "/export/csv",
    status_code=status.HTTP_200_OK,
    response_class=FileResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def client_export_endpoint(
    client_filter: schemas.ClientFilter = FilterDepends(
        schemas.ClientFilter, use_cache=False
    ),
    db: Session = Depends(get_db),
) -> FileResponse:
    return FileResponse(
        generate_csv_file(
            "clients",
            schemas.client_export_headers,
            list_client(db, client_filter).all(),
        )
    )
