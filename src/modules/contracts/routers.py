from fastapi import APIRouter, Depends, status
from fastapi_filter import FilterDepends
from fastapi_pagination import Page, Params
from fastapi_pagination.bases import AbstractPage
from sqlalchemy.orm import Session
from starlette.responses import FileResponse

from src.infrastructure.sqlalchemy.database import get_db
from src.modules.contracts import schemas
from src.modules.users.models import User
from src.services.common import (
    generate_csv_file,
    get_current_user,
    paginate_queryset_with_n_to_many,
)
from src.services.contracts import (
    contract_create,
    contract_partial_update,
    contract_update,
    delete_contracts,
    get_contract,
    list_contract,
)
from src.services.exceptions import RESPONSES

router = APIRouter(prefix="/api/contracts", tags=["contracts"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.ContractCreateResponse,
    responses={**RESPONSES},
)
def contract_create_endpoint(
    contract_data: schemas.ContractCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> schemas.ContractCreateResponse:
    return contract_create(db, contract_data, current_user)


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=Page[schemas.ContractListResponse],
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def contract_list_endpoint(
    contract_filter: schemas.ContractFilter = FilterDepends(
        schemas.ContractFilter, use_cache=False
    ),
    params: Params = Depends(),
    db: Session = Depends(get_db),
) -> AbstractPage[schemas.ContractListResponse]:
    return paginate_queryset_with_n_to_many(list_contract(db, contract_filter), params)


@router.patch(
    "/{contract_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.ContractUpdateDetailResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def contract_update_partial_endpoint(
    contract_id: int,
    contract_data: schemas.ContractPartialUpdateRequest,
    db: Session = Depends(get_db),
) -> schemas.ContractUpdateDetailResponse:
    return contract_partial_update(db, contract_id, contract_data)


@router.get(
    "/{contract_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.ContractUpdateDetailResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def user_detail_endpoint(
    contract_id: int,
    db: Session = Depends(get_db),
) -> schemas.ContractUpdateDetailResponse:
    return get_contract(db, contract_id)


@router.put(
    "/{contract_id}",
    status_code=status.HTTP_200_OK,
    response_model=schemas.ContractUpdateDetailResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def contract_update_endpoint(
    contract_id: int,
    contract_data: schemas.ContractUpdateRequest,
    db: Session = Depends(get_db),
) -> schemas.ContractUpdateDetailResponse:
    return contract_update(db, contract_id, contract_data)


@router.post(
    "/delete",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def delete_contract_endpoint(
    contracts_data: schemas.ContractDeleteRequest,
    db: Session = Depends(get_db),
):
    delete_contracts(db, contracts_data)


@router.post(
    "/export/csv",
    status_code=status.HTTP_200_OK,
    response_class=FileResponse,
    dependencies=[Depends(get_current_user)],
    responses={**RESPONSES},
)
def contract_export_endpoint(
    contract_filter: schemas.ContractFilter = FilterDepends(
        schemas.ContractFilter, use_cache=False
    ),
    db: Session = Depends(get_db),
) -> FileResponse:
    return FileResponse(
        generate_csv_file(
            "contracts",
            schemas.contract_export_headers,
            list_contract(db, contract_filter).all(),
        )
    )
