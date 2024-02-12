import typer
from sqlalchemy.orm import sessionmaker

from src.infrastructure.sqlalchemy.database import engine
from src.modules.commissions.models import Commission  # noqa
from src.modules.margins.models import Margin  # noqa
from src.modules.rates.models import RateType

app = typer.Typer(help="Create new rate_types.")


@app.command(help="Create a new rate_type.", name="create")
def create_rate_type(rate_type_name: str, user_id: int):
    with sessionmaker(autocommit=False, autoflush=True, bind=engine)() as session:
        rate_type = RateType(
            name=rate_type_name,
            energy_type="electricity",
            user_id=user_id,
        )
        session.add(rate_type)
        session.commit()
    # success message
    typer.echo(f"RateType {rate_type_name} created successfully.")


@app.command(help="Show all rate_types.", name="show-all")
def show_rate_types():
    with sessionmaker(autocommit=False, autoflush=True, bind=engine)() as session:
        rate_types = session.query(RateType).all()
    # success message
    for rate_type in rate_types:
        typer.echo(
            f"RateType: {rate_type.id=} {rate_type.name=} {rate_type.energy_type=} "
            f"{rate_type.is_deleted=}"
        )
