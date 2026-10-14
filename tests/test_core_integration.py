import secrets

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.db import init_db as init_db_module
from app.db.session import get_db_session


@pytest.fixture
def integrated_app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("SESSION_SECRET_KEY", secrets.token_urlsafe(48))
    get_settings.cache_clear()
    from app.main import create_app

    app = create_app()
    try:
        yield app
    finally:
        get_settings.cache_clear()


def test_main_registers_the_integrated_routes(integrated_app) -> None:
    paths = integrated_app.openapi()["paths"]

    assert {
        "/health",
        "/auth/login",
        "/auth/logout",
        "/auth/me",
        "/catalogs/grades",
        "/catalogs/subjects",
        "/catalogs/contents",
        "/generation",
        "/plans",
        "/plans/{plan_id}",
    } <= set(paths)


@pytest.mark.parametrize(
    ("method", "path"),
    [("get", "/auth/me"), ("post", "/generation"), ("get", "/plans")],
)
def test_sensitive_routes_reject_requests_without_a_session(
    integrated_app, method: str, path: str
) -> None:
    with TestClient(integrated_app) as client:
        response = client.request(method, path)

    assert response.status_code == 401
    assert response.json() == {"detail": "No autenticado."}


def test_database_errors_are_sanitized(integrated_app) -> None:
    def unavailable_database():
        raise SQLAlchemyError("host and credentials that must not be exposed")

    integrated_app.dependency_overrides[get_db_session] = unavailable_database
    try:
        with TestClient(integrated_app, raise_server_exceptions=False) as client:
            response = client.get("/catalogs/grades")
    finally:
        integrated_app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"detail": "Base de datos no disponible."}
    assert "credentials" not in response.text


def test_database_initialization_cli_hides_connection_details(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fail_initialization() -> None:
        raise SQLAlchemyError("postgresql://user:secret@private-host/database")

    monkeypatch.setattr(init_db_module, "init_db", fail_initialization)

    assert init_db_module.main() == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "No se pudo inicializar la base de datos.\n"
    assert "secret" not in captured.err
