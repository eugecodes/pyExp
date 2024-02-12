import typer

from src.infrastructure.sqlalchemy.database import get_db
from src.modules.users.models import Token

app = typer.Typer(help="Token manager commands")


@app.command(help="Show token of all user", name="show-all")
def show_token():
    db = list(get_db())[0]
    tokens = db.query(Token).all()
    for token in tokens:
        typer.echo(f"Token:{token.user.user_email} {token.user_id} {token.token}")
