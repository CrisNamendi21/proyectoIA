import os

import pytest

if os.getenv("COLEGIO_ALFA_TEST_AI_FLOW") != "1":
    pytest.skip(
        "Requiere el runner aislado y PostgreSQL desechable",
        allow_module_level=True,
    )

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Planning


def test_patch_persiste_en_postgresql(flow_environment):
    env = flow_environment

    original = {
        "grade_id": env.grade_id,
        "subject_id": env.subject_id,
        "curriculum_content_id": env.content_id,
        "content": {"title": "Planificacion original"},
    }

    with TestClient(env.app) as docente:
        login = docente.post("/auth/login", json={
            "username": "docente_a_ficticio",
            "password": "clave-ficticia-integracion",
        })
        assert login.status_code == 200

        created = docente.post("/plans", json=original)
        assert created.status_code == 201
        plan_id = created.json()["id"]

        updated_content = {
            "title": "Planificacion editada",
            "activities": ["Actividad modificada"],
        }

        edited = docente.patch(
            f"/plans/{plan_id}",
            json={"content": updated_content},
        )
        assert edited.status_code == 200
        assert edited.json()["content"] == updated_content

        env.engine.dispose()

        with Session(env.engine) as session:
            persisted = session.get(Planning, plan_id)
            assert persisted is not None
            assert persisted.content == updated_content

        with TestClient(env.app) as otro_docente:
            login_other = otro_docente.post("/auth/login", json={
                "username": "docente_b_ficticio",
                "password": "clave-ficticia-integracion",
            })
            assert login_other.status_code == 200

            denied = otro_docente.patch(
                f"/plans/{plan_id}",
                json={"content": {"title": "Cambio no autorizado"}},
            )
            assert denied.status_code == 404

        with Session(env.engine) as session:
            persisted = session.get(Planning, plan_id)
            assert persisted.content == updated_content
