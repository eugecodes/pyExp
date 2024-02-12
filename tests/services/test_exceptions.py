import json
from unittest.mock import patch

from fastapi import HTTPException, status
from fastapi.exceptions import RequestValidationError
from pydantic.error_wrappers import ErrorWrapper

from config.settings import settings
from src.services.exceptions import custom_exception, request_validation_error_handler


def test_custom_exception_key_error():
    exception = HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="not_existing_exception",
    )

    response = custom_exception(exception)

    json_response = json.loads(response.body)
    assert json_response["detail"][0]["code"] == "not_existing_exception"
    assert response.status_code == 422


@patch("src.services.exceptions.RequestValidationError.errors")
def test_request_validation_error_handler_not_existing_type(mock_errors):
    mock_errors.return_value = [
        {
            "loc": ("error",),
            "msg": "",
            "type": "value_error.httpexception",
            "ctx": {
                "status_code": 422,
                "detail": "Unprocessable Entity",
                "headers": None,
            },
        }
    ]
    validation_error = RequestValidationError(
        errors=[
            ErrorWrapper(
                exc=HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY),
                loc="error",
            )
        ]
    )
    settings.DEBUG = False

    response = request_validation_error_handler(validation_error)

    json_response = json.loads(response.body)
    assert json_response["detail"][0]["code"] == "value_error.httpexception"
    assert response.status_code == 422
