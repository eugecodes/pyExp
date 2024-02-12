from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.common import update_obj_db
from src.infrastructure.sqlalchemy.contracts import (
    create_contract_db,
    get_contract_by,
    get_contract_queryset,
)
from src.modules.contracts.models import Contract
from src.modules.contracts.schemas import (
    ContractCreateRequest,
    ContractDeleteRequest,
    ContractFilter,
    ContractPartialUpdateRequest,
    ContractUpdateRequest,
)
from src.modules.users.models import User
from src.services.common import update_from_dict


def contract_create(
    db: Session, contract_data: ContractCreateRequest, current_user: User
) -> Contract:
    contract = Contract(**contract_data.dict())
    contract.user_id = current_user.id
    if contract.expected_end_date is None:
        contract.expected_end_date = contract.preferred_start_date + timedelta(days=365)
    try:
        contract = create_contract_db(db, contract)
        return contract
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="value_error.already_exists"
        )


#
def list_contract(db: Session, contract_filter: ContractFilter):
    return contract_filter.sort(
        contract_filter.filter(
            get_contract_queryset(
                db,
                None,
            ),
            model_class_without_alias=Contract,
        ),
        model_class_without_alias=Contract,
    )


def get_contract(db: Session, contract_id: int) -> Contract:
    contract = get_contract_by(db, Contract.id == contract_id)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="contract_not_exist"
        )

    return contract


def contract_partial_update(
    db: Session,
    contract_id: int,
    contract_data: ContractPartialUpdateRequest,
) -> Contract:
    contract = get_contract(db, contract_id)
    contract_data_request = contract_data.dict(exclude_unset=True)
    update_from_dict(contract, contract_data_request)
    contract = update_obj_db(db, contract)
    return contract


def contract_update(
    db: Session,
    contract_id: int,
    contract_data: ContractUpdateRequest,
) -> Contract:
    contract = get_contract(db, contract_id)
    contract_data_request = contract_data.dict()
    update_from_dict(contract, contract_data_request)
    try:
        contract = update_obj_db(db, contract)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="value_error.already_exists"
        )
    return contract


def delete_contracts(db: Session, contracts_data: ContractDeleteRequest):
    db.query(Contract).filter(Contract.id.in_(contracts_data.ids)).delete()
    db.commit()
