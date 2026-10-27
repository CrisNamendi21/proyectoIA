"""Router aislado sobre create_app de Cris, sin PostgreSQL ni Ollama reales."""

import secrets
import threading
from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api.generation import create_generation_router, get_ai_service
from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import get_db_session
from app.models import Grade, Subject, User
from app.services.ai.ai_service import AIPlanningService
from app.services.ai.errors import (
    GeneratedPlanValidationError,
    OllamaConnectionError,
    OllamaTimeoutError,
    OllamaUnexpectedResponseError,
)
from app.services.ai.ollama_client import OllamaClient
from test_ai_service import build_request, valid_generated_payload


TEST_PATH = "/__test/generation"


class UserLookup:
    def __init__(self):
        self.grade = Grade(id=1, name="Quinto grado")
        self.subject = Subject(id=2, name="Matemática")
        self.user = User(
            id=7, username="Docente", password_hash=hash_password("clave-ficticia"),
            is_active=True, profile_completed_at=datetime.now(timezone.utc),
        )
        self.user.grades = [self.grade]
        self.user.subjects = [self.subject]

    def scalar(self, statement):
        username = next(iter(statement.compile().params.values()))
        return self.user if username == self.user.username else None

    def get(self, model, user_id):
        records = {
            (User, self.user.id): self.user,
            (Grade, self.grade.id): self.grade,
            (Subject, self.subject.id): self.subject,
        }
        return records.get((model, user_id))


@pytest.fixture
def generation_client(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET_KEY", secrets.token_urlsafe(48))
    get_settings.cache_clear()
    from app.main import create_app

    app = create_app()
    assert TEST_PATH not in app.openapi()["paths"]
    app.include_router(create_generation_router(TEST_PATH))
    app.openapi_schema = None
    lookup = UserLookup()
    ollama = Mock(spec=OllamaClient)
    ollama.generate_json.return_value = valid_generated_payload()
    app.dependency_overrides[get_db_session] = lambda: lookup
    app.dependency_overrides[get_ai_service] = lambda: AIPlanningService(client=ollama)

    @app.get("/__test/event-loop")
    async def event_loop_thread():
        return threading.get_ident()

    try:
        with TestClient(app) as client:
            yield client, app, lookup, ollama
    finally:
        get_settings.cache_clear()


def authenticate(client):
    assert client.post(
        "/auth/login", json={"username": "Docente", "password": "clave-ficticia"}
    ).status_code == 200


def test_generation_uses_service_and_worker_thread(generation_client):
    client, _, _, ollama = generation_client
    authenticate(client)
    event_thread = client.get("/__test/event-loop").json()

    def generate_json(prompt, *, model):
        assert threading.get_ident() != event_thread
        assert "Fracciones equivalentes" in prompt
        assert model == "qwen2.5:3b"
        return valid_generated_payload()

    ollama.generate_json.side_effect = generate_json
    response = client.post(TEST_PATH, json=build_request().model_dump())
    assert response.status_code == 200
    assert response.json() == valid_generated_payload()
    ollama.generate_json.assert_called_once()


def test_conversational_generation_uses_profile_context(generation_client):
    client, _, _, ollama = generation_client
    authenticate(client)

    response = client.post(
        "/chat/generate",
        json={
            "grade_id": 1,
            "subject_id": 2,
            "message": "Quiero explicar fracciones con tarjetas.",
            "duration_minutes": 45,
            "history": [],
        },
    )

    assert response.status_code == 200
    assert response.json()["draft"] == valid_generated_payload()
    assert response.json()["quality_checks"][-1] == "Duración verificada: 45 minutos"
    prompt = ollama.generate_json.call_args.args[0]
    assert "Quiero explicar fracciones con tarjetas" in prompt


@pytest.mark.parametrize("state", ["absent", "tampered", "inactive", "deleted"])
def test_generation_rejects_unauthenticated_users(generation_client, state):
    client, _, lookup, ollama = generation_client
    if state != "absent":
        authenticate(client)
    if state == "tampered":
        client.cookies.clear()
        client.cookies.set("colegio_alfa_session", "firma-alterada")
    elif state == "inactive":
        lookup.user.is_active = False
    elif state == "deleted":
        lookup.user.id = 8
    assert client.post(TEST_PATH, json=build_request().model_dump()).status_code == 401
    ollama.generate_json.assert_not_called()


@pytest.mark.parametrize("body", [{}, {"context": {}}, {"context": {"duration_minutes": 0}}])
def test_generation_rejects_invalid_input(generation_client, body):
    client, _, _, ollama = generation_client
    authenticate(client)
    assert client.post(TEST_PATH, json=body).status_code == 422
    ollama.generate_json.assert_not_called()


@pytest.mark.parametrize(
    ("error", "status", "detail"),
    [
        (OllamaTimeoutError, 504, "Ollama excedió el tiempo de espera."),
        (OllamaConnectionError, 503, "Ollama no está disponible."),
        (OllamaUnexpectedResponseError, 502, "Ollama devolvió una propuesta inválida."),
        (GeneratedPlanValidationError, 502, "Ollama devolvió una propuesta inválida."),
    ],
)
def test_generation_translates_errors_without_leaking_details(generation_client, error, status, detail):
    client, _, _, ollama = generation_client
    authenticate(client)
    ollama.generate_json.side_effect = error("sensitive upstream details")
    response = client.post(TEST_PATH, json=build_request().model_dump())
    assert response.status_code == status
    assert response.json() == {"detail": detail}


def test_generation_rejects_invalid_generated_plan(generation_client):
    client, _, _, ollama = generation_client
    authenticate(client)
    ollama.generate_json.return_value = {"title": "Incomplete"}
    assert client.post(TEST_PATH, json=build_request().model_dump()).status_code == 502


def test_generation_invalid_configuration_returns_503(generation_client, monkeypatch):
    client, app, _, ollama = generation_client
    authenticate(client)
    del app.dependency_overrides[get_ai_service]
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "nan")
    response = client.post(TEST_PATH, json=build_request().model_dump())
    assert response.status_code == 503
    assert response.json() == {"detail": "Configuración de IA no disponible."}
    ollama.generate_json.assert_not_called()


def test_generation_documents_implemented_responses(generation_client):
    _, app, _, _ = generation_client
    responses = app.openapi()["paths"][TEST_PATH]["post"]["responses"]
    assert set(responses) == {"200", "401", "422", "502", "503", "504"}
