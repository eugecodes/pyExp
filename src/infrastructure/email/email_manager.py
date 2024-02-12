import asyncio
import logging

import sib_api_v3_sdk
from fastapi_mail import FastMail, MessageSchema, MessageType
from sib_api_v3_sdk.api import TransactionalEmailsApi
from sib_api_v3_sdk.rest import ApiException

from config.settings import settings
from src.infrastructure.email.email_config import EmailConfig, EmailMessageSchema

logger = logging.getLogger(__name__)

TEMPLATES = {
    settings.TEMPLATE_EMAIL_RESET_PASSWORD_ID: "email_verification.html",
    settings.TEMPLATE_EMAIL_PASSWORD_CHANGED_ID: "email_password_changed.html",
}


async def send_email_account_fastapi_mail(email_message: EmailMessageSchema):
    message = MessageSchema(
        subject=email_message.subject,
        recipients=email_message.recipients,
        template_body=email_message.parameters,
        subtype=MessageType.html,
    )
    fm = FastMail(EmailConfig.conf)
    await fm.send_message(message, template_name=TEMPLATES[email_message.template_id])


async def send_email_account_sendinblue(email_message: EmailMessageSchema):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = settings.SENDIN_BLUE_API_KEY
    sib_api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )
    recipients = [
        {"email": email_address} for email_address in email_message.recipients
    ]
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=recipients,
        template_id=email_message.template_id,
        params=email_message.parameters,
        headers={
            "charset": "iso-8859-1",
        },
    )

    try:
        sib_api_instance.send_transac_email(send_smtp_email)
    except ApiException as e:
        logger.error(
            "Exception when calling TransactionalEmailsApi->send_transac_email: %s\n"
            % e
        )


def get_sendinblue_api_instance() -> TransactionalEmailsApi:
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = settings.SENDIN_BLUE_API_KEY
    return sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )


def send_email(email_message: EmailMessageSchema):
    if settings.EMAIL_MODE == "SNMP":
        return asyncio.run(send_email_account_fastapi_mail(email_message))
    return asyncio.run(send_email_account_sendinblue(email_message))
