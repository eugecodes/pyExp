from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.database import get_db
from src.modules.margins import schemas
from src.services.common import generate_csv_file, get_current_user
from src.services.exceptions import RESPONSES
from src.services.margins import (
    delete_margins,
    get_margin,
    list_margins,
    margin_create,
    margin_partial_update,
    margin_update,
)

router = APIRouter(prefix="/api/marketer-margins", tags=["margins"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.MarginCreateUpdateResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def margin_create_endpoint(
    margin_data: schemas.MarginCreateRequest,
    db: Session = Depends(get_db),
) -> schemas.MarginCreateUpdateResponse:
    return margin_create(db, margin_data)


@router.put(
    "/{margin_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.MarginCreateUpdateResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def margin_update_endpoint(
    margin_id: int,
    margin_data: schemas.MarginUpdateRequest,
    db: Session = Depends(get_db),
) -> schemas.MarginCreateUpdateResponse:
    return margin_update(
        db,
        margin_id,
        margin_data,
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=Page[schemas.MarginListDetailPartialUpdateResponse],
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def margin_list_endpoint(
    margin_filter: schemas.MarginFilter = FilterDepends(
        schemas.MarginFilter, use_cache=False
    ),
    params: Params = Depends(),
    db: Session = Depends(get_db),
) -> AbstractPage[schemas.MarginListDetailPartialUpdateResponse]:
    return paginate(list_margins(db, margin_filter), params)


@router.get(
    "/{margin_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.MarginListDetailPartialUpdateResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def user_detail_endpoint(
    margin_id: int,
    db: Session = Depends(get_db),
) -> schemas.MarginListDetailPartialUpdateResponse:
    return get_margin(db, margin_id)


@router.patch(
    "/{margin_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.MarginListDetailPartialUpdateResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def margin_update_partial_endpoint(
    margin_id: int,
    margin_data: schemas.MarginPartialUpdateRequest,
    db: Session = Depends(get_db),
) -> schemas.MarginListDetailPartialUpdateResponse:
    return margin_partial_update(
        db,
        margin_id,
        margin_data,
    )


@router.post(
    "/delete",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def delete_margins_endpoint(
    margins_data: schemas.MarginDeleteRequest,
    db: Session = Depends(get_db),
):
    delete_margins(db, margins_data)


@router.post(
    "/export/csv",
    status_code=status.HTTP_200_OK,
    response_class=FileResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def margin_export_endpoint(
    margin_filter: schemas.MarginFilter = FilterDepends(
        schemas.MarginFilter, use_cache=False
    ),
    db: Session = Depends(get_db),
) -> FileResponse:
    return FileResponse(
        generate_csv_file(
            "margins",
            schemas.margin_export_headers,
            list_margins(db, margin_filter).all(),
        )
    )
