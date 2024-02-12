import datetime
from typing import List

import psycopg2
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from fastapi_mail import FastMail
from passlib.hash import pbkdf2_sha256
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy.orm import Session

from config.settings import settings
from main import app
from src.infrastructure.email.email_config import EmailConfig
from src.infrastructure.sqlalchemy.database import Base, engine, get_db
from src.modules.clients.models import Client, InvoiceNotificationType
from src.modules.commissions.models import Commission, RangeType
from src.modules.contacts.models import Contact
from src.modules.costs.models import EnergyCost, OtherCost, OtherCostType
from src.modules.margins.models import Margin, MarginType
from src.modules.marketers.models import Address, Marketer
from src.modules.rates.models import (
    ClientType,
    EnergyType,
    HistoricalRate,
    PriceName,
    PriceType,
    Rate,
    RateType,
)
from src.modules.saving_studies.models import SavingStudy, SuggestedRate
from src.modules.users.models import Token, User, UserRole

TEST_DATABASE_URI = (
    f"postgres://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)


def postgresql_connection(initial: bool = False):
    database_uri = (
        "/".join(TEST_DATABASE_URI.split("/")[:-1]) if initial else TEST_DATABASE_URI
    )
    con = psycopg2.connect(database_uri)
    con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return con


def delete_database():
    if not settings.POSTGRES_DB.startswith("test_"):
        raise Exception(f"Invalid name for database = {settings.POSTGRES_DB}")

    sql_drop_db = f"DROP DATABASE IF EXISTS {settings.POSTGRES_DB}"
    con = postgresql_connection(initial=True)
    cursor = con.cursor()
    cursor.execute(
        f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE"
        f"  pg_stat_activity.datname = '{settings.POSTGRES_DB}' AND pid <> pg_backend_pid();"
    )
    cursor.execute(sql_drop_db)
    con.close()


def create_database():
    sql_create_db = (
        f"CREATE DATABASE {settings.POSTGRES_DB} WITH "
        f"OWNER = {settings.POSTGRES_USER} ENCODING = 'UTF8' CONNECTION LIMIT = -1;"
    )

    con = postgresql_connection(initial=True)
    cursor = con.cursor()
    cursor.execute(sql_create_db)
    con.close()
    con = postgresql_connection()
    cursor = con.cursor()
    cursor.execute("CREATE EXTENSION IF NOT EXISTS unaccent;")
    con.close()


def pytest_sessionstart(session):
    delete_database()
    create_database()

    # Run Alembic migrations
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    Base.metadata.create_all(engine)


def pytest_sessionfinish(session, exitstatus):
    delete_database()


@pytest.fixture
def hashed_password_example() -> str:
    # Hash from argon2 to the password Fakepassword1234
    return "$argon2id$v=19$m=65536,t=2,p=4$RHVtbXktU2VjcmV0LUtFWQ$+TuEF1Bf1d8JfuuLJJzFUxGb7NmVWa+i6jr0rw4Li+0"


@pytest.fixture
def fake_hash_sha256(expire_date_timestamp_valid: float) -> str:
    # Hash from sha256 to the password Fakepassword1234
    return pbkdf2_sha256.hash(
        f"1test@user.com{expire_date_timestamp_valid}{settings.SECRET_KEY}"
    )


@pytest.fixture
def fake_hash_sha256_invalid(expire_date_timestamp_valid: float) -> str:
    # Hash from sha256 to the password Fakepassword1234
    return pbkdf2_sha256.hash("fake_hash")


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def test_client(db_session: Session) -> TestClient:
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture()
def user_create(db_session: Session, hashed_password_example: str) -> User:
    user = User(
        id=1,
        email="test@user.com",
        first_name="John",
        last_name="Graham",
        hashed_password=hashed_password_example,
        role=UserRole.admin,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def user_inactive_create(db_session: Session, hashed_password_example: str) -> User:
    user = User(
        id=5,
        email="inactive@user.com",
        first_name="Inactivename",
        last_name="Inactivesurname",
        role=UserRole.admin,
        hashed_password=hashed_password_example,
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def user_deleted_create(db_session: Session, hashed_password_example: str) -> User:
    user = User(
        id=3,
        email="test_deleted@user.com",
        first_name="John deleted",
        last_name="Graham deleted",
        hashed_password=hashed_password_example,
        role=UserRole.admin,
        is_active=True,
        is_deleted=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def user_create2(db_session: Session, hashed_password_example: str) -> User:
    user = User(
        id=2,
        email="test2@user.com",
        first_name="Johnathan",
        last_name="Smith",
        role=UserRole.admin,
        hashed_password=hashed_password_example,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def user_create3(db_session: Session, hashed_password_example: str) -> User:
    user = User(
        id=6,
        email="test3@user.com",
        first_name="Emma",
        last_name="Williams",
        role=UserRole.admin,
        hashed_password=hashed_password_example,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def superadmin(db_session: Session, hashed_password_example: str) -> User:
    user = User(
        id=4,
        email="superadmin@user.com",
        first_name="super",
        last_name="admin",
        role=UserRole.super_admin,
        hashed_password=hashed_password_example,
        is_active=True,
        is_superadmin=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def token_create(db_session: Session, user_create: User) -> Token:
    token = Token(
        token="SDFGegwew56452367",
        user_id=user_create.id,
    )
    db_session.add(token)
    db_session.commit()
    return token


@pytest.fixture()
def token_superadmin(db_session: Session, superadmin: User) -> Token:
    token = Token(
        token="SDFGegwew56452367",
        user_id=superadmin.id,
    )
    db_session.add(token)
    db_session.commit()
    return token


@pytest.fixture()
def fm():
    fm = FastMail(EmailConfig.conf)
    return fm


@pytest.fixture
def expire_date_timestamp_valid() -> float:
    expiration_datetime = datetime.datetime.now() + datetime.timedelta(
        seconds=settings.RESET_PASSWORD_TOKEN_LIFETIME_SECONDS
    )
    return datetime.datetime.timestamp(expiration_datetime)


@pytest.fixture
def expire_date_timestamp_invalid() -> float:
    expiration_datetime = datetime.datetime.now() - datetime.timedelta(
        seconds=settings.RESET_PASSWORD_TOKEN_LIFETIME_SECONDS
    )
    return datetime.datetime.timestamp(expiration_datetime)


@pytest.fixture()
def rate_type_with_accent(db_session: Session, user_create: User) -> RateType:
    rate_type = RateType(
        name="Tést",
        energy_type="gas",
        user_id=user_create.id,
    )
    db_session.add(rate_type)
    db_session.commit()
    return rate_type


@pytest.fixture()
def electricity_rate_type(db_session: Session, user_create: User) -> RateType:
    rate_type = RateType(
        id=1,
        enable=True,
        is_deleted=False,
        name="Electricity rate type",
        energy_type="electricity",
        max_power=30.30,
        min_power=1.5,
        user=user_create,
    )
    db_session.add(rate_type)
    db_session.commit()
    return rate_type


@pytest.fixture()
def gas_rate_type(db_session: Session, user_create: User) -> RateType:
    rate_type = RateType(
        id=2,
        name="Gas rate type",
        energy_type="gas",
        user=user_create,
    )
    db_session.add(rate_type)
    db_session.commit()
    return rate_type


@pytest.fixture()
def gas_rate_type_2(db_session: Session, user_create: User) -> RateType:
    rate_type = RateType(
        id=5,
        name="Gas rate type 2",
        energy_type="gas",
        user=user_create,
    )
    db_session.add(rate_type)
    db_session.commit()
    return rate_type


@pytest.fixture()
def disable_rate_type(db_session: Session, user_create: User) -> RateType:
    rate_type = RateType(
        id=3,
        name="Disable rate type",
        energy_type="electricity",
        max_power=21.54,
        min_power=0,
        enable=False,
        user=user_create,
    )
    db_session.add(rate_type)
    db_session.commit()
    return rate_type


@pytest.fixture()
def deleted_rate_type(db_session: Session, user_create: User) -> RateType:
    rate_type = RateType(
        id=4,
        name="Deleted rate type",
        energy_type="electricity",
        max_power=30.30,
        min_power=0,
        is_deleted=True,
        user=user_create,
    )
    db_session.add(rate_type)
    db_session.commit()
    return rate_type


@pytest.fixture()
def energy_cost(db_session: Session, user_create: User) -> EnergyCost:
    energy_cost = EnergyCost(
        id=1,
        concept="gas installation",
        amount=56.28,
        user=user_create,
    )
    db_session.add(energy_cost)
    db_session.commit()
    return energy_cost


@pytest.fixture()
def energy_cost2(db_session: Session, user_create2: User) -> EnergyCost:
    energy_cost = EnergyCost(
        id=2,
        concept="Installation check",
        amount=26.32,
        user=user_create2,
    )
    db_session.add(energy_cost)
    db_session.commit()
    return energy_cost


@pytest.fixture()
def energy_cost_protected(db_session: Session, superadmin: User) -> EnergyCost:
    energy_cost = EnergyCost(
        id=3, concept="IVA", amount=21, is_protected=True, user=superadmin, code="iva"
    )
    db_session.add(energy_cost)
    db_session.commit()
    return energy_cost


@pytest.fixture()
def energy_cost_electric_tax(db_session: Session, superadmin: User) -> EnergyCost:
    energy_cost = EnergyCost(
        id=5,
        concept="Impuesto electrico",
        amount=5.117,
        is_protected=True,
        user=superadmin,
        code="imp_electricos",
    )
    db_session.add(energy_cost)
    db_session.commit()
    return energy_cost


@pytest.fixture()
def energy_cost_hydrocarbons_tax(db_session: Session, superadmin: User) -> EnergyCost:
    energy_cost = EnergyCost(
        id=5,
        concept="Impuestos de hibrocarburos",
        amount=0.234,
        is_protected=True,
        user=superadmin,
        code="imp_hidrocarburos",
    )
    db_session.add(energy_cost)
    db_session.commit()
    return energy_cost


@pytest.fixture()
def energy_cost_deleted(db_session: Session, user_create: User) -> EnergyCost:
    energy_cost = EnergyCost(
        id=4,
        concept="Deleted cost",
        amount=21,
        is_deleted=True,
        user=user_create,
    )
    db_session.add(energy_cost)
    db_session.commit()
    return energy_cost


@pytest.fixture()
def other_cost(
    db_session: Session,
    electricity_rate: Rate,
) -> OtherCost:
    other_cost = OtherCost(
        id=1,
        name="Other cost",
        mandatory=True,
        client_types=[ClientType.particular, ClientType.company],
        min_power=3.5,
        max_power=23.5,
        type=OtherCostType.eur_month,
        quantity=32,
        extra_fee=17.1,
        rates=[electricity_rate],
    )
    db_session.add(other_cost)
    db_session.commit()
    return other_cost


@pytest.fixture()
def other_cost_2_rates(
    db_session: Session,
    electricity_rate: Rate,
    electricity_rate_2: Rate,
) -> OtherCost:
    other_cost = OtherCost(
        id=2,
        name="Other cost 2",
        mandatory=True,
        client_types=[ClientType.community_owners],
        min_power=27.8,
        max_power=33.5,
        type=OtherCostType.eur_month,
        quantity=27,
        extra_fee=7.1,
        rates=[electricity_rate, electricity_rate_2],
    )
    db_session.add(other_cost)
    db_session.commit()
    return other_cost


@pytest.fixture()
def other_costs(
    db_session: Session,
    electricity_rate: Rate,
) -> List[OtherCost]:
    other_costs = [
        OtherCost(
            id=1,
            name="Other cost 1",
            mandatory=True,
            client_types=[ClientType.particular, ClientType.company],
            min_power=3.5,
            max_power=23.5,
            type=OtherCostType.eur_month,
            quantity=13,
            extra_fee=17.1,
            rates=[electricity_rate],
        ),
        OtherCost(
            id=2,
            name="Other cost 2",
            mandatory=True,
            client_types=[ClientType.particular, ClientType.company],
            min_power=3.5,
            max_power=33.5,
            type=OtherCostType.percentage,
            quantity=0.12,
            extra_fee=7.1,
            rates=[electricity_rate],
        ),
        OtherCost(
            id=3,
            name="Other cost 3",
            mandatory=True,
            client_types=[ClientType.particular, ClientType.company],
            min_power=3.5,
            max_power=23.5,
            type=OtherCostType.eur_kwh,
            quantity=1.22,
            extra_fee=17.1,
            rates=[electricity_rate],
        ),
    ]
    db_session.add_all(other_costs)
    db_session.commit()
    return other_costs


@pytest.fixture()
def other_cost_disabled(
    db_session: Session,
    electricity_rate: Rate,
) -> OtherCost:
    other_cost = OtherCost(
        id=3,
        name="Other cost disabled",
        mandatory=False,
        client_types=[ClientType.particular, ClientType.company],
        min_power=41.1,
        max_power=73.3,
        type=OtherCostType.eur_month,
        quantity=17,
        extra_fee=1.1,
        rates=[electricity_rate],
        is_active=False,
    )
    db_session.add(other_cost)
    db_session.commit()
    return other_cost


@pytest.fixture()
def address(db_session: Session) -> Address:
    address = Address(
        id=1,
        type="Avenue",
        name="Fifth",
        number=1,
        postal_code="10021",
        city="New York",
        province="New York State",
    )
    db_session.add(address)
    db_session.commit()
    return address


@pytest.fixture()
def marketer(db_session: Session, user_create: User, address: Address) -> Marketer:
    marketer = Marketer(
        id=1,
        name="Marketer",
        fiscal_name="Marketer official",
        cif="QWERTY123",
        email="marketer@test.com",
        fee=15.4,
        max_consume=150.8,
        consume_range_datetime=datetime.datetime(2008, 8, 21),
        surplus_price=22.5,
        user=user_create,
        address=address,
    )
    db_session.add(marketer)
    db_session.commit()
    return marketer


@pytest.fixture()
def marketer_active(
    db_session: Session, user_create: User, address: Address
) -> Marketer:
    # get or create marketer
    marketer = Marketer(
        id=2,
        name="Marketer",
        fiscal_name="Marketer official 2",
        cif="QWERTY124",
        email="marketer@test.com",
        fee=15.4,
        max_consume=150.8,
        consume_range_datetime=datetime.datetime(2008, 8, 21),
        surplus_price=22.5,
        user=user_create,
        address=address,
        is_active=True,
    )
    db_session.add(marketer)
    db_session.commit()
    return marketer


@pytest.fixture()
def marketer2(db_session: Session, user_create2: User, address: Address) -> Marketer:
    marketer = Marketer(
        id=2,
        name="Marketer secondary",
        fiscal_name="Official second marketer",
        cif="ABCDEF123",
        email="marketer@second.com",
        user=user_create2,
        address=address,
    )
    db_session.add(marketer)
    db_session.commit()
    return marketer


@pytest.fixture()
def marketer_disabled(db_session: Session, superadmin: User) -> Marketer:
    marketer = Marketer(
        id=3,
        name="Disabled marketer",
        fiscal_name="Official disabled marketer",
        cif="DISABLED1",
        email="disabled@marketer.com",
        user=superadmin,
        is_active=False,
    )
    db_session.add(marketer)
    db_session.commit()
    return marketer


@pytest.fixture()
def marketer_deleted(
    db_session: Session, user_create: User, address: Address
) -> Marketer:
    marketer = Marketer(
        id=4,
        name="Deleted marketer",
        fiscal_name="Official deleted marketer",
        cif="DELETED12",
        email="deleted@marketer.com",
        user=user_create,
        is_deleted=True,
        address=address,
    )
    db_session.add(marketer)
    db_session.commit()
    return marketer


@pytest.fixture()
def electricity_rate(
    db_session: Session, marketer: Marketer, electricity_rate_type: RateType
) -> Rate:
    electricity_rate = Rate(
        id=1,
        name="Electricity rate",
        price_type=PriceType.fixed_fixed,
        client_types=[ClientType.particular],
        min_power=10.5,
        max_power=23.39,
        min_consumption=12.5,
        max_consumption=23.39,
        energy_price_1=17.19,
        energy_price_2=5.9,
        energy_price_3=87.73,
        energy_price_4=2.43,
        energy_price_5=12.23,
        energy_price_6=9.55,
        power_price_1=19.17,
        power_price_2=9.5,
        power_price_3=73.87,
        power_price_4=43.2,
        power_price_5=23.12,
        power_price_6=55.9,
        permanency=True,
        length=12,
        is_full_renewable=True,
        compensation_surplus=True,
        compensation_surplus_value=28.32,
        rate_type_id=electricity_rate_type.id,
        marketer_id=marketer.id,
    )
    db_session.add(electricity_rate)
    db_session.commit()
    return electricity_rate


@pytest.fixture()
def electricity_rate_2(
    db_session: Session, marketer: Marketer, electricity_rate_type: RateType
) -> Rate:
    electricity_rate = Rate(
        id=4,
        name="Electricity rate 2",
        price_type=PriceType.fixed_fixed,
        client_types=[ClientType.particular, ClientType.self_employed],
        min_power=10.5,
        max_power=23.39,
        energy_price_1=17.19,
        permanency=True,
        length=12,
        is_full_renewable=True,
        compensation_surplus=True,
        compensation_surplus_value=28.32,
        rate_type_id=electricity_rate_type.id,
        marketer_id=marketer.id,
    )
    db_session.add(electricity_rate)
    db_session.commit()
    return electricity_rate


@pytest.fixture()
def electricity_rate_active_marketer(
    db_session: Session, marketer_active: Marketer, electricity_rate_type: RateType
) -> Rate:
    electricity_rate = Rate(
        id=5,
        is_active=True,
        is_deleted=False,
        name="Electricity rate active marketer",
        price_type=PriceType.fixed_fixed,
        client_types=[ClientType.particular],
        min_power=2.5,
        max_power=23.39,
        min_consumption=10.55,
        max_consumption=100.55,
        energy_price_1=17.19,
        permanency=True,
        length=12,
        is_full_renewable=True,
        compensation_surplus=True,
        compensation_surplus_value=28.32,
        rate_type_id=electricity_rate_type.id,
        marketer_id=marketer_active.id,
    )
    db_session.add(electricity_rate)
    db_session.commit()
    return electricity_rate


@pytest.fixture()
def gas_rate(db_session: Session, marketer: Marketer, gas_rate_type: RateType) -> Rate:
    gas_rate = Rate(
        id=2,
        name="Gas rate name",
        price_type=PriceType.fixed_base,
        client_types=[ClientType.particular],
        energy_price_1=17.19,
        permanency=False,
        length=24,
        rate_type_id=gas_rate_type.id,
        marketer_id=marketer.id,
    )
    db_session.add(gas_rate)
    db_session.commit()
    return gas_rate


@pytest.fixture()
def gas_rate_active(
    db_session: Session, marketer_active: Marketer, gas_rate_type: RateType
) -> Rate:
    gas_rate = Rate(
        id=6,
        name="Gas rate name active",
        price_type=PriceType.fixed_base,
        client_types=[ClientType.particular],
        energy_price_1=17.19,
        permanency=False,
        length=24,
        rate_type_id=gas_rate_type.id,
        marketer_id=marketer_active.id,
    )
    db_session.add(gas_rate)
    db_session.commit()
    return gas_rate


@pytest.fixture()
def gas_rate_deleted(
    db_session: Session, marketer: Marketer, gas_rate_type: RateType
) -> Rate:
    gas_rate = Rate(
        id=3,
        name="Gas rate name deleted",
        price_type=PriceType.fixed_base,
        client_types=[ClientType.particular],
        energy_price_1=17.19,
        permanency=False,
        length=24,
        rate_type_id=gas_rate_type.id,
        marketer_id=marketer.id,
        is_deleted=True,
    )
    db_session.add(gas_rate)
    db_session.commit()
    return gas_rate


@pytest.fixture()
def historical_electricity_rate(
    db_session: Session, electricity_rate: Rate
) -> HistoricalRate:
    historical_electrical_rate = HistoricalRate(
        id=1,
        price_name=PriceName.energy_price_3,
        price=23.56,
        rate=electricity_rate,
    )
    db_session.add(historical_electrical_rate)
    db_session.commit()
    return historical_electrical_rate


@pytest.fixture()
def margin(db_session: Session, gas_rate: Rate) -> Margin:
    margin = Margin(
        id=1,
        type=MarginType.consume_range,
        min_consumption=12.5,
        max_consumption=23.39,
        min_margin=16.3,
        max_margin=61.2,
        rate_id=2,
    )
    db_session.add(margin)
    db_session.commit()
    return margin


@pytest.fixture()
def margin_rate_type(db_session: Session, electricity_rate: Rate) -> Margin:
    margin = Margin(
        id=2,
        type=MarginType.rate_type,
        min_margin=6.32,
        max_margin=23.6,
        rate_id=1,
    )
    db_session.add(margin)
    db_session.commit()
    return margin


@pytest.fixture()
def margin_consume_range(db_session: Session, gas_rate: Rate) -> Margin:
    margin = Margin(
        id=3,
        type=MarginType.consume_range,
        min_consumption=3.5,
        max_consumption=11.5,
        min_margin=16.32,
        max_margin=61.23,
        rate_id=2,
    )
    db_session.add(margin)
    db_session.commit()
    return margin


@pytest.fixture()
def commission(db_session: Session, electricity_rate: Rate) -> Commission:
    commission = Commission(
        id=1,
        name="Commission name",
        range_type=RangeType.consumption,
        min_consumption=3.5,
        max_consumption=11.5,
        Test_commission=12,
        rate_type_segmentation=True,
        rate_type_id=1,
        rates=[electricity_rate],
    )
    db_session.add(commission)
    db_session.commit()
    return commission


@pytest.fixture()
def commission_2(db_session: Session, electricity_rate_2: Rate) -> Commission:
    commission = Commission(
        id=4,
        name="Commission name 2",
        range_type=RangeType.consumption,
        min_consumption=5,
        max_consumption=12.5,
        Test_commission=12,
        rate_type_segmentation=False,
        rates=[electricity_rate_2],
    )
    db_session.add(commission)
    db_session.commit()
    return commission


@pytest.fixture()
def commission_power(db_session: Session, electricity_rate: Rate) -> Commission:
    commission = Commission(
        id=3,
        name="Commission name",
        range_type=RangeType.power,
        min_power=3.5,
        max_power=11.5,
        Test_commission=16,
        rate_type_segmentation=True,
        rate_type_id=1,
        rates=[electricity_rate],
    )
    db_session.add(commission)
    db_session.commit()
    return commission


@pytest.fixture()
def commission_fixed_base(db_session: Session, gas_rate: Rate) -> Commission:
    commission = Commission(
        id=2,
        name="Commission fixed base",
        percentage_Test_commission=12,
        rates=[gas_rate],
    )
    db_session.add(commission)
    db_session.commit()
    return commission


@pytest.fixture()
def saving_study(
    db_session: Session,
    user_create: User,
    electricity_rate_type: RateType,
    electricity_rate_active_marketer: Rate,
) -> SavingStudy:
    electricity_rate_active_marketer.rate_type_id = electricity_rate_type.id
    saving_study = SavingStudy(
        id=1,
        user_creator_id=user_create.id,
        energy_type=EnergyType.electricity,
        is_existing_client=False,
        is_from_sips=False,
        is_compare_conditions=False,
        cups="ES0021000000000000AA",
        client_type=ClientType.particular,
        client_name="Client name",
        client_nif="12345678A",
        current_rate_type_id=electricity_rate_type.id,
        analyzed_days=365,
        energy_price_1=27.3,
        energy_price_6=23.6,
        power_6=5.75,
        annual_consumption=15.34,
    )
    db_session.add(electricity_rate_active_marketer)
    db_session.add(saving_study)
    db_session.commit()
    return saving_study


@pytest.fixture()
def deleted_saving_study(
    db_session: Session,
    user_create: User,
    electricity_rate_type: RateType,
    electricity_rate_active_marketer: Rate,
) -> SavingStudy:
    electricity_rate_active_marketer.rate_type_id = electricity_rate_type.id
    saving_study = SavingStudy(
        id=2,
        user_creator_id=user_create.id,
        energy_type=EnergyType.electricity,
        is_existing_client=False,
        is_from_sips=False,
        is_compare_conditions=False,
        cups="ES0021000000000000AA",
        client_type=ClientType.company,
        client_name="Client name",
        client_nif="12345678A",
        current_rate_type_id=electricity_rate_type.id,
        analyzed_days=365,
        energy_price_1=27.3,
        annual_consumption=50.5,
        power_6=5.5,
        is_deleted=True,
    )
    db_session.add(electricity_rate_active_marketer)
    db_session.add(saving_study)
    db_session.commit()
    return saving_study


@pytest.fixture()
def saving_study_2(
    db_session: Session,
    user_create: User,
    electricity_rate_type: RateType,
    electricity_rate_active_marketer: Rate,
) -> SavingStudy:
    electricity_rate_active_marketer.rate_type_id = electricity_rate_type.id
    saving_study = SavingStudy(
        id=3,
        user_creator_id=user_create.id,
        energy_type=EnergyType.gas,
        is_existing_client=False,
        is_from_sips=False,
        is_compare_conditions=False,
        cups="ES0021000000000000AA",
        client_type=ClientType.particular,
        client_name="Client name",
        client_nif="12345678A",
        current_rate_type_id=electricity_rate_type.id,
        analyzed_days=100,
        energy_price_1=37.3,
        energy_price_6=33.6,
        power_6=15.75,
        annual_consumption=15.34,
    )
    db_session.add(electricity_rate_active_marketer)
    db_session.add(saving_study)
    db_session.commit()
    return saving_study


@pytest.fixture()
def suggested_rate(db_session: Session, saving_study: SavingStudy) -> SuggestedRate:
    suggested_rate = SuggestedRate(
        id=1,
        saving_study_id=saving_study.id,
        marketer_name="Marketer name",
        has_contractual_commitment=True,
        duration=12,
        rate_name="Rate name",
        is_full_renewable=True,
        has_net_metering=True,
        net_metering_value=12.3,
        applied_profit_margin=12.3,
        min_profit_margin=16.3,
        max_profit_margin=61.2,
        profit_margin_type=MarginType.rate_type,
        is_selected=False,
        energy_price_1=112.3,
        power_price_1=23.4,
    )
    db_session.add(suggested_rate)
    db_session.commit()
    return suggested_rate


@pytest.fixture()
def suggested_rates(db_session: Session, saving_study: SavingStudy) -> SuggestedRate:
    suggested_rates = []
    for i in range(1, 5):
        suggested_rate = SuggestedRate(
            id=i,
            saving_study_id=saving_study.id,
            marketer_name=f"Marketer name {i}",
            has_contractual_commitment=True,
            duration=12,
            rate_name=f"Rate name {i}",
            is_full_renewable=True,
            has_net_metering=True,
            net_metering_value=12.3,
            applied_profit_margin=12.3,
            profit_margin_type=MarginType.rate_type,
            min_profit_margin=12.3,
            max_profit_margin=23.6,
            is_selected=False,
        )
        db_session.add(suggested_rate)
        suggested_rates.append(suggested_rate)
    db_session.commit()
    return suggested_rates


@pytest.fixture()
def client(db_session: Session, user_create: User) -> Client:
    client = Client(
        id=1,
        user_id=user_create.id,
        alias="Alias",
        client_type=ClientType.company,
        fiscal_name="Fiscal name",
        cif="123456789",
        invoice_notification_type=InvoiceNotificationType.email,
        invoice_email="test@test.com",
        bank_account_holder="Bank account holder",
        bank_account_number="Bank account number",
        fiscal_address="fiscal address",
        is_renewable=True,
    )
    db_session.add(client)
    db_session.commit()
    return client


@pytest.fixture()
def contact(db_session: Session, user_create: User, client: Client) -> Contact:
    contact = Contact(
        id=1,
        name="contact name",
        email="test@test.com",
        phone="666666666",
        client_id=client.id,
        user_id=user_create.id,
    )
    db_session.add(contact)
    db_session.commit()
    return contact
