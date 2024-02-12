import csv
from functools import reduce
from tempfile import NamedTemporaryFile
from typing import Any, List

from fastapi import Depends, HTTPException, Request, status
from fastapi.security.utils import get_authorization_scheme_param
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Query, Session

from src.infrastructure.sqlalchemy.database import get_db
from src.infrastructure.sqlalchemy.users import get_user_by
from src.modules.rates.models import ClientType
from src.modules.users.models import Token, User


async def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    authorization = request.headers.get("Authorization")
    scheme, token = get_authorization_scheme_param(authorization)
    if not authorization or scheme != "token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="not_authenticated",
            headers={"WWW-Authenticate": "token"},
        )

    user = get_user_by(db, User.token.has(Token.token == token))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_credentials",
            headers={"WWW-Authenticate": "token"},
        )
    return user


def update_from_dict(obj: Any, update_request: dict) -> Any:
    for key, value in update_request.items():
        setattr(obj, key, value)
    return obj


def order_client_types(client_types: List[ClientType]) -> List[ClientType]:
    client_types.sort()
    return client_types


def empty_string_to_none(value: str) -> str | None:
    return value or None


def recursive_getattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)

    return reduce(_getattr, [obj] + attr.split("."))


def generate_csv_file(filename: str, headers: dict, data: list):
    with NamedTemporaryFile(
        "w", suffix=".csv", prefix=filename, delete=False
    ) as outfile:
        writer = csv.writer(outfile, delimiter=";")
        writer.writerow(headers.values())
        for instance in data:
            row = []
            for attribute in headers.keys():
                try:
                    field = recursive_getattr(instance, attribute)
                except AttributeError:
                    try:
                        related_field, field = attribute.split(":")
                    except ValueError:  # related field None
                        row.append("")
                        continue
                    related_objects = recursive_getattr(instance, related_field)
                    row.append(
                        "|".join(
                            [
                                recursive_getattr(related_obj, field)
                                for related_obj in related_objects
                            ]
                        )
                    )
                    continue
                if type(field) is list:
                    row.append("|".join(field))
                    continue
                row.append(field)
            writer.writerow(row)
        return outfile.name


def paginate_queryset_with_n_to_many(qs: Query, params: Params) -> Any:
    paginated_response = paginate(qs, params)
    paginated_response.total = len(qs.all())
    return paginated_response
