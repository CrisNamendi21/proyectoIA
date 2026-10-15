from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware


@pytest.fixture
def plan_client(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+psycopg://test:test@127.0.0.1:1/plans_test"
    )
    from app.api.plans import get_planning_user, router
    from app.db.session import get_db_session
    from app.models import CurriculumContent, Grade, Subject, User

    db = MagicMock(spec=Session)
    records = {
        (Grade, 1): SimpleNamespace(id=1),
        (Grade, 2): SimpleNamespace(id=2),
        (Subject, 1): SimpleNamespace(id=1),
        (Subject, 2): SimpleNamespace(id=2),
        (CurriculumContent, 1): SimpleNamespace(id=1, grade_id=1, subject_id=1),
    }
    db.get.side_effect = lambda model, identifier: records.get((model, identifier))

    def flush():
        planning = db.add.call_args.args[0]
        planning.id = 10
        planning.created_at = planning.updated_at = datetime.now(timezone.utc)

    db.flush.side_effect = flush
    app = FastAPI()
    app.add_middleware(SessionMiddleware, secret_key="clave-ficticia-de-pruebas-32-caracteres")
    app.include_router(router)
    app.dependency_overrides[get_db_session] = lambda: db
    app.dependency_overrides[get_planning_user] = lambda: User(id=7, username="docente")
    with TestClient(app) as client:
        yield client, db, app
    app.dependency_overrides.clear()


@pytest.fixture
def plan():
    return SimpleNamespace(
        id=10, user_id=7, grade_id=None, subject_id=None, curriculum_content_id=None,
        content={"actividades": ["Leer", {"duracion": 20}], "extra": None},
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )


def where_sql(db):
    statement = db.scalars.call_args.args[0]
    return str(statement.whereclause.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    ))


@pytest.mark.parametrize("references", [
    {}, {"grade_id": 1, "subject_id": 1, "curriculum_content_id": 1},
    {"curriculum_content_id": 1},
])
def test_create_plan(plan_client, references):
    client, db, _ = plan_client
    content = {"texto": "Propuesta", "datos": [1, 1.5, True, None, {}]}
    response = client.post("/plans", json={"content": content, **references})
    assert response.status_code == 201
    assert response.json()["content"] == content
    assert response.json()["user_id"] == 7
    saved = db.add.call_args.args[0]
    assert saved.user_id == 7
    for name in ("grade_id", "subject_id", "curriculum_content_id"):
        assert getattr(saved, name) == references.get(name)
    assert [call[0] for call in db.mock_calls if call[0] in ("add", "flush", "commit")] == [
        "add", "flush", "commit"
    ]
    db.rollback.assert_not_called()


@pytest.mark.parametrize("content", [None, [], "{}", 1, True])
def test_reject_non_object_json(plan_client, content):
    client, db, _ = plan_client
    response = client.post("/plans", json={"content": content})
    assert response.status_code == 422
    db.add.assert_not_called()
    db.get.assert_not_called()


@pytest.mark.parametrize("content", [
    {"value": float("nan")}, {"value": float("inf")},
    {"value": datetime.now(timezone.utc)}, {1: "non-string-key"},
    {"value": (1, 2)}, {"value": {1, 2}},
])
def test_schema_rejects_non_json_python_values(content):
    from app.schemas.plans import PlanningCreate
    with pytest.raises(ValidationError):
        PlanningCreate(content=content)


@pytest.mark.parametrize("field", ["grade_id", "subject_id", "curriculum_content_id"])
@pytest.mark.parametrize("value", [0, -1, "1", True, 1.5])
def test_invalid_reference_ids(plan_client, field, value):
    client, db, _ = plan_client
    response = client.post("/plans", json={"content": {}, field: value})
    assert response.status_code == 422
    db.get.assert_not_called()
    db.add.assert_not_called()


def test_client_cannot_assign_owner(plan_client):
    client, db, _ = plan_client
    assert client.post("/plans", json={"content": {}, "user_id": 8}).status_code == 422
    db.add.assert_not_called()


@pytest.mark.parametrize("field", ["grade_id", "subject_id", "curriculum_content_id"])
def test_missing_reference(plan_client, field):
    client, db, _ = plan_client
    response = client.post("/plans", json={"content": {}, field: 99})
    assert response.status_code == 404
    db.rollback.assert_called_once_with()
    db.add.assert_not_called()
    db.commit.assert_not_called()


@pytest.mark.parametrize("field", ["grade_id", "subject_id"])
def test_incompatible_curriculum(plan_client, field):
    client, db, _ = plan_client
    response = client.post("/plans", json={"content": {}, "curriculum_content_id": 1, field: 2})
    assert response.status_code == 422
    db.rollback.assert_called_once_with()
    db.add.assert_not_called()


def test_empty_history(plan_client):
    client, db, _ = plan_client
    db.scalars.return_value.all.return_value = []
    response = client.get("/plans")
    assert response.status_code == 200
    assert response.json() == []
    assert where_sql(db) == "plannings.user_id = 7"


def test_history_filters_owner(plan_client, plan):
    client, db, _ = plan_client
    db.scalars.return_value.all.return_value = [plan]
    response = client.get("/plans")
    assert response.status_code == 200
    assert [row["id"] for row in response.json()] == [10]
    assert where_sql(db) == "plannings.user_id = 7"
    statement = db.scalars.call_args.args[0]
    assert str(statement.compile(dialect=postgresql.dialect())).endswith("ORDER BY plannings.id")
    db.commit.assert_not_called()


def test_get_existing_plan(plan_client, plan):
    client, db, _ = plan_client
    db.scalars.return_value.one_or_none.return_value = plan
    response = client.get("/plans/10")
    assert response.status_code == 200
    assert response.json()["id"] == 10
    assert where_sql(db) == "plannings.id = 10 AND plannings.user_id = 7"


@pytest.mark.parametrize("plan_id", [99, 10], ids=["missing", "other-owner"])
def test_missing_or_other_owner_plan(plan_client, plan_id):
    client, db, _ = plan_client
    # Simulate no row matching both predicates, including a plan owned by someone else.
    db.scalars.return_value.one_or_none.return_value = None
    response = client.get(f"/plans/{plan_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Planificación no encontrada"}
    assert where_sql(db) == f"plannings.id = {plan_id} AND plannings.user_id = 7"
    db.get.assert_not_called()


@pytest.mark.parametrize("plan_id", ["0", "-1", "abc"])
def test_invalid_path_id(plan_client, plan_id):
    client, db, _ = plan_client
    assert client.get(f"/plans/{plan_id}").status_code == 422
    db.scalars.assert_not_called()


@pytest.mark.parametrize("operation", ["get", "add", "flush", "commit"])
def test_transaction_failure(plan_client, operation):
    client, db, _ = plan_client
    getattr(db, operation).side_effect = SQLAlchemyError("internal database detail")
    response = client.post("/plans", json={"content": {}, "grade_id": 1})
    assert response.status_code == 500
    assert response.json() == {"detail": "No se pudo guardar la planificación"}
    db.rollback.assert_called_once_with()
    if operation != "commit":
        db.commit.assert_not_called()


@pytest.mark.parametrize("method, path", [("post", "/plans"), ("get", "/plans"), ("get", "/plans/10")])
def test_routes_require_authentication(plan_client, method, path):
    from app.api.plans import get_planning_user
    client, db, app = plan_client
    del app.dependency_overrides[get_planning_user]
    kwargs = {"json": {"content": {}}} if method == "post" else {}
    response = client.request(method, path, headers={"X-User-Id": "7"}, params={"user_id": 7}, **kwargs)
    assert response.status_code == 401
    db.get.assert_not_called()
    db.scalars.assert_not_called()
    db.add.assert_not_called()


@pytest.fixture
def update_client(plan_client, plan):
    client, db, app = plan_client
    db.scalars.return_value.one_or_none.return_value = plan
    db.flush.side_effect = None
    return client, db, app, plan


def test_update_owner_replaces_content_and_preserves_identity(update_client):
    client, db, _, plan = update_client
    original = (plan.id, plan.user_id, plan.created_at)
    old_content = plan.content
    response = client.patch("/plans/10", json={"content": {"nuevo": [1, None]}})
    assert response.status_code == 200
    assert response.json()["content"] == {"nuevo": [1, None]}
    assert old_content == {"actividades": ["Leer", {"duracion": 20}], "extra": None}
    assert (plan.id, plan.user_id, plan.created_at) == original
    assert where_sql(db) == "plannings.id = 10 AND plannings.user_id = 7"
    db.flush.assert_called_once_with()
    db.commit.assert_called_once_with()
    db.rollback.assert_not_called()
    db.add.assert_not_called()


@pytest.mark.parametrize("plan_id", [10, 99], ids=["other-owner", "missing"])
def test_update_missing_or_other_owner(update_client, plan_id):
    client, db, _, plan = update_client
    original = plan.content.copy()
    db.scalars.return_value.one_or_none.return_value = None
    response = client.patch(f"/plans/{plan_id}", json={"content": {"changed": True}})
    assert response.status_code == 404
    assert response.json() == {"detail": "Planificación no encontrada"}
    assert where_sql(db) == f"plannings.id = {plan_id} AND plannings.user_id = 7"
    assert plan.content == original
    db.get.assert_not_called()
    db.flush.assert_not_called()
    db.commit.assert_not_called()


def test_update_partial_keeps_omitted_fields(update_client):
    client, _, _, plan = update_client
    content = plan.content.copy()
    plan.subject_id = 1
    response = client.patch("/plans/10", json={"grade_id": 1})
    assert response.status_code == 200
    assert response.json()["grade_id"] == 1
    assert response.json()["subject_id"] == 1
    assert response.json()["content"] == content


@pytest.mark.parametrize("field", ["grade_id", "subject_id", "curriculum_content_id"])
def test_update_clears_optional_reference(update_client, field):
    client, _, _, plan = update_client
    plan.grade_id = plan.subject_id = plan.curriculum_content_id = 1
    response = client.patch("/plans/10", json={field: None})
    assert response.status_code == 200
    for name in ("grade_id", "subject_id", "curriculum_content_id"):
        assert response.json()[name] == (None if name == field else 1)


@pytest.mark.parametrize("body", [
    {}, {"user_id": 8}, {"id": 20}, {"created_at": "2026-10-14"},
    {"updated_at": "2026-10-14"}, {"unknown": 1},
    {"content": {}, "user_id": 8},
    *({"content": value} for value in (None, [], "{}", 1, True)),
    *({field: value} for field in ("grade_id", "subject_id", "curriculum_content_id")
      for value in (0, -1, "1", True, 1.5)),
])
def test_update_rejects_invalid_body(update_client, body):
    client, db, _, _ = update_client
    assert client.patch("/plans/10", json=body).status_code == 422
    db.scalars.assert_not_called()
    db.flush.assert_not_called()
    db.commit.assert_not_called()


@pytest.mark.parametrize("value", [float("nan"), float("inf"), (1, 2), {1, 2}, datetime.now(timezone.utc)])
def test_update_schema_rejects_non_json_values(value):
    from app.schemas.plans import PlanningUpdate
    with pytest.raises(ValidationError):
        PlanningUpdate(content={"value": value})


def test_update_rejects_malformed_json(update_client):
    client, db, _, _ = update_client
    assert client.patch("/plans/10", content='{"content":', headers={"Content-Type": "application/json"}).status_code == 422
    db.scalars.assert_not_called()


@pytest.mark.parametrize("body,previous", [
    ({"grade_id": 2}, {"curriculum_content_id": 1}),
    ({"subject_id": 2}, {"curriculum_content_id": 1}),
    ({"curriculum_content_id": 1}, {"grade_id": 2}),
    ({"curriculum_content_id": 1}, {"subject_id": 2}),
])
def test_update_validates_combined_curriculum(update_client, body, previous):
    client, db, _, plan = update_client
    for field, value in previous.items():
        setattr(plan, field, value)
    original = vars(plan).copy()
    assert client.patch("/plans/10", json=body).status_code == 422
    assert vars(plan) == original
    db.rollback.assert_called_once_with()
    db.flush.assert_not_called()
    db.commit.assert_not_called()


@pytest.mark.parametrize("field", ["grade_id", "subject_id", "curriculum_content_id"])
def test_update_rejects_missing_reference(update_client, field):
    client, db, _, _ = update_client
    assert client.patch("/plans/10", json={field: 99}).status_code == 404
    db.rollback.assert_called_once_with()
    db.flush.assert_not_called()
    db.commit.assert_not_called()


@pytest.mark.parametrize("operation", ["scalars", "get", "flush", "commit"])
def test_update_storage_failure_rolls_back(update_client, operation):
    client, db, _, _ = update_client
    getattr(db, operation).side_effect = SQLAlchemyError("private database details")
    response = client.patch("/plans/10", json={"grade_id": 1})
    assert response.status_code == 500
    assert response.json() == {"detail": "No se pudo actualizar la planificación"}
    db.rollback.assert_called_once_with()
    if operation != "commit":
        db.commit.assert_not_called()


@pytest.mark.parametrize("state", ["absent", "inactive"])
def test_update_requires_active_authenticated_user(update_client, state):
    import base64
    import json
    from itsdangerous import TimestampSigner
    from app.api.plans import get_planning_user
    from app.models import User

    client, db, app, _ = update_client
    del app.dependency_overrides[get_planning_user]
    if state == "inactive":
        payload = base64.b64encode(json.dumps({"user_id": 7}).encode())
        cookie = TimestampSigner("clave-ficticia-de-pruebas-32-caracteres").sign(payload).decode()
        client.cookies.set("session", cookie)
        db.get.side_effect = lambda model, identifier: User(id=7, username="docente", is_active=False)
    response = client.patch("/plans/10", json={"content": {}}, headers={"X-User-Id": "7"})
    assert response.status_code == 401
    if state == "inactive":
        db.get.assert_called_once_with(User, 7)
    else:
        db.get.assert_not_called()
    db.scalars.assert_not_called()
    db.flush.assert_not_called()
    db.commit.assert_not_called()


@pytest.mark.parametrize("plan_id", ["0", "-1", "abc"])
def test_update_invalid_path(update_client, plan_id):
    client, db, _, _ = update_client
    assert client.patch(f"/plans/{plan_id}", json={"content": {}}).status_code == 422
    db.scalars.assert_not_called()


def test_update_preserves_complete_teaching_draft(update_client):
    from app.services.ai.schemas import TeachingPlanDraft
    client, _, _, _ = update_client
    draft = TeachingPlanDraft(
        title="Fracciones", grade="Quinto", subject="Matemática",
        curriculum_content="Fracciones", learning_objective="Comparar fracciones",
        activities=[{"stage": stage, "description": "Comparar dibujos", "minutes": 15,
                     "resources": ["tarjetas"]} for stage in ("inicio", "desarrollo", "cierre")],
        assessment={"criteria": ["Compara fracciones"], "evidence": "Ejercicios"},
        materials=["pizarra"], teacher_notes=["Revisado"],
    ).model_dump(mode="json")
    assert client.patch("/plans/10", json={"content": draft}).json()["content"] == draft


def test_update_schema_distinguishes_omission_and_null():
    from app.schemas.plans import PlanningUpdate
    assert PlanningUpdate(grade_id=None).model_dump(exclude_unset=True) == {"grade_id": None}
    assert PlanningUpdate(content={}).model_dump(exclude_unset=True) == {"content": {}}
