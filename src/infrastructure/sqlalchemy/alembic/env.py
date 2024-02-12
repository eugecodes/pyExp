from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
from src.infrastructure.sqlalchemy.database import SQLALCHEMY_DATABASE_URL, Base
from src.modules.clients.models import Base as ClientsBase  # noqa
from src.modules.commissions.models import Base as CommissionsBase  # noqa
from src.modules.contacts.models import Base as ContactsBase  # noqa
from src.modules.contracts.models import Base as ContractsBase  # noqa
from src.modules.costs.models import Base as CostsBase  # noqa
from src.modules.margins.models import Base as MarginsBase  # noqa
from src.modules.marketers.models import Base as MarketersBase  # noqa
from src.modules.rates.models import Base as RatesBase  # noqa
from src.modules.saving_studies.models import Base as SavingStudiesBase  # noqa
from src.modules.supply_points.models import Base as SupplyPointBase  # noqa
from src.modules.users.models import Base as UsersBase  # noqa

# Import models base to add models to database Base

config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
section = config.config_ini_section
config.set_section_option(section, "DATABASE_URL", SQLALCHEMY_DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, compare_type=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
