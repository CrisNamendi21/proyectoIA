"""Flujo completo del domingo con una base PostgreSQL desechable."""

import os
import secrets
from types import SimpleNamespace
from typing import Annotated
from uuid import uuid4

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.security import verify_password
from app.db import seed_users
from app.db.base import Base
from app.models import User


@pytest.mark.skipif(
    os.getenv("COLEGIO_ALFA_TEST_POSTGRES") != "1",
    reason="Requiere COLEGIO_ALFA_TEST_POSTGRES=1 y PostgreSQL local",
)
def test_seed_login_rejection_and_later_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SESSION_SECRET_KEY", secrets.token_urlsafe(48))
    get_settings.cache_clear()
    source_url = make_url(get_settings().database_url)
    assert source_url.get_backend_name() == "postgresql"

    database_name = f"colegio_alfa_flow_test_{uuid4().hex}"
    database_url = source_url.set(database=database_name)
    admin_engine = create_engine(source_url, isolation_level="AUTOCOMMIT")
    test_engine = create_engine(database_url)
    try:
        with admin_engine.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{database_name}"'))
        Base.metadata.create_all(test_engine)

        monkeypatch.setattr("app.db.session.SessionLocal", sessionmaker(bind=test_engine))
        monkeypatch.setattr(seed_users.sys, "argv", ["seed_users", "docente_ficticio"])
        monkeypatch.setattr(seed_users.sys, "stdin", SimpleNamespace(isatty=lambda: True))
        monkeypatch.setattr(seed_users.getpass, "getpass", lambda _: "clave-ficticia")
        assert seed_users.main() == 0
        assert seed_users.main() == 0

        with Session(test_engine) as session:
            assert session.scalar(select(func.count()).select_from(User)) == 1
            user = session.scalar(select(User).where(User.username == "docente_ficticio"))
            assert user is not None
            assert user.password_hash.startswith("$argon2id$")
            assert "clave-ficticia" not in user.password_hash
            assert verify_password("clave-ficticia", user.password_hash)
            assert not verify_password("clave-incorrecta", user.password_hash)

        from app.main import create_app

        app = create_app()

        @app.get("/__test/identity")
        def identity(current_user: Annotated[User, Depends(get_current_user)]) -> dict[str, object]:
            return {"id": current_user.id, "username": current_user.username}

        with TestClient(app) as client:
            assert client.get("/__test/identity").status_code == 401

            login = client.post(
                "/auth/login",
                json={"username": "docente_ficticio", "password": "clave-ficticia"},
            )
            assert login.status_code == 200
            assert login.json() == {"id": user.id, "username": "docente_ficticio"}
            assert "password_hash" not in login.text
            assert "clave-ficticia" not in login.text
            assert client.get("/__test/identity").json() == login.json()

            rejected = client.post(
                "/auth/login",
                json={"username": "docente_ficticio", "password": "clave-incorrecta"},
            )
            assert rejected.status_code == 401
            assert rejected.json() == {"detail": "Credenciales inválidas."}
            assert client.get("/__test/identity").status_code == 401

            unknown = client.post(
                "/auth/login",
                json={"username": "desconocido", "password": "clave-ficticia"},
            )
            assert unknown.status_code == 401
            assert unknown.json() == rejected.json()

        with Session(test_engine) as session:
            assert session.scalar(select(func.count()).select_from(User)) == 1
            stored = session.get(User, user.id)
            assert stored is not None
            assert stored.password_hash == user.password_hash
    finally:
        test_engine.dispose()
        try:
            with admin_engine.connect() as connection:
                connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}" WITH (FORCE)'))
        finally:
            admin_engine.dispose()
            get_settings.cache_clear()
