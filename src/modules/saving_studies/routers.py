from typing import List

from fastapi import APIRouter, Depends, status
from fastapi.responses import FileResponse
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.database import get_db
from src.modules.saving_studies import schemas
from src.modules.users.models import User
from src.services.common import generate_csv_file, get_current_user
from src.services.exceptions import RESPONSES
from src.services.studies import (
    delete_saving_study,
    duplicate_saving_study,
    finish_saving_study,
    generate_suggested_rates_for_study,
    get_saving_study,
    list_saving_studies,
    list_suggested_rates,
    saving_study_create,
    saving_study_update,
    suggested_rate_update,
)

router = APIRouter(prefix="/api", tags=["saving-studies"])


@router.post(
    "/studies",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.SavingStudyOutput,
    responses={**RESPONSES},
)
def saving_study_create_endpoint(
    saving_study_create_data: schemas.SavingStudyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.SavingStudyOutput:
    return saving_study_create(db, saving_study_create_data, current_user)


@router.get(
    "/studies",
    response_model=Page[schemas.SavingStudyOutput],
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def saving_studies_list_endpoint(
    saving_study_filter: schemas.SavingStudyFilter = FilterDepends(
        schemas.SavingStudyFilter, use_cache=False
    ),
    params: Params = Depends(),
    db: Session = Depends(get_db),
) -> AbstractPage[schemas.SavingStudyOutput]:
    return paginate(list_saving_studies(db, saving_study_filter), params)


@router.put(
    "/studies/{saving_study_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.SavingStudyOutput,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def saving_study_update_endpoint(
    saving_study_id: int,
    saving_study_data: schemas.SavingStudyRequest,
    db: Session = Depends(get_db),
) -> schemas.SavingStudyOutput:
    return saving_study_update(db, saving_study_id, saving_study_data)


@router.get(
    "/studies/{saving_study_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.SavingStudyOutput,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def saving_study_detail_endpoint(
    saving_study_id: int,
    db: Session = Depends(get_db),
) -> schemas.SavingStudyOutput:
    return get_saving_study(db, saving_study_id)


@router.post(
    "/studies/{saving_study_id}/generate-rates",
    status_code=status.HTTP_201_CREATED,
    response_model=List[schemas.SuggestedRateResponse],
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def generate_suggested_rates_list_endpoint(
    saving_study_id: int,
    db: Session = Depends(get_db),
) -> List[schemas.SuggestedRateResponse]:
    return generate_suggested_rates_for_study(db, saving_study_id)


@router.post(
    "/studies/{saving_study_id}/finish",
    status_code=status.HTTP_200_OK,
    response_model=schemas.SavingStudyFinishOutput,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def finish_saving_study_endpoint(
    saving_study_id: int,
    finish_study_request_data: schemas.SavingStudyFinishRequest,
    db: Session = Depends(get_db),
) -> schemas.SavingStudyFinishOutput:
    saving_study, suggested_rate = finish_saving_study(
        db, saving_study_id, finish_study_request_data.suggested_rate_id
    )

    return saving_study


@router.get(
    "/studies/{saving_study_id}/suggested-rates",
    response_model=Page[schemas.SuggestedRateResponse],
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def suggested_rates_list_endpoint(
    saving_study_id: int,
    suggested_rate_filter: schemas.SuggestedRateFilter = FilterDepends(
        schemas.SuggestedRateFilter, use_cache=False
    ),
    params: Params = Depends(),
    db: Session = Depends(get_db),
) -> AbstractPage[schemas.SuggestedRateResponse]:
    return paginate(
        list_suggested_rates(db, suggested_rate_filter, saving_study_id), params
    )


@router.put(
    "/studies/{saving_study_id}/suggested-rates/{suggested_rate_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.SuggestedRateResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def suggested_rate_update_endpoint(
    saving_study_id: int,
    suggested_rate_id: int,
    suggested_rate_data: schemas.SuggestedRateUpdate,
    db: Session = Depends(get_db),
) -> schemas.SuggestedRateResponse:
    return suggested_rate_update(
        db, saving_study_id, suggested_rate_id, suggested_rate_data
    )


@router.post(
    "/studies/delete",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def delete_saving_studies_endpoint(
    saving_studies_data: schemas.SavingStudyDeleteRequest,
    db: Session = Depends(get_db),
):
    delete_saving_study(db, saving_studies_data)


@router.post(
    "/studies/{saving_study_id}/duplicate",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.SavingStudyOutput,
    responses={**RESPONSES},
)
def duplicate_saving_study_endpoint(
    saving_study_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.SavingStudyOutput:
    saving_study = duplicate_saving_study(db, saving_study_id, current_user)

    return saving_study


@router.post(
    "/studies/export/csv",
    status_code=status.HTTP_200_OK,
    response_class=FileResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def saving_study_export_endpoint(
    saving_study_filter: schemas.SavingStudyFilter = FilterDepends(
        schemas.SavingStudyFilter, use_cache=False
    ),
    db: Session = Depends(get_db),
) -> FileResponse:
    return FileResponse(
        generate_csv_file(
            "saving_studies",
            schemas.saving_study_export_headers,
            list_saving_studies(db, saving_study_filter).all(),
        )
    )
