from collections.abc import Iterator
import secrets

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Select
from starlette.middleware.sessions import SessionMiddleware

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

    def get(self, model: type[User], user_id: int) -> User | None:
        assert model is User
        return next((user for user in self.users.values() if user.id == user_id), None)


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
    app.add_middleware(SessionMiddleware, secret_key=secrets.token_urlsafe(32))
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
    assert "colegio_alfa_session" not in response.text


def test_me_and_logout_complete_the_session_flow(
    login_client: tuple[TestClient, UserLookup],
) -> None:
    client, _ = login_client

    assert client.get("/auth/me").status_code == 401
    login = client.post(
        "/auth/login", json={"username": "Docente", "password": "clave-ficticia"}
    )
    assert login.status_code == 200
    assert client.get("/auth/me").json() == {"id": 7, "username": "Docente"}

    logout = client.post("/auth/logout")
    assert logout.status_code == 204
    assert logout.content == b""
    deleted_cookie = logout.headers["set-cookie"].lower()
    assert "expires=thu, 01 jan 1970" in deleted_cookie
    assert client.get("/auth/me").status_code == 401


def test_logout_is_idempotent_without_a_session(
    login_client: tuple[TestClient, UserLookup],
) -> None:
    client, _ = login_client

    assert client.post("/auth/logout").status_code == 204
    assert client.get("/auth/me").status_code == 401


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
