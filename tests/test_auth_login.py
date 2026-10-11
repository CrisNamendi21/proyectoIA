from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Select

from app.api.auth import router
from app.core.security import hash_password
from app.db.session import get_db_session
from app.models import User


class UserLookup:
    def __init__(self, users: dict[str, User]) -> None:
        self.users = users
        self.last_username: str | None = None

    def scalar(self, statement: Select[tuple[User]]) -> User | None:
        parameters = statement.compile().params
        self.last_username = next(iter(parameters.values()))
        return self.users.get(self.last_username)


@pytest.fixture
def login_client() -> Iterator[tuple[TestClient, UserLookup]]:
    password_hash = hash_password("clave-ficticia")
    lookup = UserLookup(
        {
            "Docente": User(
                id=7,
                username="Docente",
                password_hash=password_hash,
                is_active=True,
            ),
            "Inactivo": User(
                id=8,
                username="Inactivo",
                password_hash=password_hash,
                is_active=False,
            ),
        }
    )
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db_session] = lambda: lookup
    with TestClient(app) as client:
        yield client, lookup


def test_login_returns_only_public_identity(login_client: tuple[TestClient, UserLookup]) -> None:
    client, lookup = login_client
    response = client.post(
        "/auth/login", json={"username": "  Docente  ", "password": "clave-ficticia"}
    )

    assert response.status_code == 200
    assert response.json() == {"id": 7, "username": "Docente"}
    assert lookup.last_username == "Docente"
    assert "password_hash" not in response.text
    assert "clave-ficticia" not in response.text


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("Docente", "clave-equivocada"),
        ("docente", "clave-ficticia"),
        ("Desconocido", "clave-ficticia"),
        ("Inactivo", "clave-ficticia"),
    ],
)
def test_login_rejects_invalid_or_inactive_accounts(
    login_client: tuple[TestClient, UserLookup], username: str, password: str
) -> None:
    client, _ = login_client
    response = client.post(
        "/auth/login", json={"username": username, "password": password}
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Credenciales inválidas."}


@pytest.mark.parametrize(
    "body",
    [
        {"username": " ", "password": "clave-ficticia"},
        {"username": "Docente", "password": ""},
        {"username": "Docente"},
    ],
)
def test_login_rejects_invalid_request_body(
    login_client: tuple[TestClient, UserLookup], body: dict[str, str]
) -> None:
    client, _ = login_client
    assert client.post("/auth/login", json=body).status_code == 422
