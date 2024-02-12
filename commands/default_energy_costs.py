import typer
from sqlalchemy.orm import sessionmaker

from src.infrastructure.sqlalchemy.database import engine
from src.modules.costs.models import EnergyCost
from src.modules.users.models import User

app = typer.Typer(help="Create default energy costs.")


@app.command(help="Create default energy costs.", name="create")
def create_default_energy_costs(user_email: str):
    with sessionmaker(autocommit=False, autoflush=True, bind=engine)() as session:
        user = session.query(User).filter(User.email == user_email).first()
        if not user:
            typer.echo(f"User with email {user_email} does not exist.")
            return
        iva = EnergyCost(
            concept="IVA (%)", amount=21, is_protected=True, user_id=user.id, code="iva"
        )
        session.add(iva)
        iva_reducido = EnergyCost(
            concept="IVA Reducido (%)",
            amount=5,
            is_protected=True,
            user_id=user.id,
            code="iva_reducido",
        )
        session.add(iva_reducido)
        imp_hidrocarburos = EnergyCost(
            concept="Impuestos de hidrocarburos (€/kWh)",
            amount=0.00234,
            is_protected=True,
            user_id=user.id,
            code="imp_hidrocarburos",
        )
        session.add(imp_hidrocarburos)
        imp_electricos = EnergyCost(
            concept="Impuestos eléctricos (%)",
            amount=5.1127,
            is_protected=True,
            user_id=user.id,
            code="imp_electricos",
        )
        session.add(imp_electricos)
        session.commit()
        # success message
        typer.echo(f"Energy Cost {iva.concept} created successfully.")
        typer.echo(f"Energy Cost {iva_reducido.concept} created successfully.")
        typer.echo(f"Energy Cost {imp_hidrocarburos.concept} created successfully.")
        typer.echo(f"Energy Cost {imp_electricos.concept} created successfully.")


@app.command(help="Show all energy-costs.", name="show-all")
def show_energy_costs():
    with sessionmaker(autocommit=False, autoflush=True, bind=engine)() as session:
        energy_costs = session.query(EnergyCost).all()
        # success message
        for energy_cost in energy_costs:
            typer.echo(
                f"Energy Cost: {energy_cost.id=} {energy_cost.concept=} {energy_cost.amount=} {energy_cost.is_active=} "
                f"{energy_cost.is_deleted=} {energy_cost.is_protected=}"
            )


@app.command(help="Delete energy-costs.", name="delete")
def delete_energy_costs(energy_cost_id: int):
    with sessionmaker(autocommit=False, autoflush=True, bind=engine)() as session:
        if (
            session.query(EnergyCost).filter(EnergyCost.id == energy_cost_id).delete()
            > 0
        ):
            # success message
            session.commit()
            typer.echo(f"Energy Cost with id: {energy_cost_id} deleted successfully.")
        else:
            typer.echo(f"No Energy Cost found with id: {energy_cost_id}.")
