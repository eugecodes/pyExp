import logging
from typing import List

from pydantic import BaseSettings


class TestBaseSettings(BaseSettings):
    DEBUG: bool = False
    PROJECT_NAME: str = "Test"
    SECRET_KEY: str
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:8000",
        "http://0.0.0.0:8000",
        "http://127.0.0.1:8000",
    ]
    # Database settings
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "Test"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "meloleo"
    # End database settings
    # Sentry settings
    SENTRY_DSN: str = None
    SENTRY_ENVIRONMENT: str = "production"
    SENTRY_TRACES_SAMPLE: float = 0.1
    SENTRY_LOGGING_LEVEL: int = logging.INFO
    # End sentry settings
    # Token settings
    TOKEN_EXPIRATION_TIME: int = 600
    # End token settings
    # Password reset settings
    RESET_PASSWORD_TOKEN_LIFETIME_SECONDS: int = 28800
    RESET_PASSWORD_URL: str = "http://localhost:5000/api/users/reset-password"
    RESET_PASS_PASSWORD_POLICY: str = "^(?=.{8,30}$)(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9]).*"
    # End password reset settings
    # Eail settings
    EMAIL_MODE: str
    SENDIN_BLUE_API_KEY: str
    # End email settings
    # language settings
    DEFAULT_LANGUAGE: str = "en"
    SUPPORTED_LANGUAGE: list = ["en", "es"]
    # logging
    LOG_LEVEL: str = "INFO"
    # Swagger basic auth
    SWAGGER_USERNAME: str = "user"
    SWAGGER_PASSWORD: str = "password"
    # End language settings

    # Email Template settings
    TEMPLATE_EMAIL_PASSWORD_CHANGED_ID = 3
    TEMPLATE_EMAIL_RESET_PASSWORD_ID = 2

    # SIPS
    SIPS_CONSUMER_KEY: str = ""
    SIPS_CONSUMER_SECRET: str = ""
