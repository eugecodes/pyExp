import logging
from typing import List

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class CustomValidationErrorSchema(BaseModel):
    code: str
    source: str = None
    field: str = None
    message: str = None


class CustomValidationErrorList(BaseModel):
    detail: List[CustomValidationErrorSchema]


RESPONSES = {
    422: {"model": CustomValidationErrorList, "description": "Validation Error"}
}

ERROR_MESSAGES_BY_TYPE = {
    "value_error.missing": ["FIELD_REQUIRED", "Field required"],
    "value_error.email": ["INVALID_EMAIL", "There is not a valid email"],
    "type_error.integer": ["INVALID_INTEGER", "There is not a valid integer"],
    "type_error.none.not_allowed": ["NULL_NOT_ALLOWED", "None is not an allowed value"],
    "value_error.number.not_ge": [
        "NEGATIVE_NUMBER",
        "ensure this value is greater than or equal to 0",
    ],
}

CUSTOM_ERRORS = {
    "login_error": {
        "code": "LOGIN_ERROR",
        "message": "There is an error with the login information",
        "source": None,
        "field": None,
    },
    "not_authenticated": {
        "code": "NOT_AUTHENTICATED",
        "message": "Not authenticated",
        "source": None,
        "field": None,
    },
    "invalid_credentials": {
        "code": "INVALID_CREDENTIALS",
        "message": "Invalid authentication credentials",
        "source": None,
        "field": None,
    },
    "timestamp_invalid": {
        "code": "INVALID_TIMESTAMP",
        "message": "The timestamp is not valid",
        "source": "query",
        "field": "query_param",
    },
    "expired_url": {
        "code": "EXPIRED_URL",
        "message": "The url has expired",
        "source": "query",
        "field": "query_param",
    },
    "user_not_exist": {
        "code": "NOT_EXIST",
        "message": "The user does not exist",
        "source": "path",
        "field": "path_param",
    },
    "invalid_token": {
        "code": "INVALID_TOKEN",
        "message": "The token used is not valid",
        "source": "query",
        "field": "query_param",
    },
    "invalid_url": {
        "code": "INVALID_URL",
        "message": "The url used is not valid",
        "source": "query",
        "field": "query_param",
    },
    "invalid_password": {
        "code": "INVALID_PASSWORD",
        "message": "The password does not meet the password policy requirements",
        "source": "body",
        "field": "password",
    },
    "email_already_exists": {
        "code": "EMAIL_ALREADY_EXISTS",
        "message": "User email already exists",
        "source": "body",
        "field": "email",
    },
    "incorrect_old_password": {
        "code": "INCORRECT_OLD_PASSWORD",
        "message": "The old password is incorrect",
        "source": "body",
        "field": "old_password",
    },
    "value_error.numeric_field_overflow": {
        "code": "NUMERIC_FIELD_OVERFLOW",
        "message": "Numeric field overflow",
        "source": None,
        "field": None,
    },
    "value_error.power_range.missing": {
        "code": "POWER_RANGE_MISSING",
        "message": "Max or min power missing",
        "source": "body",
        "field": None,
    },
    "value_error.power_range.invalid_range": {
        "code": "POWER_RANGE_INVALID_RANGE",
        "message": "min_power cannot be greater than max_power",
        "source": "body",
        "field": None,
    },
    "value_error.power_range.invalid": {
        "code": "POWER_RANGE_INVALID",
        "message": "invalid value for min_power or max_power",
        "source": "body",
        "field": None,
    },
    "value_error.power_range.invalid_rate_combination": {
        "code": "POWER_RANGE_INVALID_COMBINATION",
        "message": "invalid power_range for this price_type and energy_type combination",
        "source": "body",
        "field": None,
    },
    "value_error.energy_type.invalid": {
        "code": "ENERGY_TYPE_INVALID",
        "message": "Power range can only be defined for electricity type",
        "source": "body",
        "field": "energy_type",
    },
    "value_error.energy_type.invalid_price": {
        "code": "ENERGY_TYPE_INVALID_PRICE",
        "message": "invalid price value for this energy_type",
        "source": "body",
        "field": None,
    },
    "value_error.energy_type.invalid_consumption": {
        "code": "INVALID_ENERGY_TYPE",
        "message": "Invalid consumption range for this energy type",
        "source": "body",
        "field": "energy_type",
    },
    "value_error.energy_type.invalid_fixed_term_price": {
        "code": "ENERGY_TYPE_INVALID_FIXED_TERM_PRICE",
        "message": "Invalid fixed_term_price for this energy type",
        "source": "body",
        "field": "energy_type",
    },
    "value_error.energy_type.invalid_field": {
        "code": "ENERGY_TYPE_INVALID_FIELD",
        "message": "Invalid field for this energy type",
        "source": "body",
        "field": "energy_type",
    },
    "value_error.is_full_renewable.required": {
        "code": "IS_FULL_RENEWABLE_REQUIRED",
        "message": "Invalid is_full_renewable for this energy type",
        "source": "body",
        "field": "is_full_renewable",
    },
    "value_error.consumption_range.invalid_consumption_range": {
        "code": "INVALID_CONSUMPTION_RANGE",
        "message": "min_consumption cannot be greater than max_consumption",
        "source": "body",
        "field": None,
    },
    "rate_type_not_exist": {
        "code": "NOT_EXIST",
        "message": "Rate type does not exist",
        "source": None,
        "field": None,
    },
    "rate_not_exist": {
        "code": "NOT_EXIST",
        "message": "Rate does not exist",
        "source": None,
        "field": None,
    },
    "energy_cost_not_exist": {
        "code": "NOT_EXIST",
        "message": "Energy cost does not exist",
        "source": "path",
        "field": "path_param",
    },
    "other_cost_not_exist": {
        "code": "NOT_EXIST",
        "message": "Other cost does not exist",
        "source": "path",
        "field": "path_param",
    },
    "margin_not_exist": {
        "code": "NOT_EXIST",
        "message": "Margin does not exist",
        "source": "path",
        "field": "path_param",
    },
    "marketer_not_exist": {
        "code": "NOT_EXIST",
        "message": "Marketer does not exist",
        "source": "path",
        "field": "path_param",
    },
    "commission_not_exist": {
        "code": "NOT_EXIST",
        "message": "Commission does not exist",
        "source": "path",
        "field": "path_param",
    },
    "modify_energy_cost_not_allowed": {
        "code": "ENERGY_COST_MODIFICATION_NOT_ALLOWED",
        "message": "Modify energy cost without user is not allowed",
        "source": None,
        "field": None,
    },
    "value_error.already_exists": {
        "code": "RESOURCE_ALREADY_EXISTS",
        "message": "Another resource already exists with the same data",
        "source": "body",
        "field": None,
    },
    "value_error.type.invalid_rate_type_id": {
        "code": "TYPE_INVALID_RATE_TYPE_ID",
        "message": "Invalid rated_type for this type",
        "source": "body",
        "field": "type",
    },
    "value_error.consumption_range.missing": {
        "code": "CONSUMPTION_RANGE_MISSING",
        "message": "Consumption range missing",
        "source": "body",
        "field": None,
    },
    "value_error.type.invalid_consumption_range": {
        "code": "INVALID_CONSUMPTION_RANGE",
        "message": "Invalid consumption range for this type",
        "source": "body",
        "field": "type",
    },
    "value_error.rate_type.missing": {
        "code": "RATE_TYPE_ID_MISSING",
        "message": "rate_type_id missing",
        "source": "body",
        "field": "rate_type_id",
    },
    "value_error.rate_type.invalid": {
        "code": "RATE_TYPE_INVALID",
        "message": "rate_type must include the rate introduced",
        "source": "body",
        "field": "rate_type_id",
    },
    "value_error.type.already_exist_other_type": {
        "code": "OTHER_TYPE_EXISTS",
        "message": "Already exists other margin with different type",
        "source": "body",
        "field": "type",
    },
    "value_error.type.invalid": {
        "code": "RATE_TYPE_REQUIRED",
        "message": "Rate type required for this type",
        "source": "body",
        "field": "rate_type_id",
    },
    "value_error.consumption_range.overlap": {
        "code": "CONSUMPTION_RANGE_OVERLAP",
        "message": "Overlap in the consuption range with existing resource",
        "source": "body",
        "field": None,
    },
    "value_error.power_range.overlap": {
        "code": "POWER_RANGE_OVERLAP",
        "message": "Overlap in the power range with existing resource",
        "source": "body",
        "field": None,
    },
    "value_error.consumption_range.invalid": {
        "code": "CONSUPTION_RANGE_INVALID",
        "message": "min_consuption cannot be greater than max_consuption",
        "source": "body",
        "field": None,
    },
    "value_error.consumption_range.cannot_be_modified": {
        "code": "CONSUPTION_RANGE_INVALID",
        "message": "consumption range cannot be modified for this margin type",
        "source": "body",
        "field": None,
    },
    "value_error.margin_range.invalid": {
        "code": "MARGIN_RANGE_INVALID",
        "message": "min_margin cannot be greater than max_margin",
        "source": "body",
        "field": None,
    },
    "value_error.rate.existing_margin": {
        "code": "EXISTING_MARGIN",
        "message": "There is an existing margin for the rate selected",
        "source": "body",
        "field": "rate_id",
    },
    "value_error.rate.invalid": {
        "code": "INVALID_RATE",
        "message": "Invalid rate for this resource",
        "source": "body",
        "field": "rates",
    },
    "value_error.rate.invalid_energy_type": {
        "code": "INVALID_RATE_ENERGY_TYPE",
        "message": "Invalid energy_type for this resource",
        "source": "body",
        "field": "rates",
    },
    "value_error.rate.invalid_price_type": {
        "code": "INVALID_RATE_PRICE_TYPE",
        "message": "Invalid price_type_type for this commission",
        "source": "body",
        "field": "rates",
    },
    "value_error.rate.invalid_rate_type": {
        "code": "INVALID_RATE_RATE_TYPE",
        "message": "Invalid rate_type for the rate introduced",
        "source": "body",
        "field": "rates",
    },
    "value_error.power_1.missing": {
        "code": "POWER_1_MISSING",
        "message": "power_1 missing",
        "source": "body",
        "field": "power_1",
    },
    "value_error.power_2.missing": {
        "code": "POWER_2_MISSING",
        "message": "power_2 missing",
        "source": "body",
        "field": "power_2",
    },
    "value_error.current_rate_type_id.missing": {
        "code": "CURRENT_RATE_TYPE_ID_MISSING",
        "message": "current_rate_type_id missing",
        "source": "body",
        "field": "current_rate_type_id",
    },
    "saving_study_not_exist": {
        "code": "NOT_EXIST",
        "message": "Saving study does not exist",
        "source": None,
        "field": None,
    },
    "suggested_rate_not_exist": {
        "code": "NOT_EXIST",
        "message": "Suggested rate does not exist",
        "source": "body",
        "field": "suggested_rate_id",
    },
}


def request_validation_error_handler(exc: RequestValidationError) -> JSONResponse:
    error_response_content = {"detail": []}
    for error in exc.errors():
        try:
            code, message = ERROR_MESSAGES_BY_TYPE[error["type"]]
        except KeyError:
            logger.warning(
                f"Custom error message for type {error['type']} does not exist"
            )
            message = error["msg"]
            code = error["type"]
        error_response_content["detail"].append(
            {
                "source": error["loc"][0],
                "field": error["loc"][-1],
                "message": message,
                "code": code,
            }
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(error_response_content),
    )


def custom_exception(exc: StarletteHTTPException) -> JSONResponse:
    try:
        error_response = CustomValidationErrorSchema(**CUSTOM_ERRORS[exc.detail])
    except KeyError:
        error_response = CustomValidationErrorSchema(code=exc.detail)
    error_list = CustomValidationErrorList(detail=[error_response])
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(error_list),
        headers=exc.headers,
    )
