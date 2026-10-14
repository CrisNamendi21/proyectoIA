"""Flujo HTTP real con PostgreSQL; contrato pedagógico todavía provisional.

Se ejecuta sobre el snapshot de Cris mediante run_snapshot.py. El checkout antiguo
de Jean puede no incluir planes, por lo que la activación es explícita.
"""

import json
import os
import socket
import time
import urllib.error
import urllib.request

import pytest

if os.getenv("COLEGIO_ALFA_TEST_AI_FLOW") != "1":
    pytest.skip("Requiere el runner aislado y PostgreSQL desechable", allow_module_level=True)

from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models import Planning, User
from app.schemas.plans import PlanningCreate
from app.services.ai.schemas import TeachingPlanDraft


def generation_request():
    return {"context": {
        "grade": "Quinto grado", "subject": "Matemática",
        "curriculum_content": "Fracciones equivalentes", "duration_minutes": 45,
        "learning_goal": "Reconocer fracciones equivalentes.",
        "resources": ["pizarra", "tarjetas"],
    }, "model": "qwen2.5:3b"}


def draft_payload():
    return {
        "title": "Fracciones equivalentes", "grade": "Quinto grado",
        "subject": "Matemática", "curriculum_content": "Fracciones equivalentes",
        "learning_objective": "Reconocer fracciones equivalentes mediante dibujos.",
        "activities": [
            {"stage": "inicio", "description": "Comparar dibujos.", "minutes": 10, "resources": ["pizarra"]},
            {"stage": "desarrollo", "description": "Clasificar tarjetas.", "minutes": 25, "resources": ["tarjetas"]},
            {"stage": "cierre", "description": "Explicar equivalencias.", "minutes": 10, "resources": []},
        ],
        "assessment": {"criteria": ["Reconoce equivalencias"], "evidence": "Explicación oral."},
        "materials": ["pizarra", "tarjetas"], "teacher_notes": [],
    }


def login(client, username="docente_a_ficticio"):
    response = client.post("/auth/login", json={
        "username": username, "password": "clave-ficticia-integracion",
    })
    assert response.status_code == 200
    assert "password_hash" not in response.text
    return response.json()


def planning_body(env, draft=None):
    return PlanningCreate(
        grade_id=env.grade_id, subject_id=env.subject_id,
        curriculum_content_id=env.content_id,
        content=draft or draft_payload(),
    ).model_dump(mode="json")


def plan_count(env):
    with Session(env.engine) as session:
        return session.scalar(select(func.count()).select_from(Planning))


@pytest.fixture
def ollama_transport(monkeypatch):
    state = {"calls": [], "body": json.dumps({"response": json.dumps(draft_payload())}), "error": None}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return state["body"].encode("utf-8")

    def urlopen(request, timeout):
        assert request.full_url.endswith("/api/generate")
        state["calls"].append(json.loads(request.data))
        if state["error"] is not None:
            raise state["error"]
        return Response()

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    return state


def exercise_persisted_flow(env):
    with TestClient(env.app) as first, TestClient(env.app) as second:
        assert login(first)["id"] == env.teacher_id
        assert first.get("/auth/me").json() == {"id": env.teacher_id, "username": "docente_a_ficticio"}
        for route, identifier in (("grades", env.grade_id), ("subjects", env.subject_id)):
            response = first.get(f"/catalogs/{route}")
            assert response.status_code == 200
            assert identifier in [row["id"] for row in response.json()]
        contents = first.get("/catalogs/contents", params={
            "grade_id": env.grade_id, "subject_id": env.subject_id,
        })
        assert contents.status_code == 200
        assert contents.json() == [{
            "id": env.content_id, "grade_id": env.grade_id,
            "subject_id": env.subject_id, "description": "Fracciones equivalentes",
        }]
        assert plan_count(env) == 0
        generated = first.post("/generation", json=generation_request())
        assert generated.status_code == 200
        draft = TeachingPlanDraft.model_validate(generated.json())
        assert plan_count(env) == 0, "Generación no debe persistir por sí sola"
        # Simula revisión previa al guardado, sin afirmar validación pedagógica humana.
        draft.teacher_notes.append("Revisión simulada: usar tarjetas de apoyo.")
        draft.activities[0].description = "Comparar dibujos con apoyo de tarjetas."
        reviewed = TeachingPlanDraft.model_validate(draft.model_dump(mode="json"))
        body = planning_body(env, reviewed.model_dump(mode="json"))
        saved = first.post("/plans", json=body)
        assert saved.status_code == 201
        data = saved.json()
        plan_id = data["id"]
        assert data["user_id"] == env.teacher_id
        assert data["content"] == body["content"]
        assert data["grade_id"] == env.grade_id and data["curriculum_content_id"] == env.content_id
        assert data["created_at"] and data["updated_at"]
        # Fuerza otra conexión física: comprueba commit/JSONB más allá del response HTTP.
        env.engine.dispose()
        with Session(env.engine) as session:
            persisted = session.get(Planning, plan_id)
            assert persisted.content == body["content"]
            assert persisted.user_id == env.teacher_id
            assert session.scalar(text("SELECT pg_typeof(content)::text FROM plannings WHERE id=:id"), {"id": plan_id}) == "jsonb"
        assert first.get("/plans").json() == [data]
        assert first.get(f"/plans/{plan_id}").json() == data
        assert login(second, "docente_b_ficticio")["id"] == env.second_teacher_id
        assert second.get("/plans").json() == []
        assert second.get(f"/plans/{plan_id}").status_code == 404
        spoof = second.post("/plans", json={**body, "user_id": env.teacher_id})
        assert spoof.status_code == 422
        own = second.post("/plans", json=body)
        assert own.status_code == 201 and own.json()["user_id"] == env.second_teacher_id
        assert first.get(f"/plans/{own.json()['id']}").status_code == 404
        assert [row["id"] for row in first.get("/plans").json()] == [plan_id]
        assert first.post("/auth/logout").status_code == 204
        assert first.cookies.get("colegio_alfa_session") is None
        assert first.get("/auth/me").status_code == 401
        assert first.get("/plans").status_code == 401
        assert first.post("/plans", json=body).status_code == 401
        assert first.post("/generation", json=generation_request()).status_code == 401
        assert plan_count(env) == 2


def test_mock_ollama_persisted_flow(flow_environment, ollama_transport):
    exercise_persisted_flow(flow_environment)
    assert len(ollama_transport["calls"]) == 1
    payload = ollama_transport["calls"][0]
    assert payload["model"] == "qwen2.5:3b" and payload["format"] == "json"
    assert "Fracciones equivalentes" in payload["prompt"]


@pytest.mark.skipif(os.getenv("COLEGIO_ALFA_TEST_REAL_OLLAMA") != "1", reason="Inferencia real opcional, una ejecución explícita")
def test_real_ollama_persisted_flow(flow_environment):
    started = time.perf_counter()
    exercise_persisted_flow(flow_environment)
    print(json.dumps({"real_ollama_flow": "passed", "seconds": round(time.perf_counter() - started, 2)}))


@pytest.mark.parametrize(("method", "path"), [
    ("get", "/auth/me"), ("get", "/plans"), ("get", "/plans/1"),
    ("post", "/plans"), ("post", "/generation"),
])
def test_sensitive_routes_require_session(flow_environment, ollama_transport, method, path):
    env = flow_environment
    with TestClient(env.app) as client:
        body = generation_request() if path == "/generation" else planning_body(env)
        response = client.request(method, path, json=body if method == "post" else None)
        assert response.status_code == 401 and response.json() == {"detail": "No autenticado."}
    assert not ollama_transport["calls"] and plan_count(env) == 0


@pytest.mark.parametrize("username", ["desconocido_ficticio", "docente_inactivo_ficticio"])
def test_login_rejects_unknown_or_inactive(flow_environment, username):
    with TestClient(flow_environment.app) as client:
        response = client.post("/auth/login", json={"username": username, "password": "clave-ficticia-integracion"})
        assert response.status_code == 401 and response.json() == {"detail": "Credenciales inválidas."}


def test_invalid_password_and_session_clear(flow_environment):
    with TestClient(flow_environment.app) as client:
        login(client)
        response = client.post("/auth/login", json={"username": "docente_a_ficticio", "password": "incorrecta"})
        assert response.status_code == 401
        assert client.get("/auth/me").status_code == 401


def test_user_deactivation_is_checked_against_postgres(flow_environment, ollama_transport):
    env = flow_environment
    with TestClient(env.app) as client:
        login(client)
        with Session(env.engine) as session:
            session.get(User, env.teacher_id).is_active = False
            session.commit()
        assert client.post("/generation", json=generation_request()).status_code == 401
        assert client.get("/plans").status_code == 401
    assert not ollama_transport["calls"]


@pytest.mark.parametrize(("patch", "status"), [
    ({"grade_id": 999999}, 404), ({"subject_id": 999999}, 404),
    ({"curriculum_content_id": 999999}, 404), ({"grade_id": "other"}, 422),
    ({"subject_id": "other"}, 422), ({"grade_id": True}, 422),
    ({"user_id": 999999}, 422), ({"content": []}, 422),
])
def test_invalid_planning_does_not_persist(flow_environment, patch, status):
    env = flow_environment
    patch = dict(patch)
    for key, value in list(patch.items()):
        if value == "other":
            patch[key] = env.other_grade_id if key == "grade_id" else env.other_subject_id
    with TestClient(env.app) as client:
        login(client)
        assert client.post("/plans", json={**planning_body(env), **patch}).status_code == status
        assert plan_count(env) == 0
        assert client.post("/plans", json=planning_body(env)).status_code == 201


@pytest.mark.parametrize(("failure", "status"), [
    ("timeout", 504), ("unavailable", 503), ("invalid_json", 502), ("invalid_plan", 502),
])
def test_ollama_failures_do_not_persist(flow_environment, ollama_transport, failure, status):
    if failure == "timeout":
        ollama_transport["error"] = socket.timeout()
    elif failure == "unavailable":
        ollama_transport["error"] = urllib.error.URLError(ConnectionRefusedError())
    elif failure == "invalid_json":
        ollama_transport["body"] = "not-json"
    else:
        ollama_transport["body"] = json.dumps({"response": "{}"})
    with TestClient(flow_environment.app) as client:
        login(client)
        response = client.post("/generation", json=generation_request())
        assert response.status_code == status
    assert plan_count(flow_environment) == 0


def test_invalid_generation_and_catalog_filters(flow_environment, ollama_transport):
    with TestClient(flow_environment.app) as client:
        login(client)
        assert client.post("/generation", json={"context": {}}).status_code == 422
        assert client.get("/catalogs/contents", params={"grade_id": 0}).status_code == 422
        assert client.get("/catalogs/contents", params={"grade_id": 999999}).status_code == 404
    assert not ollama_transport["calls"] and plan_count(flow_environment) == 0


def test_postgres_storage_failure_rolls_back_and_next_request_works(flow_environment):
    env = flow_environment
    with env.engine.begin() as connection:
        connection.execute(text("ALTER TABLE plannings ADD CONSTRAINT ai_flow_test_storage_failure CHECK (NOT (content ? 'force_storage_error'))"))
    with TestClient(env.app) as client:
        login(client)
        response = client.post("/plans", json={"content": {"force_storage_error": True}})
        assert response.status_code == 500
        assert response.json() == {"detail": "No se pudo guardar la planificación"}
        assert plan_count(env) == 0
        assert client.post("/plans", json=planning_body(env)).status_code == 201
        assert plan_count(env) == 1


def test_database_unavailable_http_is_sanitized(flow_environment):
    def unavailable():
        raise SQLAlchemyError("private connection details")

    flow_environment.app.dependency_overrides[get_db_session] = unavailable
    with TestClient(flow_environment.app, raise_server_exceptions=False) as client:
        response = client.get("/catalogs/grades")
        assert response.status_code == 503
        assert response.json() == {"detail": "Base de datos no disponible."}


def test_catalogs_currently_allow_anonymous_reading(flow_environment):
    # Observación de la implementación actual; no aprueba una política de acceso.
    with TestClient(flow_environment.app) as client:
        assert client.get("/catalogs/grades").status_code == 200


def test_logout_does_not_revoke_a_previously_copied_cookie(flow_environment):
    # Límite ya documentado de SessionMiddleware: pendiente de decisión del equipo.
    with TestClient(flow_environment.app) as client:
        login(client)
        saved_cookie = client.cookies.get("colegio_alfa_session")
        assert client.post("/auth/logout").status_code == 204
        assert client.get("/auth/me").status_code == 401
        with TestClient(flow_environment.app) as replay:
            replay.cookies.set("colegio_alfa_session", saved_cookie)
            assert replay.get("/auth/me").status_code == 200
