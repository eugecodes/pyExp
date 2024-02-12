import pytest
from fastapi_mail import FastMail
from pytest_mock import MockFixture
from sib_api_v3_sdk.api import TransactionalEmailsApi
from sib_api_v3_sdk.rest import ApiException

from config.settings import settings
from src.infrastructure.email.email_config import EmailMessageSchema
from src.infrastructure.email.email_manager import (
    get_sendinblue_api_instance,
    send_email,
    send_email_account_fastapi_mail,
    send_email_account_sendinblue,
)
from src.modules.users.models import User


@pytest.mark.asyncio
async def test_send_email_account_fastapi_mail_ok(fm: FastMail):
    email_message = EmailMessageSchema(
        subject="Test reset password",
        recipients=["test@user.com"],
        template_id=settings.TEMPLATE_EMAIL_RESET_PASSWORD_ID,
        parameters={"verification_url": "fake_verification_url"},
    )

    with fm.record_messages() as outbox:
        await send_email_account_fastapi_mail(email_message)
        assert len(outbox) == 1
        assert outbox[0]["from"] == "root@localhost.com <root@localhost.com>"
        assert outbox[0]["to"] == "test@user.com"
        assert outbox[0]["subject"] == "Test reset password"


@pytest.mark.asyncio
async def test_send_email_account_sendinblue_ok(
    mocker: MockFixture,
):
    mocked_1 = mocker.patch(
        "sib_api_v3_sdk.api.TransactionalEmailsApi.send_transac_email"
    )
    email_message = EmailMessageSchema(
        subject="Test reset password",
        recipients=["test@user.com"],
        template_id=settings.TEMPLATE_EMAIL_RESET_PASSWORD_ID,
        parameters={"verification_url": "fake_verification_url"},
    )
    await send_email_account_sendinblue(email_message)
    mocked_1.assert_called_once()


@pytest.mark.asyncio
async def test_send_email_account_sendinblue_api_exception(
    mocker: MockFixture,
):
    my_mock = mocker.patch("src.infrastructure.email.email_manager.logger.error")
    mocker.patch(
        "sib_api_v3_sdk.api.TransactionalEmailsApi.send_transac_email",
        side_effect=ApiException(reason=0, status="sendinblue api error"),
    )
    email_message = EmailMessageSchema(
        subject="Test reset password",
        recipients=["test@user.com"],
        template_id=settings.TEMPLATE_EMAIL_RESET_PASSWORD_ID,
        parameters={"verification_url": "fake_verification_url"},
    )

    await send_email_account_sendinblue(email_message)
    my_mock.assert_called_once_with(
        "Exception when calling TransactionalEmailsApi->send_transac_email: "
        "(sendinblue api error)\nReason: 0\n\n"
    )


def test_get_sendinblue_api_instance_ok():
    result = get_sendinblue_api_instance()
    assert isinstance(result, TransactionalEmailsApi)


def test_send_email_snmp_ok(user_create: User, mocker: MockFixture):
    my_mock = mocker.patch("asyncio.run")
    email_message = EmailMessageSchema(
        subject="Test password changed",
        recipients=[user_create.email],
        template_id=settings.TEMPLATE_EMAIL_PASSWORD_CHANGED_ID,
        parameters={
            "content_1": "Hi",
            "content_2": "John",
            "content_3": "Your password has been changed.",
            "content_4": "Thank you.",
            "content_5": "Regards.",
        },
    )

    send_email(email_message)

    my_mock.assert_called_once()


def test_send_email_api_ok(user_create: User, mocker: MockFixture):
    my_mock = mocker.patch("asyncio.run")
    settings.EMAIL_MODE = "EXTERNAL_API"
    email_message = EmailMessageSchema(
        subject="Test password changed",
        recipients=[user_create.email],
        template_id=settings.TEMPLATE_EMAIL_PASSWORD_CHANGED_ID,
        parameters={
            "content_1": "Hi",
            "content_2": "John",
            "content_3": "Your password has been changed.",
            "content_4": "Thank you.",
            "content_5": "Regards.",
        },
    )
    send_email(email_message)

    my_mock.assert_called_once()
