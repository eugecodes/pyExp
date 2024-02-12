from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.database import get_db
from src.modules.marketers import schemas
from src.modules.users.models import User
from src.services.common import (
    generate_csv_file,
    get_current_user,
    paginate_queryset_with_n_to_many,
)
from src.services.exceptions import RESPONSES
from src.services.marketers import (
    delete_marketers,
    get_marketer,
    list_marketer,
    marketer_create,
    marketer_partial_update,
    marketer_update,
)

router = APIRouter(prefix="/api/marketers", tags=["marketers"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.MarketerCreateResponse,
    responses={**RESPONSES},
)
def marketer_create_endpoint(
    marketer_data: schemas.MarketerCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.MarketerCreateResponse:
    return marketer_create(db, marketer_data, current_user)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=Page[schemas.MarketerListResponse],
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def marketer_list_endpoint(
    marketer_filter: schemas.MarketerFilter = FilterDepends(
        schemas.MarketerFilter, use_cache=False
    ),
    params: Params = Depends(),
    db: Session = Depends(get_db),
) -> AbstractPage[schemas.MarketerListResponse]:
    return paginate_queryset_with_n_to_many(list_marketer(db, marketer_filter), params)


@router.patch(
    "/{marketer_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.MarketerUpdateDetailResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def marketer_update_partial_endpoint(
    marketer_id: int,
    marketer_data: schemas.MarketerPartialUpdateRequest,
    db: Session = Depends(get_db),
) -> schemas.MarketerUpdateDetailResponse:
    return marketer_partial_update(
        db,
        marketer_id,
        marketer_data,
    )


@router.get(
    "/{marketer_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.MarketerUpdateDetailResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def user_detail_endpoint(
    marketer_id: int,
    db: Session = Depends(get_db),
) -> schemas.MarketerUpdateDetailResponse:
    return get_marketer(db, marketer_id)


@router.put(
    "/{marketer_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.MarketerUpdateDetailResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def marketer_update_endpoint(
    marketer_id: int,
    marketer_data: schemas.MarketerUpdateRequest,
    db: Session = Depends(get_db),
) -> schemas.MarketerUpdateDetailResponse:
    return marketer_update(
        db,
        marketer_id,
        marketer_data,
    )


@router.post(
    "/delete",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def deletemarketer_endpoint(
    marketers_data: schemas.MarketerDeleteRequest,
    db: Session = Depends(get_db),
):
    delete_marketers(db, marketers_data)


@router.post(
    "/export/csv",
    status_code=status.HTTP_200_OK,
    response_class=FileResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def marketer_export_endpoint(
    marketer_filter: schemas.MarketerFilter = FilterDepends(
        schemas.MarketerFilter, use_cache=False
    ),
    db: Session = Depends(get_db),
) -> FileResponse:
    return FileResponse(
        generate_csv_file(
            "marketers",
            schemas.marketer_export_headers,
            list_marketer(db, marketer_filter).all(),
        )
    )
