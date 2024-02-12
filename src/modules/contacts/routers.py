from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.database import get_db
from src.modules.contacts import schemas
from src.modules.users.models import User
from src.services.common import (
    generate_csv_file,
    get_current_user,
    paginate_queryset_with_n_to_many,
)
from src.services.contacts import (
    contact_create,
    contact_partial_update,
    contact_update,
    delete_contacts,
    get_contact,
    list_contact,
)
from src.services.exceptions import RESPONSES

router = APIRouter(prefix="/api/contacts", tags=["contacts"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.ContactCreateResponse,
    responses={**RESPONSES},
)
def contact_create_endpoint(
    contact_data: schemas.ContactCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.ContactCreateResponse:
    return contact_create(db, contact_data, current_user)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=Page[schemas.ContactListResponse],
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def contact_list_endpoint(
    contact_filter: schemas.ContactFilter = FilterDepends(
        schemas.ContactFilter, use_cache=False
    ),
    params: Params = Depends(),
    db: Session = Depends(get_db),
) -> AbstractPage[schemas.ContactListResponse]:
    return paginate_queryset_with_n_to_many(list_contact(db, contact_filter), params)


@router.patch(
    "/{contact_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.ContactUpdateDetailResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def contact_update_partial_endpoint(
    contact_id: int,
    contact_data: schemas.ContactPartialUpdateRequest,
    db: Session = Depends(get_db),
) -> schemas.ContactUpdateDetailResponse:
    return contact_partial_update(db, contact_id, contact_data)


@router.get(
    "/{contact_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.ContactUpdateDetailResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def user_detail_endpoint(
    contact_id: int,
    db: Session = Depends(get_db),
) -> schemas.ContactUpdateDetailResponse:
    return get_contact(db, contact_id)


@router.put(
    "/{contact_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.ContactUpdateDetailResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def contact_update_endpoint(
    contact_id: int,
    contact_data: schemas.ContactUpdateRequest,
    db: Session = Depends(get_db),
) -> schemas.ContactUpdateDetailResponse:
    return contact_update(db, contact_id, contact_data)


@router.post(
    "/delete",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def deletecontact_endpoint(
    contacts_data: schemas.ContactDeleteRequest,
    db: Session = Depends(get_db),
):
    delete_contacts(db, contacts_data)


@router.post(
    "/export/csv",
    status_code=status.HTTP_200_OK,
    response_class=FileResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def contact_export_endpoint(
    contact_filter: schemas.ContactFilter = FilterDepends(
        schemas.ContactFilter, use_cache=False
    ),
    db: Session = Depends(get_db),
) -> FileResponse:
    return FileResponse(
        generate_csv_file(
            "contacts",
            schemas.contact_export_headers,
            list_contact(db, contact_filter).all(),
        )
    )
