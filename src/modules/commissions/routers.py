from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.database import get_db
from src.modules.commissions import schemas
from src.services.commissions import (
    commission_create,
    commission_partial_update,
    commission_update,
    delete_commissions,
    get_commission,
    list_commissions,
)
from src.services.common import (
    generate_csv_file,
    get_current_user,
    paginate_queryset_with_n_to_many,
)
from src.services.exceptions import RESPONSES

router = APIRouter(prefix="/api/commissions", tags=["commissions"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.CommissionCreateResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def commission_create_endpoint(
    commission_data: schemas.CommissionCreateRequest,
    db: Session = Depends(get_db),
) -> schemas.CommissionCreateResponse:
    return commission_create(db, commission_data)


@router.put(
    "/{commission_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.CommissionUpdateDetailListResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def commission_update_endpoint(
    commission_id: int,
    commission_data: schemas.CommissionUpdateRequest,
    db: Session = Depends(get_db),
) -> schemas.CommissionUpdateDetailListResponse:
    return commission_update(
        db,
        commission_id,
        commission_data,
    )


@router.get(
    "/{commission_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.CommissionUpdateDetailListResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def commission_detail_endpoint(
    commission_id: int,
    db: Session = Depends(get_db),
) -> schemas.CommissionUpdateDetailListResponse:
    return get_commission(db, commission_id)


@router.patch(
    "/{commission_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.CommissionUpdateDetailListResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def commission_update_partial_endpoint(
    commission_id: int,
    commission_data: schemas.CommissionPartialUpdateRequest,
    db: Session = Depends(get_db),
) -> schemas.CommissionUpdateDetailListResponse:
    return commission_partial_update(
        db,
        commission_id,
        commission_data,
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=Page[schemas.CommissionUpdateDetailListResponse],
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def commission_list_endpoint(
    commission_filter: schemas.CommissionFilter = FilterDepends(
        schemas.CommissionFilter, use_cache=False
    ),
    params: Params = Depends(),
    db: Session = Depends(get_db),
) -> AbstractPage[schemas.CommissionUpdateDetailListResponse]:
    return paginate_queryset_with_n_to_many(
        list_commissions(db, commission_filter), params
    )


@router.post(
    "/delete",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def delete_commissions_endpoint(
    commissions_data: schemas.CommissionDeleteRequest,
    db: Session = Depends(get_db),
):
    delete_commissions(db, commissions_data)


@router.post(
    "/export/csv",
    status_code=status.HTTP_200_OK,
    response_class=FileResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def commission_export_endpoint(
    commission_filter: schemas.CommissionFilter = FilterDepends(
        schemas.CommissionFilter, use_cache=False
    ),
    db: Session = Depends(get_db),
) -> FileResponse:
    return FileResponse(
        generate_csv_file(
            "commissions",
            schemas.commission_export_headers,
            list_commissions(db, commission_filter).all(),
        )
    )
