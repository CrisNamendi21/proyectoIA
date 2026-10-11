import base64
import json
import os
import secrets
from collections.abc import Iterator
from typing import Annotated
from uuid import uuid4

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import Select, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db_session
from app.models import User


class UserLookup:
    def __init__(self, user: User) -> None:
        self.user = user
        self.requests = 0

    def scalar(self, statement: Select[tuple[User]]) -> User | None:
        username = next(iter(statement.compile().params.values()))
        return self.user if username == self.user.username else None

    def get(self, model: type[User], user_id: int) -> User | None:
        assert model is User
        return self.user if user_id == self.user.id else None


def test_session_recovers_identity_and_rejects_invalid_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SESSION_SECRET_KEY", secrets.token_urlsafe(48))
    get_settings.cache_clear()
    from app.main import create_app

    app = create_app()
    user = User(
        id=7,
        username="Docente",
        password_hash=hash_password("clave-ficticia"),
        is_active=True,
    )
    lookup = UserLookup(user)

    def session_override() -> UserLookup:
        lookup.requests += 1
        return lookup

    app.dependency_overrides[get_db_session] = session_override

    @app.get("/__test/identity")
    def identity(current_user: Annotated[User, Depends(get_current_user)]) -> dict[str, object]:
        return {"id": current_user.id, "username": current_user.username}

    with TestClient(app) as client:
        assert client.get("/__test/identity").status_code == 401

        login = client.post(
            "/auth/login",
            json={"username": "Docente", "password": "clave-ficticia"},
        )
        assert login.status_code == 200
        assert login.json() == {"id": 7, "username": "Docente"}
        cookie = client.cookies.get("colegio_alfa_session")
        assert cookie is not None
        session_data = json.loads(base64.b64decode(cookie.split(".")[0]))
        assert session_data == {"user_id": 7}
        set_cookie = login.headers["set-cookie"].lower()
        assert "httponly" in set_cookie
        assert "samesite=lax" in set_cookie
        assert "max-age=28800" in set_cookie

        assert client.get("/__test/identity").json() == {"id": 7, "username": "Docente"}
        assert lookup.requests == 3

        client.cookies.set("colegio_alfa_session", "firma-alterada")
        assert client.get("/__test/identity").status_code == 401

        client.cookies.clear()
        assert client.get("/__test/identity").status_code == 401

        assert client.post(
            "/auth/login",
            json={"username": "Docente", "password": "clave-ficticia"},
        ).status_code == 200
        assert client.post(
            "/auth/login",
            json={"username": "Docente", "password": "clave-equivocada"},
        ).status_code == 401
        assert client.get("/__test/identity").status_code == 401

        assert client.post(
            "/auth/login",
            json={"username": "Docente", "password": "clave-ficticia"},
        ).status_code == 200
        user.is_active = False
        assert client.get("/__test/identity").status_code == 401

    get_settings.cache_clear()


@pytest.mark.skipif(
    os.getenv("COLEGIO_ALFA_TEST_POSTGRES") != "1",
    reason="Requiere COLEGIO_ALFA_TEST_POSTGRES=1 y PostgreSQL local",
)
def test_login_and_next_request_with_postgresql(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SESSION_SECRET_KEY", secrets.token_urlsafe(48))
    get_settings.cache_clear()
    source_url = make_url(get_settings().database_url)
    assert source_url.get_backend_name() == "postgresql"
    database_name = f"colegio_alfa_auth_test_{uuid4().hex}"
    database_url = source_url.set(database=database_name)
    admin_engine = create_engine(source_url, isolation_level="AUTOCOMMIT")
    test_engine = create_engine(database_url)
    try:
        with admin_engine.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{database_name}"'))
        Base.metadata.create_all(test_engine)
        with Session(test_engine) as session:
            session.add(
                User(
                    username="docente_prueba",
                    password_hash=hash_password("clave-ficticia"),
                    is_active=True,
                )
            )
            session.commit()

        from app.main import create_app

        app = create_app()

        def session_override() -> Iterator[Session]:
            with Session(test_engine) as session:
                yield session

        app.dependency_overrides[get_db_session] = session_override

        @app.get("/__test/identity")
        def identity(current_user: Annotated[User, Depends(get_current_user)]) -> dict[str, object]:
            return {"id": current_user.id, "username": current_user.username}

        with TestClient(app) as client:
            assert client.get("/__test/identity").status_code == 401
            login = client.post(
                "/auth/login",
                json={"username": "docente_prueba", "password": "clave-ficticia"},
            )
            assert login.status_code == 200
            assert login.json()["username"] == "docente_prueba"
            assert client.get("/__test/identity").json() == login.json()
            client.cookies.clear()
            assert client.get("/__test/identity").status_code == 401
    finally:
        test_engine.dispose()
        try:
            with admin_engine.connect() as connection:
                connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}" WITH (FORCE)'))
        finally:
            admin_engine.dispose()
            get_settings.cache_clear()
