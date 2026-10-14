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
