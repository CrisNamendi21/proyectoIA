"""Comprobación opcional del cargador contra PostgreSQL real y aislado."""

import os
import subprocess
import sys
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.security import verify_password
from app.db.base import Base
from app.db import seed_users
from app.models import User


@pytest.mark.skipif(
    os.getenv("COLEGIO_ALFA_TEST_POSTGRES") != "1",
    reason="Requiere COLEGIO_ALFA_TEST_POSTGRES=1 y PostgreSQL local",
)
def test_seed_twice_preserves_active_and_inactive_accounts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Crea una BD desechable para no modificar las cuentas de desarrollo."""
    source_url = make_url(get_settings().database_url)
    assert source_url.get_backend_name() == "postgresql"

    database_name = f"colegio_alfa_seed_test_{uuid4().hex}"
    database_url = source_url.set(database=database_name)
    admin_engine = create_engine(source_url, isolation_level="AUTOCOMMIT")
    test_engine = create_engine(database_url)
    try:
        with admin_engine.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{database_name}"'))

        Base.metadata.create_all(test_engine)
        monkeypatch.setattr("app.db.session.SessionLocal", sessionmaker(bind=test_engine))
        monkeypatch.setattr(seed_users.sys, "argv", ["seed_users", "docente_activo_prueba"])
        monkeypatch.setattr(seed_users.sys, "stdin", SimpleNamespace(isatty=lambda: True))
        monkeypatch.setattr(
            seed_users.getpass, "getpass", lambda _: "clave-ficticia-segura"
        )
        with Session(test_engine) as session:
            session.add(
                User(
                    username="docente_inactivo_prueba",
                    password_hash="hash-previo",
                    is_active=False,
                )
            )
            session.commit()

            assert seed_users.main() == 0
            before = {
                user.username: (user.id, user.password_hash, user.is_active)
                for user in session.scalars(select(User).order_by(User.id))
            }
            assert len(before) == 2
            assert before["docente_activo_prueba"][2] is True
            assert before["docente_inactivo_prueba"][2] is False
            assert before["docente_activo_prueba"][1] != "clave-ficticia-segura"
            assert verify_password(
                "clave-ficticia-segura", before["docente_activo_prueba"][1]
            )

            assert seed_users.main() == 0
            assert not seed_users.create_user_if_missing(
                session, "docente_inactivo_prueba", "otra-clave-segura"
            )

            child_env = os.environ.copy()
            child_env["DATABASE_URL"] = database_url.render_as_string(hide_password=False)
            result = subprocess.run(
                [sys.executable, "-m", "app.db.seed_users", "docente_activo_prueba"],
                env=child_env,
                capture_output=True,
                text=True,
                check=False,
            )
            assert result.returncode == 0
            assert "ya existe" in result.stdout

            session.expire_all()
            after = {
                user.username: (user.id, user.password_hash, user.is_active)
                for user in session.scalars(select(User).order_by(User.id))
            }
            assert after == before
    finally:
        test_engine.dispose()
        try:
            with admin_engine.connect() as connection:
                connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}" WITH (FORCE)'))
        finally:
            admin_engine.dispose()


def test_initial_password_requires_fifteen_characters() -> None:
    with pytest.raises(ValueError, match="al menos 15 caracteres"):
        seed_users.validate_initial_password("corta")

    seed_users.validate_initial_password("123456789012345")
