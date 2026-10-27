from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.profile import router
from app.db.session import get_db_session
from app.models import Grade, Subject, User


@pytest.fixture
def profile_client():
    user = User(id=7, username="Docente", password_hash="hash", is_active=True)
    user.grades = []
    user.subjects = []
    db = MagicMock(spec=Session)
    grades = [Grade(id=1, name="Séptimo grado")]
    subjects = [Subject(id=3, name="Matemática")]
    db.scalars.side_effect = [
        SimpleNamespace(all=lambda: grades),
        SimpleNamespace(all=lambda: subjects),
    ]
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db_session] = lambda: db
    with TestClient(app) as client:
        yield client, user, db


def test_profile_starts_incomplete(profile_client) -> None:
    client, _, _ = profile_client

    response = client.get("/profile")

    assert response.status_code == 200
    assert response.json() == {
        "completed": False,
        "completed_at": None,
        "grades": [],
        "subjects": [],
    }


def test_profile_saves_multiple_teacher_assignments(profile_client) -> None:
    client, user, db = profile_client

    response = client.put(
        "/profile", json={"grade_ids": [1], "subject_ids": [3]}
    )

    assert response.status_code == 200
    assert response.json()["completed"] is True
    assert response.json()["grades"] == [{"id": 1, "name": "Séptimo grado"}]
    assert response.json()["subjects"] == [{"id": 3, "name": "Matemática"}]
    assert user.profile_completed_at is not None
    db.flush.assert_called_once_with()
    db.commit.assert_called_once_with()


@pytest.mark.parametrize(
    "payload",
    [
        {"grade_ids": [], "subject_ids": [1]},
        {"grade_ids": [1], "subject_ids": []},
        {"grade_ids": [1, 1], "subject_ids": [1]},
        {"grade_ids": [0], "subject_ids": [1]},
    ],
)
def test_profile_rejects_invalid_selections(profile_client, payload) -> None:
    client, _, db = profile_client

    response = client.put("/profile", json=payload)

    assert response.status_code == 422
    db.commit.assert_not_called()
