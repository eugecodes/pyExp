from sqlalchemy.orm import Session

from src.infrastructure.sqlalchemy.clients import (
    create_client_db,
    get_client_by,
    get_client_queryset,
)
from src.modules.clients.models import Client, InvoiceNotificationType
from src.modules.rates.models import ClientType
from src.modules.users.models import User


def test_create_client_db_ok(db_session: Session, user_create: User):
    create_client_db(
        db_session,
        Client(
            alias="Alias",
            user_id=user_create.id,
            client_type=ClientType.company,
            fiscal_name="Fiscal name",
            cif="123456789",
            invoice_notification_type=InvoiceNotificationType.email,
            invoice_email="test@test.com",
            bank_account_holder="Bank account holder",
            bank_account_number="Bank account number",
            fiscal_address="fiscal address",
            is_renewable=True,
        ),
    )
    assert db_session.query(Client).count() == 1


def test_get_client_queryset_ok(db_session: Session, client: Client):
    assert get_client_queryset(db_session).count() == 1


def test_get_client_queryset_with_join_list(db_session: Session, client: Client):
    result = get_client_queryset(db_session, [Client.user])
    assert result.count() == 1
    assert result.first().user.first_name == "John"


def test_get_client_by_one_field(client: Client, db_session: Session):
    client = get_client_by(db_session, Client.id == 1)
    assert client.id == 1


def test_get_client_by_multiple_fields(client: Client, db_session: Session):
    client = get_client_by(
        db_session,
        Client.id == 1,
        Client.fiscal_name == "Fiscal name",
    )
    assert client.id == 1
    assert client.fiscal_name == "Fiscal name"


def test_get_client_by_without_fields(client: Client, db_session: Session):
    client = get_client_by(db_session)
    assert client.id == 1
    assert client.fiscal_name == "Fiscal name"


def test_get_client_by_none(client: Client, db_session: Session):
    client = get_client_by(db_session, Client.id == 1234)
    assert client is None
