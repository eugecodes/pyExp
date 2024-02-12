import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.modules.clients.models import Client, InvoiceNotificationType
from src.modules.clients.schemas import ClientCreateRequest
from src.modules.contacts.schemas import ContactInlineCreateRequest
from src.modules.rates.models import ClientType
from src.modules.users.models import User
from src.services.clients import (  # create_update_client_address,
    client_create,
    get_client,
)


def test_client_create_ok(db_session: Session, user_create: User):
    client = client_create(
        db_session,
        ClientCreateRequest(
            alias="Alias",
            client_type=ClientType.company,
            fiscal_name="Fiscal name",
            cif="123456789",
            main_contact=ContactInlineCreateRequest(
                name="contact name", email="contasct@email.com", phone="666666666"
            ),
            invoice_notification_type=InvoiceNotificationType.email,
            invoice_email="test@test.com",
            bank_account_holder="Bank account holder",
            bank_account_number="Bank account number",
            fiscal_address="fiscal address",
            is_renewable=True,
        ),
        user_create,
    )

    assert db_session.query(Client).count() == 1
    assert client.alias == "Alias"
    assert client.client_type == ClientType.company
    assert client.fiscal_name == "Fiscal name"
    assert client.cif == "123456789"
    assert client.invoice_notification_type == InvoiceNotificationType.email
    assert client.invoice_email == "test@test.com"
    assert client.bank_account_holder == "Bank account holder"
    assert client.bank_account_number == "Bank account number"
    assert client.fiscal_address == "fiscal address"
    assert client.is_renewable is True
    assert client.contacts[0].name == "contact name"


def test_client_create_already_exists_error(
    db_session: Session, user_create: User, client: Client
):
    with pytest.raises(HTTPException) as exc:
        client_create(
            db_session,
            ClientCreateRequest(
                alias=client.alias,
                client_type=ClientType.company,
                fiscal_name=client.fiscal_name,
                cif=client.cif,
                main_contact=ContactInlineCreateRequest(
                    name="contact name", email="contasct@email.com", phone="666666666"
                ),
                invoice_notification_type=InvoiceNotificationType.email,
                invoice_email=client.invoice_email,
                bank_account_holder=client.bank_account_holder,
                bank_account_number=client.bank_account_number,
                fiscal_address=client.fiscal_address,
                is_renewable=True,
            ),
            user_create,
        )

    assert exc.value.detail == "value_error.already_exists"
    assert exc.value.status_code == 409


def test_get_client_ok(db_session: Session, client: Client):
    assert get_client(db_session, client.id)


def test_get_client_not_exist(db_session: Session, client: Client):
    with pytest.raises(HTTPException) as exc:
        get_client(db_session, 1234)

    assert exc.value.detail == "client_not_exist"


#
#
# def test_get_client_deleted(db_session: Session, client_deleted: Client):
#     with pytest.raises(HTTPException) as exc:
#         get_client(db_session, 4)
#
#     assert exc.value.detail == ("client_not_exist")
#
#
# # def test_create_update_client_address_ok(db_session: Session, client: Client):
# #     updated_client = create_update_client_address(
# #         db_session,
# #         client,
# #         {
# #             "type": "Street",
# #             "name": "Main",
# #             "number": 6,
# #             "postal_code": "999999",
# #             "city": "Miami",
# #             "province": "Florida",
# #         },
# #     )
# #
# #     assert updated_client.address.type == "Street"
# #     assert updated_client.address.name == "Main"
# #     assert updated_client.address.number == 6
# #     assert updated_client.address.postal_code == "999999"
# #     assert updated_client.address.city == "Miami"
# #     assert updated_client.address.province == "Florida"
#
#
# # def test_create_update_client_address_no_address_ok(
# #     db_session: Session, client: Client
# # ):
# #     client.address = None
# #
# #     updated_client = create_update_client_address(
# #         db_session,
# #         client,
# #         {
# #             "type": "Street",
# #             "name": "Main",
# #             "number": 6,
# #             "postal_code": "999999",
# #             "city": "Miami",
# #             "province": "Florida",
# #         },
# #     )
# #
# #     assert updated_client.address.type == "Street"
# #     assert updated_client.address.name == "Main"
# #     assert updated_client.address.number == 6
# #     assert updated_client.address.postal_code == "999999"
# #     assert updated_client.address.city == "Miami"
# #     assert updated_client.address.province == "Florida"
#
#
# def test_client_update_ok(db_session: Session, client: Client):
#     client_update(
#         db_session,
#         1,
#         ClientUpdateRequest(
#             name="Updated name",
#             fiscal_name="Fiscal name Updated",
#             cif="NEWCIF123",
#             email="updated_email@test.com",
#             fee=4.15,
#             max_consume=8.15,
#             consume_range_datetime=datetime.datetime(1998, 2, 2),
#             surplus_price=5.11,
#             address=AddressUpdateRequest(
#                 type="square",
#                 name="Main",
#                 number=3,
#                 postal_code="A1AB2B",
#                 city="Madrid",
#                 province="Madrid",
#             ),
#         ),
#     )
#
#     client = db_session.query(Client).filter(Client.id == 1).first()
#     assert client.id == 1
#     assert client.name == "Updated name"
#     assert client.fiscal_name == "Fiscal name Updated"
#     assert client.cif == "NEWCIF123"
#     assert client.email == "updated_email@test.com"
#     assert client.fee == Decimal("4.15")
#     assert client.max_consume == Decimal("8.15")
#     assert client.consume_range_datetime == datetime.datetime(1998, 2, 2)
#     assert client.surplus_price == Decimal("5.11")
#     assert client.address.id == 1
#     assert client.address.type == "square"
#     assert client.address.name == "Main"
#     assert client.address.number == 3
#     assert client.address.postal_code == "A1AB2B"
#     assert client.address.city == "Madrid"
#     assert client.address.province == "Madrid"
#
#
# def test_client_update_no_address_ok(db_session: Session, client_disabled: Client):
#     client = client_update(
#         db_session,
#         3,
#         ClientUpdateRequest(
#             name="Updated name",
#             fiscal_name="Fiscal name Updated",
#             cif="NEWCIF123",
#             email="updated_email@test.com",
#             fee=4.15,
#             max_consume=8.15,
#             consume_range_datetime=datetime.datetime(1998, 2, 2),
#             surplus_price=5.11,
#         ),
#     )
#
#     assert client.id == 3
#     assert client.name == "Updated name"
#     assert client.fiscal_name == "Fiscal name Updated"
#     assert client.cif == "NEWCIF123"
#     assert client.email == "updated_email@test.com"
#     assert client.fee == Decimal("4.15")
#     assert client.max_consume == Decimal("8.15")
#     assert client.consume_range_datetime == datetime.datetime(1998, 2, 2)
#     assert client.surplus_price == Decimal("5.11")
#     assert not client.is_active
#
#
# def test_client_update_empty_address_ok(
#     db_session: Session, client_disabled: Client, user_create: User
# ):
#     client = client_update(
#         db_session,
#         3,
#         ClientUpdateRequest(
#             name="Disabled client",
#             address=AddressUpdateRequest(),
#         ),
#     )
#     client = db_session.query(Client).filter(Client.id == 3).first()
#     assert client.id == 3
#     assert client.name == "Disabled client"
#     assert client.address
#     assert not client.address.name
#     assert not client.address.city
#
#
# def test_client_update_already_exists_error(
#     db_session: Session, client: Client, client2: Client
# ):
#     with pytest.raises(HTTPException) as exc:
#         client_update(
#             db_session,
#             2,
#             ClientUpdateRequest(
#                 name="Client",
#                 fiscal_name="Client official",
#                 cif="QWERTY123",
#                 email="client@test.com",
#             ),
#         )
#
#     assert exc.value.status_code == 409
#     assert exc.value.detail == "value_error.already_exists"
#
#
# def test_client_update_not_exists(db_session: Session, client2: Client):
#     with pytest.raises(HTTPException) as exc:
#         client_update(
#             db_session,
#             1,
#             ClientUpdateRequest(
#                 name="Updated name",
#                 fiscal_name="Fiscal name Updated",
#                 cif="NEWCIF123",
#                 email="updated_email@test.com",
#             ),
#         )
#
#     assert exc.value.detail == ("client_not_exist")
#     client = db_session.query(Client).filter(Client.id == 2).first()
#     assert client.id == 2
#     assert client.name == "Client secondary"
#     assert client.cif == "ABCDEF123"
#
#
# def test_client_update_invalid_cif_value(db_session: Session, client: Client):
#     with pytest.raises(ValidationError) as exc:
#         client_update(
#             db_session,
#             1,
#             ClientUpdateRequest(
#                 name="Updated name",
#                 fiscal_name="Fiscal name Updated",
#                 cif="TOOLONGCIF1234",
#                 email="updated_email@test.com",
#             ),
#         )
#
#     assert exc.value.errors()[0]["type"] == "value_error.any_str.max_length"
#     assert exc.value.errors()[0]["msg"] == (
#         "ensure this value has at most 9 characters"
#     )
#     client = db_session.query(Client).filter(Client.id == 1).first()
#     assert client.cif == "QWERTY123"
#
#
# def test_client_update_invalid_fee_value(db_session: Session, client: Client):
#     with pytest.raises(ValidationError) as exc:
#         client_update(
#             db_session,
#             1,
#             ClientUpdateRequest(
#                 name="Updated name",
#                 fiscal_name="Fiscal name Updated",
#                 cif="NEWCIF123",
#                 email="updated_email@test.com",
#                 fee="23.36521547",
#             ),
#         )
#
#     assert exc.value.errors()[0]["type"] == "value_error.decimal.max_places"
#     assert exc.value.errors()[0]["msg"] == (
#         "ensure that there are no more than 6 decimal places"
#     )
#     client = db_session.query(Client).filter(Client.id == 1).first()
#     assert client.fee == Decimal("15.4")
#
#
# def test_client_partial_update_ok(db_session: Session, client: Client):
#     client = client_partial_update(
#         db_session, 1, ClientPartialUpdateRequest(is_active=False, is_deleted=True)
#     )
#
#     assert client.id == 1
#     assert not client.is_active
#     assert client.is_deleted
#
#
# def test_client_partial_update_not_used_field_ok(db_session: Session, client: Client):
#     client = client_partial_update(
#         db_session,
#         1,
#         ClientPartialUpdateRequest(is_active=False, name="Name updated"),
#     )
#
#     assert client.id == 1
#     assert client.name == "Client"
#     assert not client.is_active
#     assert not client.is_deleted
#
#
# def test_delete_clients_ok(
#     db_session: Session,
#     client: Client,
#     client2: Client,
#     client_disabled: Client,
#     client_deleted: Client,
# ):
#     delete_clients(db_session, ClientDeleteRequest(ids=[1, 3, 4, 84]))
#
#     assert db_session.query(Client).filter(Client.is_deleted == false()).count() == 1
#
#
# def test_delete_clients_empty_ok(
#     db_session: Session,
#     client: Client,
#     client2: Client,
#     client_disabled: Client,
#     client_deleted: Client,
# ):
#     delete_clients(db_session, ClientDeleteRequest(ids=[]))
#
#     assert db_session.query(Client).filter(Client.is_deleted == false()).count() == 3
