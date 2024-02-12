import logging
import secrets
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse

from config.settings import settings
from src.modules.clients.routers import router as clients_router
from src.modules.commissions.routers import router as commissions_router
from src.modules.contacts.routers import router as contacts_router
from src.modules.contracts.routers import router as contracts_router
from src.modules.costs.routers import router as energy_costs_router
from src.modules.healthcheck.routers import router as healthcheck_router
from src.modules.margins.routers import router as margins_router
from src.modules.marketers.routers import router as marketers_router
from src.modules.rates.routers import router as rates_router
from src.modules.saving_studies.routers import router as saving_studies_router
from src.modules.supply_points.routers import router as supply_points_router
from src.modules.users.routers import router as users_router
from src.services.exceptions import custom_exception, request_validation_error_handler
from utils.middleware import add_middlewares

if settings.SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration

    sentry_logging = LoggingIntegration(
        level=settings.SENTRY_LOGGING_LEVEL,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR,  # Send errors as events
    )

    integrations = [
        sentry_logging,
        StarletteIntegration(),
        FastApiIntegration(),
    ]
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=integrations,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE,
        environment=settings.SENTRY_ENVIRONMENT,
        # https://docs.sentry.io/platforms/python/configuration/options/#send-default-pii
        send_default_pii=True,
    )

# config logs
# TODO: Improve log configuration
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(title="Test", docs_url=None, redoc_url=None, openapi_url=None)


# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


security = HTTPBasic()


def get_current_username(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    correct_username = secrets.compare_digest(
        credentials.username, settings.SWAGGER_USERNAME
    )
    correct_password = secrets.compare_digest(
        credentials.password, settings.SWAGGER_PASSWORD
    )
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="login_error",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username


@app.get("/api/openapi.json", include_in_schema=False)
async def openapi(username: str = Depends(get_current_username)) -> Dict[str, Any]:
    return get_openapi(title=app.title, version=app.version, routes=app.routes)


@app.get("/api/docs/", include_in_schema=False)
async def get_swagger_documentation(
    username: str = Depends(get_current_username),
) -> HTMLResponse:
    return get_swagger_ui_html(openapi_url="/api/openapi.json", title="API")


add_middlewares(app)

app.include_router(healthcheck_router)
app.include_router(users_router)
app.include_router(rates_router)
app.include_router(margins_router)
app.include_router(energy_costs_router)
app.include_router(marketers_router)
app.include_router(commissions_router)
app.include_router(saving_studies_router)
app.include_router(clients_router)
app.include_router(contacts_router)
app.include_router(supply_points_router)
app.include_router(contracts_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return request_validation_error_handler(exc)


@app.exception_handler(StarletteHTTPException)
async def custom_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    return custom_exception(exc)
