from fastapi import APIRouter

from src.modules.healthcheck import schemas
from src.services.exceptions import RESPONSES

router = APIRouter(prefix="/__status__", tags=["healthcheck"])


@router.get("/", response_model=schemas.HealthCheck, responses={**RESPONSES})
def api_status() -> schemas.HealthCheck:
    return schemas.HealthCheck()


@router.get("/sentry-debug")
def trigger_error():
    return 1 / 0
