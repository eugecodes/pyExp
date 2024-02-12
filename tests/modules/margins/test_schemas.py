import pytest
from fastapi import HTTPException

from src.modules.margins.schemas import MarginCreateRequest, validate_margin


def test_validate_margin_range_invalid_error():
    with pytest.raises(HTTPException) as exc:
        validate_margin("consume_range", {"min_margin": 71.17, "max_margin": 17.71})
    assert exc.value.detail == "value_error.margin_range.invalid"


def test_validate_margin_consume_range_ok():
    assert (
        validate_margin(
            "consume_range",
            {
                "min_consumption": 28.63,
                "max_consumption": 63.28,
                "min_margin": 17.71,
                "max_margin": 71.17,
            },
        )
        is None
    )


def test_validate_margin_consume_range_consumption_range_missing_error():
    with pytest.raises(HTTPException) as exc:
        validate_margin(
            "consume_range",
            {
                "min_consumption": 28.63,
                "min_margin": 17.71,
                "max_margin": 71.17,
            },
        )
    assert exc.value.detail == "value_error.consumption_range.missing"


def test_validate_margin_consume_range_consumption_range_invalid_error():
    with pytest.raises(HTTPException) as exc:
        validate_margin(
            "consume_range",
            {
                "min_consumption": 63.28,
                "max_consumption": 28.63,
                "min_margin": 17.71,
                "max_margin": 71.17,
            },
        )
    assert exc.value.detail == "value_error.consumption_range.invalid"


def test_validate_margin_rate_type_ok():
    assert (
        validate_margin(
            "rate_type",
            {
                "min_margin": 17.71,
                "max_margin": 71.17,
            },
        )
        is None
    )


class TestMarginCreateRequest:
    def test_validate_margin_ok(self):
        assert MarginCreateRequest.validate_margin(
            {
                "type": "consume_range",
                "min_consumption": 3.5,
                "max_consumption": 13.5,
                "min_margin": 17.3,
                "max_margin": 27.3,
            }
        )

    def test_validate_margin_rate_type_ok(self):
        assert MarginCreateRequest.validate_margin(
            {"type": "rate_type", "min_margin": 17.3, "max_margin": 27.3}
        )

    def test_validate_margin_rate_type_consumption_range_error(self):
        with pytest.raises(HTTPException) as exc:
            MarginCreateRequest.validate_margin(
                {
                    "type": "rate_type",
                    "min_consumption": 3.5,
                    "max_consumption": 13.5,
                    "min_margin": 17.3,
                    "max_margin": 27.3,
                }
            )
        assert exc.value.detail == "value_error.type.invalid_consumption_range"
