from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.database import get_db
from src.modules.supply_points import schemas
from src.modules.users.models import User
from src.services.common import (
    generate_csv_file,
    get_current_user,
    paginate_queryset_with_n_to_many,
)
from src.services.exceptions import RESPONSES
from src.services.supply_points import (
    delete_supply_points,
    get_supply_point,
    list_supply_point,
    supply_point_create,
    supply_point_partial_update,
    supply_point_update,
)

router = APIRouter(prefix="/api/supply_points", tags=["supply_points"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.SupplyPointCreateResponse,
    responses={**RESPONSES},
)
def supply_point_create_endpoint(
    supply_point_data: schemas.SupplyPointCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.SupplyPointCreateResponse:
    return supply_point_create(db, supply_point_data, current_user)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=Page[schemas.SupplyPointListResponse],
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def supply_point_list_endpoint(
    supply_point_filter: schemas.SupplyPointFilter = FilterDepends(
        schemas.SupplyPointFilter, use_cache=False
    ),
    params: Params = Depends(),
    db: Session = Depends(get_db),
) -> AbstractPage[schemas.SupplyPointListResponse]:
    return paginate_queryset_with_n_to_many(
        list_supply_point(db, supply_point_filter), params
    )


@router.patch(
    "/{supply_point_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.SupplyPointUpdateDetailResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def supply_point_update_partial_endpoint(
    supply_point_id: int,
    supply_point_data: schemas.SupplyPointPartialUpdateRequest,
    db: Session = Depends(get_db),
) -> schemas.SupplyPointUpdateDetailResponse:
    return supply_point_partial_update(db, supply_point_id, supply_point_data)


@router.get(
    "/{supply_point_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.SupplyPointUpdateDetailResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def user_detail_endpoint(
    supply_point_id: int,
    db: Session = Depends(get_db),
) -> schemas.SupplyPointUpdateDetailResponse:
    return get_supply_point(db, supply_point_id)


@router.put(
    "/{supply_point_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.SupplyPointUpdateDetailResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def supply_point_update_endpoint(
    supply_point_id: int,
    supply_point_data: schemas.SupplyPointUpdateRequest,
    db: Session = Depends(get_db),
) -> schemas.SupplyPointUpdateDetailResponse:
    return supply_point_update(db, supply_point_id, supply_point_data)


@router.post(
    "/delete",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def delete_supply_point_endpoint(
    supply_points_data: schemas.SupplyPointDeleteRequest,
    db: Session = Depends(get_db),
):
    delete_supply_points(db, supply_points_data)


@router.post(
    "/export/csv",
    status_code=status.HTTP_200_OK,
    response_class=FileResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def supply_point_export_endpoint(
    supply_point_filter: schemas.SupplyPointFilter = FilterDepends(
        schemas.SupplyPointFilter, use_cache=False
    ),
    db: Session = Depends(get_db),
) -> FileResponse:
    return FileResponse(
        generate_csv_file(
            "supply_points",
            schemas.supply_point_export_headers,
            list_supply_point(db, supply_point_filter).all(),
        )
    )
