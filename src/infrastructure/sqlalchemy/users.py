import secrets
from typing import List

from sqlalchemy.orm import Session, joinedload

from src.modules.users.models import Token, User


def get_user_by(db: Session, *filters) -> User:
    return db.query(User).filter(*filters).first()


# TODO -> Check sql num queries executed
def get_users_queryset(db: Session, join_list: List = None, *filters) -> List[User]:
    queryset = db.query(User).filter(*filters)
    if join_list:
        queryset = queryset.options(joinedload(*join_list))
    return queryset


def get_token_by(db: Session, *filters) -> Token:
    return db.query(Token).filter(*filters).first()


def delete_token(db: Session, *filters) -> None:
    db.query(Token).filter(*filters).delete()
    db.commit()


def get_or_create_token(db: Session, user: User) -> Token:
    token = get_token_by(db, Token.user_id == user.id)
    if token is None:
        token = Token(token=secrets.token_hex(), user_id=user.id)
        db.add(token)
        db.commit()
        db.refresh(token)
    return token


def create_user_db(db: Session, user: User) -> User:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
