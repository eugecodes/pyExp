from datetime import datetime
from decimal import Decimal
from typing import List
from unittest.mock import patch

import pytest
from sqlalchemy import true
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from src.modules.rates.models import EnergyType, Rate, RateType
from src.modules.saving_studies.models import (
    ClientType,
    SavingStudy,
    SavingStudyStatusEnum,
    SuggestedRate,
)
from src.modules.users.models import Token


def test_saving_study_create_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    electricity_rate_type: RateType,
    db_session: Session,
):
    data = {
        "cups": "stringstringstringst",
        "energy_type": EnergyType.electricity,
        "is_existing_client": False,
        "is_from_sips": False,
        "is_compare_conditions": False,
        "current_rate_type_id": electricity_rate_type.id,
        "analyzed_days": 100,
        "energy_price_1": 100,
        "client_type": "particular",
        "client_name": "Client name",
        "client_nif": "12345678A",
    }
    response = test_client.post(
        "/api/studies",
        headers={"Authorization": f"token {token_create.token}"},
        json=data,
    )

    response_data = response.json()
    assert response.status_code == 201
    saving_study = db_session.query(SavingStudy).all()
    assert len(saving_study) == 1
    assert saving_study[0].is_deleted is False
    assert saving_study[0].id > 0

    assert response_data["id"] > 0
    assert response_data["create_at"] is not None
    assert response_data["status"] == SavingStudyStatusEnum.IN_PROGRESS
    assert response_data["cups"] == "stringstringstringst"
    assert response_data["is_existing_client"] is False
    assert response_data["is_from_sips"] is False
    assert response_data["is_compare_conditions"] is False
    assert response_data["power_1"] is None
    assert response_data["power_2"] is None
    assert response_data["power_3"] is None
    assert response_data["power_4"] is None
    assert response_data["power_5"] is None
    assert response_data["power_6"] is None
    assert response_data["power_price_1"] is None
    assert response_data["power_price_2"] is None
    assert response_data["power_price_3"] is None
    assert response_data["power_price_4"] is None
    assert response_data["power_price_5"] is None
    assert response_data["power_price_6"] is None
    assert response_data["energy_price_1"] == 100
    assert response_data["energy_price_2"] is None
    assert response_data["energy_price_3"] is None
    assert response_data["energy_price_4"] is None
    assert response_data["energy_price_5"] is None
    assert response_data["energy_price_6"] is None
    assert response_data["annual_consumption"] == Decimal("0")
    assert response_data["client_type"] == "particular"
    assert response_data["client_name"] == "Client name"
    assert response_data["client_nif"] == "12345678A"
    assert response_data["current_rate_type"]["id"] == 1
    assert response_data["current_rate_type"]["name"] == "Electricity rate type"
    assert response_data["current_rate_type"]["energy_type"] == EnergyType.electricity
    assert response_data["current_marketer"] is None
    assert response_data["fixed_price"] is None
    assert response_data["other_cost_kwh"] is None
    assert response_data["other_cost_percentage"] is None
    assert response_data["other_cost_eur_month"] is None
    assert response_data["selected_suggested_rate"] is None
    assert response_data["user_creator"]["id"] == 1
    assert response_data["user_creator"]["first_name"] == "John"
    assert response_data["user_creator"]["last_name"] == "Graham"


def test_saving_study_create_endpoint_just_mandatory_fields(
    test_client: TestClient,
    token_create: Token,
    electricity_rate_type: RateType,
    db_session: Session,
):
    data = {
        "cups": "stringstringstringst",
        "energy_type": EnergyType.electricity,
        "is_existing_client": False,
        "is_from_sips": False,
        "is_compare_conditions": False,
    }
    response = test_client.post(
        "/api/studies",
        headers={"Authorization": f"token {token_create.token}"},
        json=data,
    )

    assert response.status_code == 201
    saving_study = db_session.query(SavingStudy).all()
    assert len(saving_study) == 1
    assert saving_study[0].is_deleted is False


def test_saving_study_create_endpoint_ok_rate_type_id_null(
    test_client: TestClient,
    token_create: Token,
    electricity_rate_type: RateType,
    db_session: Session,
):
    data = {
        "cups": "stringstringstringst",
        "energy_type": EnergyType.electricity,
        "is_existing_client": False,
        "is_from_sips": False,
        "is_compare_conditions": False,
        "analyzed_days": 100,
        "energy_price_1": 100,
        "client_type": "particular",
    }
    response = test_client.post(
        "/api/studies",
        headers={"Authorization": f"token {token_create.token}"},
        json=data,
    )

    assert response.status_code == 201
    saving_study = db_session.query(SavingStudy).all()
    assert len(saving_study) == 1
    assert saving_study[0].is_deleted is False
    assert saving_study[0].id > 0
    assert saving_study[0].create_at is not None
    assert saving_study[0].status == SavingStudyStatusEnum.IN_PROGRESS


def test_saving_study_create_endpoint_validation_error(
    test_client: TestClient,
    token_create: Token,
    electricity_rate_type: RateType,
    db_session: Session,
):
    data = {
        "cups": "stringstringstringst",
        "current_rate_type_id": electricity_rate_type.id,
        "energy_type": EnergyType.electricity,
        "is_existing_client": False,
        "is_from_sips": False,
        "is_compare_conditions": False,
        "analyzed_days": 100,
        "energy_price_1": 100,
        "client_type": "this-gives-an-error",
    }
    response = test_client.post(
        "/api/studies",
        headers={"Authorization": f"token {token_create.token}"},
        json=data,
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["message"] == (
        "value is not a valid enumeration member; permitted: "
        "'company', 'self-employed', 'particular', 'community_owners'"
    )


def test_saving_study_create_endpoint_rate_type_not_found(
    test_client: TestClient,
    token_create: Token,
    electricity_rate_type: RateType,
    db_session: Session,
):
    data = {
        "cups": "stringstringstringst",
        "energy_type": EnergyType.electricity,
        "is_existing_client": False,
        "is_from_sips": False,
        "is_compare_conditions": False,
        "current_rate_type_id": 1000,
        "analyzed_days": 100,
        "energy_price_1": 100,
        "client_type": "particular",
    }
    response = test_client.post(
        "/api/studies",
        headers={"Authorization": f"token {token_create.token}"},
        json=data,
    )

    assert response.status_code == 404
    assert response.json()["detail"][0]["message"] == "Rate type does not exist"
    assert response.json()["detail"][0]["code"] == "NOT_EXIST"


def test_saving_study_create_endpoint_validation_error_negative_value(
    test_client: TestClient,
    token_create: Token,
    electricity_rate_type: RateType,
    db_session: Session,
):
    data = {
        "cups": "stringstringstringst",
        "energy_type": EnergyType.electricity,
        "is_existing_client": False,
        "is_from_sips": False,
        "is_compare_conditions": False,
        "current_rate_type_id": 1000,
        "analyzed_days": -100,
        "energy_price_1": 100,
        "client_type": "particular",
    }
    response = test_client.post(
        "/api/studies",
        headers={"Authorization": f"token {token_create.token}"},
        json=data,
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"][0]["message"] == "ensure this value is greater than 0"
    )


def test_saving_study_create_endpoint_validation_error_string_too_long(
    test_client: TestClient,
    token_create: Token,
    electricity_rate_type: RateType,
    db_session: Session,
):
    data = {
        "cups": "stringstringstringstringstringstring",
        "energy_type": EnergyType.electricity,
        "is_existing_client": False,
        "is_from_sips": False,
        "is_compare_conditions": False,
        "current_rate_type_id": 1000,
        "analyzed_days": 100,
        "energy_price_1": 100,
        "client_type": "particular",
    }
    response = test_client.post(
        "/api/studies",
        headers={"Authorization": f"token {token_create.token}"},
        json=data,
    )

    assert response.status_code == 422
    assert (
        response.json()["detail"][0]["message"]
        == "ensure this value has at most 22 characters"
    )


def test_saving_study_create_endpoint_auth_error(
    test_client: TestClient,
    token_create: Token,
    electricity_rate_type: RateType,
    db_session: Session,
):
    data = {
        "cups": "stringstringstringst",
        "current_rate_type_id": electricity_rate_type.id,
        "energy_type": EnergyType.electricity,
        "is_existing_client": False,
        "is_from_sips": False,
        "is_compare_conditions": False,
        "analyzed_days": 100,
        "energy_price_1": 100,
        "client_type": "particular",
    }
    response = test_client.post(
        "/api/studies",
        headers={"Authorization": "token ivalid-token"},
        json=data,
    )

    assert response.status_code == 401


def test_saving_studies_list_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    saving_study: SavingStudy,
    deleted_saving_study: SavingStudy,
):
    response = test_client.get(
        "/api/studies",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 1
    assert response_data["page"] == 1
    assert response_data["size"] == 50
    assert len(response_data["items"]) == 1


def test_saving_studies_list_endpoint_invalid_token(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    saving_study: SavingStudy,
):
    response = test_client.get(
        "/api/studies",
        headers={"Authorization": "token invalid-token"},
    )

    assert response.status_code == 401


def test_saving_study_update_endpoint_ok(
    test_client: TestClient,
    db_session: Session,
    saving_study: SavingStudy,
    electricity_rate_type: RateType,
    token_create: Token,
):
    response = test_client.put(
        "/api/studies/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "cups": "stringstringstringst",
            "current_rate_type_id": electricity_rate_type.id,
            "energy_type": EnergyType.electricity,
            "is_existing_client": False,
            "is_from_sips": False,
            "is_compare_conditions": True,
            "analyzed_days": 365,
            "energy_price_1": 100,
            "power_1": 22,
            "power_2": 23,
            "client_type": "particular",
        },
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] > 0
    assert response_data["create_at"] is not None
    assert response_data["status"] == SavingStudyStatusEnum.IN_PROGRESS
    assert response_data["cups"] == "stringstringstringst"
    assert response_data["is_existing_client"] is False
    assert response_data["is_from_sips"] is False
    assert response_data["is_compare_conditions"] is True
    assert response_data["analyzed_days"] == 365
    assert response_data["power_1"] == 22
    assert response_data["power_2"] == 23
    assert response_data["power_3"] is None
    assert response_data["power_4"] is None
    assert response_data["power_5"] is None
    assert response_data["power_6"] == 5.75
    assert response_data["power_price_1"] is None
    assert response_data["power_price_2"] is None
    assert response_data["power_price_3"] is None
    assert response_data["power_price_4"] is None
    assert response_data["power_price_5"] is None
    assert response_data["power_price_6"] is None
    assert response_data["energy_price_1"] == 100
    assert response_data["energy_price_2"] is None
    assert response_data["energy_price_3"] is None
    assert response_data["energy_price_4"] is None
    assert response_data["energy_price_5"] is None
    assert response_data["energy_price_6"] == 23.6
    assert response_data["client_type"] == "particular"
    assert response_data["client_name"] == "Client name"
    assert response_data["client_nif"] == "12345678A"
    assert response_data["current_rate_type"]["id"] == 1
    assert response_data["current_rate_type"]["name"] == "Electricity rate type"
    assert response_data["current_rate_type"]["energy_type"] == EnergyType.electricity
    assert response_data["current_marketer"] is None
    assert response_data["fixed_price"] is None
    assert response_data["other_cost_kwh"] is None
    assert response_data["other_cost_percentage"] is None
    assert response_data["other_cost_eur_month"] is None
    assert response_data["selected_suggested_rate"] is None
    assert response_data["user_creator"]["id"] == 1
    assert response_data["user_creator"]["first_name"] == "John"
    assert response_data["user_creator"]["last_name"] == "Graham"


def test_saving_study_update_endpoint_not_auth(
    test_client: TestClient,
    db_session: Session,
    saving_study: SavingStudy,
    electricity_rate_type: RateType,
    token_create: Token,
):
    response = test_client.put(
        "/api/studies/1",
        headers={"Authorization": "token invalid-token"},
        json={
            "cups": "stringstringstringst",
            "current_rate_type_id": electricity_rate_type.id,
            "energy_type": EnergyType.electricity,
            "is_existing_client": False,
            "is_from_sips": False,
            "is_compare_conditions": True,
            "analyzed_days": 365,
            "energy_price_1": 100,
            "power_1": 22,
            "power_2": 23,
            "client_type": "particular",
        },
    )

    assert response.status_code == 401


def test_saving_study_update_endpoint_not_exist(
    test_client: TestClient,
    db_session: Session,
    electricity_rate_type: RateType,
    token_create: Token,
):
    response = test_client.put(
        "/api/studies/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "cups": "stringstringstringst",
            "current_rate_type_id": electricity_rate_type.id,
            "energy_type": EnergyType.electricity,
            "is_existing_client": False,
            "is_from_sips": False,
            "is_compare_conditions": True,
            "analyzed_days": 365,
            "energy_price_1": 100,
            "power_1": 22,
            "power_2": 23,
            "client_type": "particular",
        },
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_EXIST"
    assert response_data["detail"][0]["message"] == "Saving study does not exist"


def test_saving_study_update_endpoint_rate_type_not_exist(
    test_client: TestClient,
    db_session: Session,
    saving_study: SavingStudy,
    electricity_rate_type: RateType,
    token_create: Token,
):
    response = test_client.put(
        "/api/studies/1",
        headers={"Authorization": f"token {token_create.token}"},
        json={
            "cups": "stringstringstringst",
            "current_rate_type_id": 1000,
            "energy_type": EnergyType.electricity,
            "is_existing_client": False,
            "is_from_sips": False,
            "is_compare_conditions": True,
            "analyzed_days": 365,
            "energy_price_1": 100,
            "power_1": 22,
            "power_2": 23,
            "client_type": "particular",
        },
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_EXIST"
    assert response_data["detail"][0]["message"] == "Rate type does not exist"


def test_saving_study_details_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    saving_study: SavingStudy,
    suggested_rate: SuggestedRate,
):
    suggested_rate.is_selected = True
    response = test_client.get(
        "/api/studies/1",
        headers={"Authorization": f"token {token_create.token}"},
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == 1
    assert response_data["energy_type"] == EnergyType.electricity
    assert response_data["is_existing_client"] is False
    assert response_data["is_from_sips"] is False
    assert response_data["is_compare_conditions"] is False
    assert response_data["cups"] == "ES0021000000000000AA"
    assert response_data["client_type"] == ClientType.particular
    assert response_data["client_name"] == "Client name"
    assert response_data["client_nif"] == "12345678A"
    assert response_data["current_rate_type"]["id"] == 1
    assert response_data["current_rate_type"]["name"] == "Electricity rate type"
    assert response_data["current_rate_type"]["id"] == 1
    assert response_data["analyzed_days"] == 365
    assert Decimal(str(response_data["energy_price_1"])) == Decimal("27.3")
    assert response_data["energy_price_2"] is None
    assert response_data["energy_price_3"] is None
    assert response_data["energy_price_4"] is None
    assert response_data["energy_price_5"] is None
    assert Decimal(str(response_data["energy_price_6"])) == Decimal("23.6")
    assert response_data["power_1"] is None
    assert response_data["power_2"] is None
    assert response_data["power_3"] is None
    assert response_data["power_4"] is None
    assert response_data["power_5"] is None
    assert Decimal(str(response_data["power_6"])) == Decimal("5.75")
    assert response_data["consumption_p1"] is None
    assert response_data["consumption_p2"] is None
    assert response_data["consumption_p3"] is None
    assert response_data["consumption_p4"] is None
    assert response_data["consumption_p5"] is None
    assert response_data["consumption_p6"] is None
    assert Decimal(str(response_data["annual_consumption"])) == Decimal("15.34")
    assert response_data["fixed_price"] is None

    assert response_data["selected_suggested_rate"]["id"] == 1
    assert response_data["selected_suggested_rate"]["is_selected"] is True
    assert Decimal(
        str(response_data["selected_suggested_rate"]["applied_profit_margin"])
    ) == Decimal("12.3")
    assert response_data["selected_suggested_rate"]["final_cost"] is None
    assert (
        response_data["selected_suggested_rate"]["has_contractual_commitment"] is True
    )
    assert response_data["selected_suggested_rate"]["is_full_renewable"] is True
    assert response_data["selected_suggested_rate"]["has_net_metering"] is True
    assert Decimal(
        str(response_data["selected_suggested_rate"]["net_metering_value"])
    ) == Decimal("12.3")

    assert response_data["selected_suggested_rate"]["total_commission"] is None
    assert response_data["selected_suggested_rate"]["other_costs_commission"] is None
    assert response_data["selected_suggested_rate"]["theoretical_commission"] is None

    assert response_data["selected_suggested_rate"]["saving_relative"] is None
    assert response_data["selected_suggested_rate"]["saving_absolute"] is None

    assert Decimal(
        str(response_data["selected_suggested_rate"]["energy_price_1"])
    ) == Decimal("112.3")
    assert response_data["selected_suggested_rate"]["energy_price_2"] is None
    assert response_data["selected_suggested_rate"]["energy_price_3"] is None
    assert response_data["selected_suggested_rate"]["energy_price_4"] is None
    assert response_data["selected_suggested_rate"]["energy_price_5"] is None
    assert response_data["selected_suggested_rate"]["energy_price_6"] is None

    assert Decimal(
        str(response_data["selected_suggested_rate"]["power_price_1"])
    ) == Decimal("23.4")
    assert response_data["selected_suggested_rate"]["power_price_2"] is None
    assert response_data["selected_suggested_rate"]["power_price_3"] is None
    assert response_data["selected_suggested_rate"]["power_price_4"] is None
    assert response_data["selected_suggested_rate"]["power_price_5"] is None
    assert response_data["selected_suggested_rate"]["power_price_6"] is None

    assert response_data["selected_suggested_rate"]["fixed_term_price"] is None
    assert response_data["selected_suggested_rate"]["price_type"] is None
    assert response_data["selected_suggested_rate"]["final_cost"] is None

    assert response_data["selected_suggested_rate"]["energy_cost"] is None
    assert response_data["selected_suggested_rate"]["power_cost"] is None
    assert response_data["selected_suggested_rate"]["fixed_cost"] is None
    assert response_data["selected_suggested_rate"]["other_costs"] is None
    assert response_data["selected_suggested_rate"]["ie_cost"] is None
    assert response_data["selected_suggested_rate"]["ih_cost"] is None
    assert response_data["selected_suggested_rate"]["iva_cost"] is None

    assert response_data["other_cost_kwh"] is None
    assert response_data["other_cost_percentage"] is None
    assert response_data["other_cost_eur_month"] is None
    assert response_data["user_creator"]["id"] == 1
    assert response_data["user_creator"]["first_name"] == "John"
    assert response_data["user_creator"]["last_name"] == "Graham"


def test_saving_study_details_endpoint_not_token(test_client: TestClient):
    response = test_client.get("/api/studies/1")
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_AUTHENTICATED"
    assert response_data["detail"][0]["message"] == "Not authenticated"


def test_saving_study_details_endpoint_wrong_token(
    test_client: TestClient, token_create: Token
):
    response = test_client.get(
        "/api/rates/1", headers={"Authorization": "token faketoken"}
    )
    assert response.status_code == 401
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "INVALID_CREDENTIALS"
    assert response_data["detail"][0]["message"] == "Invalid authentication credentials"


@patch("src.services.studies.validate_saving_study_before_generating_rates")
def test_saving_study_generate_suggested_rates(
    mock_validator,
    test_client: TestClient,
    token_create: Token,
    saving_study: SavingStudy,
    db_session: Session,
):
    mock_validator.return_value = None
    saving_study.annual_consumption = 15
    saving_study.power_6 = 10
    saving_study.power_2 = 10

    response = test_client.post(
        f"/api/studies/{saving_study.id}/generate-rates",
        headers={"Authorization": f"token {token_create.token}"},
    )
    response_json = response.json()
    assert response.status_code == 201
    assert len(response_json) == 1
    assert response_json[0]["id"] == 1
    assert response_json[0]["rate_name"] == "Electricity rate active marketer"


def test_finish_study_ok(
    test_client: TestClient,
    token_create: Token,
    saving_study: SavingStudy,
    suggested_rate: SuggestedRate,
    db_session: Session,
):
    suggested_rate.is_selected = False
    response = test_client.post(
        f"/api/studies/{saving_study.id}/finish",
        headers={"Authorization": f"token {token_create.token}"},
        json={"suggested_rate_id": suggested_rate.id},
    )
    response_json = response.json()
    assert response.status_code == 200
    assert response_json["id"] == 1
    assert response_json["status"] == SavingStudyStatusEnum.COMPLETED
    assert response_json["selected_suggested_rate"]["id"] == 1
    assert response_json["selected_suggested_rate"]["is_selected"] is True


def test_suggested_rates_list_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    saving_study: SavingStudy,
    suggested_rate: SuggestedRate,
):
    response = test_client.get(
        f"/api/studies/{saving_study.id}/suggested-rates",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 1
    assert response_data["page"] == 1
    assert response_data["size"] == 50
    assert len(response_data["items"]) == 1
    assert response_data["items"][0]["id"] == 1
    assert response_data["items"][0]["is_selected"] is False
    assert Decimal(str(response_data["items"][0]["applied_profit_margin"])) == Decimal(
        "12.3"
    )
    assert response_data["items"][0]["final_cost"] is None
    assert response_data["items"][0]["has_contractual_commitment"] is True
    assert response_data["items"][0]["is_full_renewable"] is True
    assert response_data["items"][0]["has_net_metering"] is True
    assert Decimal(str(response_data["items"][0]["net_metering_value"])) == Decimal(
        "12.3"
    )
    assert response_data["items"][0]["theoretical_commission"] is None
    assert response_data["items"][0]["saving_relative"] is None
    assert response_data["items"][0]["saving_absolute"] is None


@pytest.mark.parametrize(
    "query_params",
    [
        "marketer_name__unaccent=marketer name",
        "rate_name__unaccent=rate name",
        "has_contractual_commitment=true",
        "is_full_renewable=true",
        "has_net_metering=true",
    ],
)
def test_suggested_rates_list_endpoint_filters_ok(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    saving_study: SavingStudy,
    suggested_rate: SuggestedRate,
    query_params: str,
):
    response = test_client.get(
        f"/api/studies/{saving_study.id}/suggested-rates?{query_params}",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 1
    assert response_data["page"] == 1
    assert response_data["size"] == 50
    assert len(response_data["items"]) == 1
    assert response_data["items"][0]["id"] == 1


def test_suggested_rates_list_endpoint_saving_study_not_found(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
):
    response = test_client.get(
        "/api/studies/1000/suggested-rates",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_EXIST"
    assert response_data["detail"][0]["message"] == "Saving study does not exist"


def test_suggested_rates_list_endpoint_ok_suggested_rates_from_another_study(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    saving_study: SavingStudy,
    deleted_saving_study: SavingStudy,
    suggested_rates: List[SuggestedRate],
):
    """
    Tests that we only list the suggested rates related with 'saving_study'.
    So, we create 4 suggested rates, one of them assigned to the saving study with id=2,
    thus expecting that the saving study with id=1 has 3 suggested rates linked to it
    """
    suggested_rates[0].saving_study_id = 2
    response = test_client.get(
        f"/api/studies/{saving_study.id}/suggested-rates",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 3
    assert response_data["page"] == 1
    assert response_data["size"] == 50
    assert len(response_data["items"]) == 3


def test_update_suggested_rate_ok(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    saving_study: SavingStudy,
    suggested_rate: SuggestedRate,
    electricity_rate: Rate,
):
    electricity_rate.name = "Rate name"
    suggested_rate.other_costs_commission = Decimal("10.0")
    db_session.add(suggested_rate)
    db_session.commit()
    db_session.refresh(suggested_rate)

    response = test_client.put(
        f"/api/studies/{saving_study.id}/suggested-rates/{suggested_rate.id}",
        headers={"Authorization": f"token {token_create.token}"},
        json={"applied_profit_margin": 20.0},
    )

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == 1
    assert response_data["is_selected"] is False
    assert Decimal(str(response_data["applied_profit_margin"])) == Decimal("20.0")
    assert response_data["final_cost"] == 0
    assert response_data["has_contractual_commitment"] is True
    assert response_data["is_full_renewable"] is True
    assert response_data["has_net_metering"] is True
    assert Decimal(str(response_data["net_metering_value"])) == Decimal("12.3")

    assert response_data["saving_relative"] is None
    assert response_data["saving_absolute"] is None

    assert response_data["theoretical_commission"] == Decimal("0")
    assert response_data["total_commission"] == Decimal("10.0")
    assert response_data["other_costs_commission"] == Decimal("10.0")


def test_update_suggested_rate_saving_study_not_found(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    saving_study: SavingStudy,
    suggested_rate: SuggestedRate,
    electricity_rate: Rate,
):
    electricity_rate.name = "Rate name"
    response = test_client.put(
        f"/api/studies/1000/suggested-rates/{suggested_rate.id}",
        headers={"Authorization": f"token {token_create.token}"},
        json={"applied_profit_margin": 20.0},
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_EXIST"
    assert response_data["detail"][0]["message"] == "Saving study does not exist"


def test_update_suggested_rate_suggested_rate_not_found(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    saving_study: SavingStudy,
    suggested_rate: SuggestedRate,
    electricity_rate: Rate,
):
    electricity_rate.name = "Rate name"
    response = test_client.put(
        f"/api/studies/{saving_study.id}/suggested-rates/1000",
        headers={"Authorization": f"token {token_create.token}"},
        json={"applied_profit_margin": 20.0},
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_EXIST"
    assert response_data["detail"][0]["message"] == "Suggested rate does not exist"


def test_update_suggested_rate_rate_not_found(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    saving_study: SavingStudy,
    suggested_rate: SuggestedRate,
    electricity_rate: Rate,
):
    electricity_rate.name = "NOT FOUND"
    response = test_client.put(
        f"/api/studies/{saving_study.id}/suggested-rates/{suggested_rate.id}",
        headers={"Authorization": f"token {token_create.token}"},
        json={"applied_profit_margin": 20.0},
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_EXIST"
    assert response_data["detail"][0]["message"] == "Rate does not exist"


def test_delete_saving_study_ok(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    saving_study: SavingStudy,
):
    response = test_client.post(
        "/api/studies/delete",
        headers={"Authorization": f"token {token_create.token}"},
        json={"ids": [1]},
    )

    assert response.status_code == 200
    assert (
        db_session.query(SavingStudy).filter(SavingStudy.is_deleted == true()).count()
        == 1
    )


def test_delete_saving_study_ok_id_not_found(
    test_client: TestClient,
    token_create: Token,
    db_session: Session,
    saving_study: SavingStudy,
):
    response = test_client.post(
        "/api/studies/delete",
        headers={"Authorization": f"token {token_create.token}"},
        json={"ids": [1000, 2000, 3000]},
    )

    assert response.status_code == 200
    assert (
        db_session.query(SavingStudy).filter(SavingStudy.is_deleted == true()).count()
        == 0
    )


def test_saving_study_duplicate_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    saving_study: SavingStudy,
    electricity_rate_type: RateType,
    db_session: Session,
):
    response = test_client.post(
        f"/api/studies/{saving_study.id}/duplicate",
        headers={"Authorization": f"token {token_create.token}"},
    )

    response_data = response.json()
    assert response.status_code == 201
    saving_study = db_session.query(SavingStudy).all()
    assert len(saving_study) == 2
    assert saving_study[1].is_deleted is False
    assert saving_study[1].id > 0

    assert response_data["id"] > 0
    assert response_data["create_at"] is not None
    assert response_data["status"] == SavingStudyStatusEnum.IN_PROGRESS
    assert response_data["cups"] == "ES0021000000000000AA"
    assert response_data["is_existing_client"] is False
    assert response_data["is_from_sips"] is False
    assert response_data["is_compare_conditions"] is False
    assert Decimal(str(response_data["annual_consumption"])) == Decimal("15.34")
    assert response_data["power_1"] is None
    assert response_data["power_2"] is None
    assert response_data["power_3"] is None
    assert response_data["power_4"] is None
    assert response_data["power_5"] is None
    assert Decimal(str(response_data["power_6"])) == Decimal("5.75")
    assert response_data["power_price_1"] is None
    assert response_data["power_price_2"] is None
    assert response_data["power_price_3"] is None
    assert response_data["power_price_4"] is None
    assert response_data["power_price_5"] is None
    assert response_data["power_price_6"] is None
    assert Decimal(str(response_data["energy_price_1"])) == Decimal("27.3")
    assert response_data["energy_price_2"] is None
    assert response_data["energy_price_3"] is None
    assert response_data["energy_price_4"] is None
    assert response_data["energy_price_5"] is None
    assert Decimal(str(response_data["energy_price_6"])) == Decimal("23.6")
    assert response_data["client_type"] == "particular"
    assert response_data["client_name"] == "Client name"
    assert response_data["client_nif"] == "12345678A"
    assert response_data["current_rate_type"]["id"] == 1
    assert response_data["current_rate_type"]["name"] == "Electricity rate type"
    assert response_data["current_rate_type"]["energy_type"] == EnergyType.electricity
    assert response_data["current_marketer"] is None
    assert response_data["fixed_price"] is None
    assert response_data["other_cost_kwh"] is None
    assert response_data["other_cost_percentage"] is None
    assert response_data["other_cost_eur_month"] is None
    assert response_data["selected_suggested_rate"] is None
    assert response_data["user_creator"]["id"] == 1
    assert response_data["user_creator"]["first_name"] == "John"
    assert response_data["user_creator"]["last_name"] == "Graham"


def test_saving_study_duplicate_endpoint_not_found(
    test_client: TestClient,
    token_create: Token,
    saving_study: SavingStudy,
    electricity_rate_type: RateType,
    db_session: Session,
):
    response = test_client.post(
        "/api/studies/1000/duplicate",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"][0]["code"] == "NOT_EXIST"
    assert response_data["detail"][0]["message"] == "Saving study does not exist"


def test_saving_studies_export_endpoint_ok(
    test_client: TestClient,
    token_create: Token,
    saving_study: SavingStudy,
    saving_study_2: SavingStudy,
    deleted_saving_study: SavingStudy,
    suggested_rate: SuggestedRate,
):
    saving_study.create_at = datetime(
        2023, 5, 5, 0, 0, 0
    )  # Set the created time to a fixed date
    suggested_rate.is_selected = True
    response = test_client.post(
        "/api/studies/export/csv",
        headers={"Authorization": f"token {token_create.token}"},
    )

    assert response.status_code == 200
    lines = response.text.split("\r\n")
    assert len(lines) == 4
    assert len(lines[0].split(";")) == 20
    assert len(lines[1].split(";")) == 20
    assert len(lines[2].split(";")) == 20
    assert lines[3].split(";")[0] == ""

    assert response.text.startswith(
        "Id;Cups;Client type;Client name;Client NIF;Rate type ID;"
        "Rate type name;Energy type;Current marketer;Suggested rate ID;Suggested rate name;"
        "Suggested rate final cost;Suggested rate theoretical commission;"
        "Suggested rate saving relative;Suggested rate saving absolute;Date;"
        "User creator ID;User creator first name;User creator last name;Status\r\n"
        "3;ES0021000000000000AA;particular;Client name;12345678A;"
    )
