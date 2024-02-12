from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.database import get_db
from src.modules.costs import schemas
from src.modules.users.models import User
from src.services.common import (
    generate_csv_file,
    get_current_user,
    paginate_queryset_with_n_to_many,
)
from src.services.costs import (
    delete_energy_costs,
    delete_other_costs,
    energy_cost_create,
    energy_cost_partial_update,
    get_energy_cost,
    get_energy_cost_amount_range,
    get_other_cost,
    list_energy_costs,
    list_other_costs,
    other_cost_create,
    other_cost_partial_update,
    other_cost_update,
)
from src.services.exceptions import RESPONSES

router = APIRouter(prefix="/api", tags=["costs"])


@router.post(
    "/energy-costs",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.CostInfo,
    responses={**RESPONSES},
)
def energy_cost_create_endpoint(
    energy_cost_data: schemas.EnergyCostCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.CostInfo:
    return energy_cost_create(db, energy_cost_data, current_user)


@router.get(
    "/energy-costs",
    response_model=Page[schemas.CostInfo],
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def energy_costs_list_endpoint(
    energy_cost_filter: schemas.EnergyCostFilter = FilterDepends(
        schemas.EnergyCostFilter, use_cache=False
    ),
    params: Params = Depends(),
    db: Session = Depends(get_db),
) -> AbstractPage[schemas.CostInfo]:
    return paginate(list_energy_costs(db, energy_cost_filter), params)


@router.patch(
    "/energy-costs/{energy_cost_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.CostInfo,
    responses={**RESPONSES},
)
def energy_cost_update_partial_endpoint(
    energy_cost_id: int,
    energy_cost_data: schemas.EnergyCostUpdatePartialRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.CostInfo:
    return energy_cost_partial_update(
        db,
        energy_cost_id,
        energy_cost_data,
        current_user=current_user,
    )


@router.get(
    "/energy-costs/amount-range",
    status_code=status.HTTP_200_OK,
    response_model=schemas.EnergyCostAmountRangeResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def energy_cost_min_max_endpoint(
    db: Session = Depends(get_db),
) -> schemas.EnergyCostAmountRangeResponse:
    return get_energy_cost_amount_range(db)


@router.get(
    "/energy-costs/{energy_cost_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.CostInfo,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def energy_cost_detail_endpoint(
    energy_cost_id: int,
    db: Session = Depends(get_db),
) -> schemas.CostInfo:
    return get_energy_cost(db, energy_cost_id)


@router.post(
    "/energy-costs/delete",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def delete_energy_costs_endpoint(
    energy_costs_data: schemas.CostDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_energy_costs(db, energy_costs_data, current_user)


@router.post(
    "/energy-costs/export/csv",
    status_code=status.HTTP_200_OK,
    response_class=FileResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def energy_costs_export_endpoint(
    energy_cost_filter: schemas.EnergyCostFilter = FilterDepends(
        schemas.EnergyCostFilter, use_cache=False
    ),
    db: Session = Depends(get_db),
) -> FileResponse:
    return FileResponse(
        generate_csv_file(
            "energy_costs",
            schemas.energy_cost_export_headers,
            list_energy_costs(db, energy_cost_filter).all(),
        )
    )


@router.post(
    "/costs",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.OtherCostCreateResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def other_cost_create_endpoint(
    other_cost_data: schemas.OtherCostCreateUpdateRequest,
    db: Session = Depends(get_db),
) -> schemas.OtherCostCreateResponse:
    return other_cost_create(db, other_cost_data)


@router.put(
    "/costs/{other_cost_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.OtherCostUpdateListDetailResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def other_cost_update_endpoint(
    other_cost_id: int,
    other_cost_data: schemas.OtherCostCreateUpdateRequest,
    db: Session = Depends(get_db),
) -> schemas.OtherCostUpdateListDetailResponse:
    return other_cost_update(
        db,
        other_cost_id,
        other_cost_data,
    )


@router.get(
    "/costs",
    status_code=status.HTTP_200_OK,
    response_model=Page[schemas.OtherCostUpdateListDetailResponse],
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def other_cost_list_endpoint(
    other_cost_filter: schemas.OtherCostFilter = FilterDepends(
        schemas.OtherCostFilter, use_cache=False
    ),
    params: Params = Depends(),
    db: Session = Depends(get_db),
) -> AbstractPage[schemas.OtherCostUpdateListDetailResponse]:
    return paginate_queryset_with_n_to_many(
        list_other_costs(db, other_cost_filter), params
    )


@router.get(
    "/costs/{other_cost_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.OtherCostUpdateListDetailResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def user_detail_endpoint(
    other_cost_id: int,
    db: Session = Depends(get_db),
) -> schemas.OtherCostUpdateListDetailResponse:
    return get_other_cost(db, other_cost_id)


@router.patch(
    "/costs/{other_cost_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.OtherCostUpdateListDetailResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def other_cost_update_partial_endpoint(
    other_cost_id: int,
    other_cost_data: schemas.OtherCostPartialUpdateRequest,
    db: Session = Depends(get_db),
) -> schemas.OtherCostUpdateListDetailResponse:
    return other_cost_partial_update(
        db,
        other_cost_id,
        other_cost_data,
    )


@router.post(
    "/costs/delete",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def delete_other_costs_endpoint(
    other_costs_data: schemas.CostDeleteRequest,
    db: Session = Depends(get_db),
):
    delete_other_costs(db, other_costs_data)


@router.post(
    "/costs/export/csv",
    status_code=status.HTTP_200_OK,
    response_class=FileResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def other_cost_export_endpoint(
    other_cost_filter: schemas.OtherCostFilter = FilterDepends(
        schemas.OtherCostFilter, use_cache=False
    ),
    db: Session = Depends(get_db),
) -> FileResponse:
    return FileResponse(
        generate_csv_file(
            "other_costs",
            schemas.other_cost_export_headers,
            list_other_costs(db, other_cost_filter).all(),
        )
    )
