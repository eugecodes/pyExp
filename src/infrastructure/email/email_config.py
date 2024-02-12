from typing import Dict, List

from fastapi_mail import ConnectionConfig
from pydantic import BaseModel

from config.settings import settings


class EmailConfig:
    conf = ConnectionConfig(
        MAIL_USERNAME=settings.EMAIL_CONFIG_USERNAME,
        MAIL_PASSWORD=settings.EMAIL_CONFIG_PASSWORD,
        MAIL_FROM=settings.EMAIL_CONFIG_FROM,
        MAIL_PORT=settings.EMAIL_CONFIG_PORT,
        MAIL_SERVER=settings.EMAIL_CONFIG_SERVER,
        MAIL_FROM_NAME=settings.EMAIL_CONFIG_FROM_NAME,
        MAIL_STARTTLS=settings.EMAIL_CONFIG_STARTTLS,
        MAIL_SSL_TLS=settings.EMAIL_CONFIG_SSL_TLS,
        USE_CREDENTIALS=settings.EMAIL_CONFIG_USE_CREDENTIALS,
        VALIDATE_CERTS=settings.EMAIL_CONFIG_VALIDATE_CERTS,
        TEMPLATE_FOLDER=settings.EMAIL_CONFIG_TEMPLATE_FOLDER,
        SUPPRESS_SEND=settings.EMAIL_CONFIG_SUPPRESS_SEND,
    )


class EmailMessageSchema(BaseModel):
    subject: str | None
    recipients: List[str] | None
    template_id: int | None
    parameters: Dict | None
