import typer
from sqlalchemy.orm import sessionmaker

from src.infrastructure.sqlalchemy.database import engine
from src.modules.users.models import User
from src.services.users import generate_password_hash

app = typer.Typer(help="Create new users.")


@app.command(help="Create a new user.", name="create")
def create_user(email: str, password: str, is_superadmin: bool = True):
    """
    Example: docker compose -f local.yml run --rm fastapi python cli.py user create user@Test.com password
    """
    with sessionmaker(autocommit=False, autoflush=True, bind=engine)() as session:
        password_hashed = generate_password_hash(password)
        print(password_hashed)
        user = User(
            first_name="admin",
            last_name="lastname",
            email=email,
            hashed_password=password_hashed,
            is_superadmin=is_superadmin,
            is_active=True,
            is_deleted=False,
            role="super_admin"
        )
        session.add(user)
        session.commit()
        # success message
    typer.echo(f"User {email} created successfully.")


@app.command(help="Show all users.", name="show-all")
def show_users():
    with sessionmaker(autocommit=False, autoflush=True, bind=engine)() as session:
        users = session.query(User).all()
        # success message
        for user in users:
            typer.echo(
                f"User: {user.id=} {user.email=} {user.is_superadmin=} {user.is_active=} "
                f"{user.is_deleted=} {user.hashed_password=}"
            )
