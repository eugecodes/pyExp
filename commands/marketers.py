import typer
from sqlalchemy.orm import sessionmaker

from src.infrastructure.sqlalchemy.database import engine
from src.modules.marketers.models import Marketer

app = typer.Typer(help="Create new marketers.")


@app.command(help="Create marketer.", name="create")
def create_marketer(user_id: int, marketer_name: str):
    with sessionmaker(autocommit=False, autoflush=True, bind=engine)() as session:
        marketer = Marketer(
            name=marketer_name,
            fiscal_name="Marketer official",
            cif="QWERTY123",
            email="marketer@test.com",
            user_id=user_id,
        )

        session.add(marketer)
        session.commit()
    # success message
    typer.echo(f"Marketer {marketer.name} created successfully.")


@app.command(help="Show all marketers.", name="show-all")
def show_marketers():
    with sessionmaker(autocommit=False, autoflush=True, bind=engine)() as session:
        marketers = session.query(Marketer).all()
    # success message
    for marketer in marketers:
        typer.echo(
            f"Marketer: {marketer.id=} {marketer.name=} {marketer.fiscal_name=} "
            f"{marketer.cif=} {marketer.email=} {marketer.is_active=} {marketer.is_deleted=}"
        )
