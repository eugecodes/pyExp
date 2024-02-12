import pytest
from fastapi import HTTPException

from src.modules.rates.schemas import RateTypeCreateRequest


class TestRateTypeCreateRequest:
    def test_validate_electricity_power_ok(self):
        assert RateTypeCreateRequest.validate_electricity_power(
            {
                "energy_type": "electricity",
                "max_power": 15.15,
                "min_power": 0.0,
            }
        )

    def test_validate_electricity_no_power_ok(self):
        assert RateTypeCreateRequest.validate_electricity_power(
            {
                "energy_type": "electricity",
            }
        )

    def test_validate_electricity_power_error_min_power(self):
        with pytest.raises(HTTPException) as exc:
            RateTypeCreateRequest.validate_electricity_power(
                {
                    "energy_type": "electricity",
                    "max_power": 15.15,
                }
            )
        assert exc.value.detail == "value_error.power_range.invalid"

    def test_validate_electricity_power_error_max_power(self):
        with pytest.raises(HTTPException) as exc:
            RateTypeCreateRequest.validate_electricity_power(
                {
                    "energy_type": "electricity",
                    "min_power": 15.15,
                }
            )
        assert exc.value.detail == "value_error.power_range.invalid"

    def test_validate_gas_power_ok(self):
        assert RateTypeCreateRequest.validate_electricity_power(
            {
                "energy_type": "gas",
            }
        )

    def test_validate_gas_power_error_min_power(self):
        with pytest.raises(HTTPException) as exc:
            RateTypeCreateRequest.validate_electricity_power(
                {"energy_type": "gas", "min_power": 0.0}
            )
        assert exc.value.detail == "value_error.energy_type.invalid"

    def test_validate_gas_power_error_max_power(self):
        with pytest.raises(HTTPException) as exc:
            RateTypeCreateRequest.validate_electricity_power(
                {"energy_type": "gas", "max_power": 10.0}
            )
        assert exc.value.detail == "value_error.energy_type.invalid"

    def test_validate_gas_power_error_both_power(self):
        with pytest.raises(HTTPException) as exc:
            RateTypeCreateRequest.validate_electricity_power(
                {
                    "energy_type": "gas",
                    "max_power": 10.0,
                    "min_power": 0.0,
                }
            )
        assert exc.value.detail == "value_error.energy_type.invalid"

    def test_validate_power_range_invalid(self):
        with pytest.raises(HTTPException) as exc:
            RateTypeCreateRequest.validate_electricity_power(
                {
                    "energy_type": "electricity",
                    "max_power": 5.5,
                    "min_power": 8.1,
                }
            )
        assert exc.value.detail == "value_error.power_range.invalid_range"
