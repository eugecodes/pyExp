from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.database import get_db
from src.modules.rates import schemas
from src.modules.users.models import User
from src.services.common import generate_csv_file, get_current_user
from src.services.exceptions import RESPONSES
from src.services.rates import (
    delete_rate_types,
    delete_rates,
    get_rate,
    get_rate_type,
    get_rate_type_power_ranges,
    list_rate,
    list_rate_types,
    rate_create,
    rate_partial_update,
    rate_type_create,
    rate_type_partial_update,
    rate_update,
)

router = APIRouter(prefix="/api", tags=["rates"])


@router.post(
    "/rate-types",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.RateTypeInfo,
    responses={**RESPONSES},
)
def rate_type_create_endpoint(
    rate_type_data: schemas.RateTypeCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.RateTypeInfo:
    return rate_type_create(db, rate_type_data, current_user)


@router.get(
    "/rate-types",
    response_model=Page[schemas.RateTypeInfo],
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def rate_types_list_endpoint(
    rate_type_filter: schemas.RateTypeFilter = FilterDepends(
        schemas.RateTypeFilter, use_cache=False
    ),
    params: Params = Depends(),
    db: Session = Depends(get_db),
) -> AbstractPage[schemas.RateTypeInfo]:
    return paginate(list_rate_types(db, rate_type_filter), params)


@router.patch(
    "/rate-types/{rate_type_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.RateTypeInfo,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def rate_type_update_partial_endpoint(
    rate_type_id: int,
    rate_type_data: schemas.RateTypeUpdatePartialRequest,
    db: Session = Depends(get_db),
) -> schemas.RateTypeInfo:
    return rate_type_partial_update(
        db,
        rate_type_id,
        rate_type_data,
    )


@router.get(
    "/rate-types/power-ranges",
    status_code=status.HTTP_200_OK,
    response_model=schemas.RateTypePowerRangesResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def rate_type_min_max_endpoint(
    db: Session = Depends(get_db),
) -> schemas.RateTypePowerRangesResponse:
    return get_rate_type_power_ranges(db)


@router.get(
    "/rate-types/{rate_type_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.RateTypeInfo,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def rate_type_detail_endpoint(
    rate_type_id: int,
    db: Session = Depends(get_db),
) -> schemas.RateTypeInfo:
    return get_rate_type(db, rate_type_id)


@router.post(
    "/rate-types/delete",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def delete_rate_types_endpoint(
    rate_types_data: schemas.RateDeleteRequest,
    db: Session = Depends(get_db),
):
    delete_rate_types(db, rate_types_data)


@router.post(
    "/rate-types/export/csv",
    status_code=status.HTTP_200_OK,
    response_class=FileResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def rate_type_export_endpoint(
    rate_type_filter: schemas.RateTypeFilter = FilterDepends(
        schemas.RateTypeFilter, use_cache=False
    ),
    db: Session = Depends(get_db),
) -> FileResponse:
    return FileResponse(
        generate_csv_file(
            "rate_types",
            schemas.rate_type_export_headers,
            list_rate_types(db, rate_type_filter).all(),
        )
    )


@router.post(
    "/rates",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.RateCreateResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def rate_create_endpoint(
    rate_data: schemas.RateCreateRequest,
    db: Session = Depends(get_db),
) -> schemas.RateCreateResponse:
    return rate_create(db, rate_data)


@router.put(
    "/rates/{rate_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.RateUpdateDetailListResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def rate_update_endpoint(
    rate_id: int,
    rate_data: schemas.RateUpdateRequest,
    db: Session = Depends(get_db),
) -> schemas.RateUpdateDetailListResponse:
    return rate_update(
        db,
        rate_id,
        rate_data,
    )


@router.patch(
    "/rates/{rate_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.RateUpdateDetailListResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def rate_update_partial_endpoint(
    rate_id: int,
    rate_data: schemas.RatePartialUpdateRequest,
    db: Session = Depends(get_db),
) -> schemas.RateUpdateDetailListResponse:
    return rate_partial_update(
        db,
        rate_id,
        rate_data,
    )


@router.get(
    "/rates",
    response_model=Page[schemas.RateUpdateDetailListResponse],
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def rate_list_endpoint(
    rate_filter: schemas.RateFilter = FilterDepends(
        schemas.RateFilter, use_cache=False
    ),
    params: Params = Depends(),
    db: Session = Depends(get_db),
) -> AbstractPage[schemas.RateUpdateDetailListResponse]:
    return paginate(list_rate(db, rate_filter), params)


@router.get(
    "/rates/{rate_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.RateUpdateDetailListResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def rate_detail_endpoint(
    rate_id: int,
    db: Session = Depends(get_db),
) -> schemas.RateUpdateDetailListResponse:
    return get_rate(db, rate_id)


@router.post(
    "/rates/delete",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def delete_rates_endpoint(
    rates_data: schemas.RateDeleteRequest,
    db: Session = Depends(get_db),
):
    delete_rates(db, rates_data)


@router.post(
    "/rates/export/csv",
    status_code=status.HTTP_200_OK,
    response_class=FileResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def rate_export_endpoint(
    rate_filter: schemas.RateFilter = FilterDepends(
        schemas.RateFilter, use_cache=False
    ),
    db: Session = Depends(get_db),
) -> FileResponse:
    return FileResponse(
        generate_csv_file(
            "rates",
            schemas.rate_export_headers,
            list_rate(db, rate_filter).all(),
        )
    )
