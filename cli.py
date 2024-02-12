import typer

from commands import default_energy_costs, marketers, rate_type, rates, token, user

app = typer.Typer(help="Awesome CLI command manager.")


if __name__ == "__main__":
    # add sub-commands
    app.add_typer(user.app, name="user")
    app.add_typer(token.app, name="token")
    app.add_typer(rate_type.app, name="rate_type")
    app.add_typer(marketers.app, name="marketer")
    app.add_typer(rates.app, name="rate")
    app.add_typer(default_energy_costs.app, name="default_energy_costs")
    app()
