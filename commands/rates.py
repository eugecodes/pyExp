import typer
from sqlalchemy.orm import sessionmaker

from src.infrastructure.sqlalchemy.database import engine
from src.modules.rates.models import Rate

app = typer.Typer(help="Create new rates.")


@app.command(help="Create rate.", name="create")
def create_rate(rate_name: str, rate_type_id: int, marketer_id: int):
    with sessionmaker(autocommit=False, autoflush=True, bind=engine)() as session:
        rate = Rate(
            name=rate_name,
            price_type="fixed_fixed",
            client_types=["particular"],
            min_power=10.5,
            max_power=23.39,
            energy_price_1=17.19,
            permanency=True,
            length=12,
            is_full_renewable=True,
            rate_type_id=rate_type_id,
            marketer_id=marketer_id,
        )

        session.add(rate)
        session.commit()
    # success message
    typer.echo(f"Rate {rate_name} created successfully.")


@app.command(help="Show all rates.", name="show-all")
def show_rates():
    with sessionmaker(autocommit=False, autoflush=True, bind=engine)() as session:
        rates = session.query(Rate).all()
    # success message
    for rate in rates:
        typer.echo(
            f"Rate: {rate.id=} {rate.name=} {rate.price_type=} {rate.client_types=} "
            f"{rate.rate_type_id=} {rate.marketer_id=} {rate.is_active=} {rate.is_deleted=}"
        )
