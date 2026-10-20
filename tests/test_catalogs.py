from types import SimpleNamespace
from unittest.mock import MagicMock, call

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware


@pytest.fixture
def catalog_client(monkeypatch):
    # Solo configura un engine sin conexion; la dependencia se sustituye abajo.
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://test:test@127.0.0.1:1/catalogs_test",
    )
    from app.api.catalogs import get_catalog_user, router
    from app.db.session import get_db_session
    from app.models.grade import Grade
    from app.models.subject import Subject
    from app.models.user import User

    db = MagicMock(spec=Session)
    records = {
        (Grade, 1): SimpleNamespace(id=1, name="Quinto"),
        (Grade, 2): SimpleNamespace(id=2, name="Sexto"),
        (Subject, 1): SimpleNamespace(id=1, name="Matematica"),
        (Subject, 2): SimpleNamespace(id=2, name="Lengua"),
    }
    db.get.side_effect = lambda model, identifier: records.get((model, identifier))
    app = FastAPI()
    app.add_middleware(
        SessionMiddleware, secret_key="clave-ficticia-de-pruebas-32-caracteres"
    )
    app.include_router(router)
    app.dependency_overrides[get_db_session] = lambda: db
    app.dependency_overrides[get_catalog_user] = lambda: User(
        id=7, username="docente", is_active=True
    )

    with TestClient(app) as client:
        yield client, db, app
    app.dependency_overrides.clear()


@pytest.fixture
def contents():
    # Incluye coincidencias parciales para distinguir AND de OR.
    return [
        SimpleNamespace(id=1, grade_id=1, subject_id=1, description="Fracciones"),
        SimpleNamespace(id=2, grade_id=1, subject_id=2, description="Lectura"),
        SimpleNamespace(id=3, grade_id=2, subject_id=1, description="Decimales"),
        SimpleNamespace(id=4, grade_id=2, subject_id=2, description="Escritura"),
    ]


@pytest.mark.parametrize(
    "params, expected_ids, expected_where",
    [
        ({}, [1, 2, 3, 4], None),
        ({"grade_id": 1}, [1, 2], "curriculum_contents.grade_id = 1"),
        ({"subject_id": 1}, [1, 3], "curriculum_contents.subject_id = 1"),
        (
            {"grade_id": 1, "subject_id": 1},
            [1],
            "curriculum_contents.grade_id = 1 AND "
            "curriculum_contents.subject_id = 1",
        ),
    ],
    ids=["sin-filtros", "por-grado", "por-asignatura", "ambos-usan-and"],
)
def test_contents_filters(catalog_client, contents, params, expected_ids, expected_where):
    from app.models.grade import Grade
    from app.models.subject import Subject

    client, db, _ = catalog_client
    expected = [vars(row) for row in contents if row.id in expected_ids]
    db.scalars.return_value.all.return_value = [
        row for row in contents if row.id in expected_ids
    ]

    response = client.get("/catalogs/contents", params=params)

    assert response.status_code == 200
    assert response.json() == expected
    expected_calls = []
    if "grade_id" in params:
        expected_calls.append(call(Grade, params["grade_id"]))
    if "subject_id" in params:
        expected_calls.append(call(Subject, params["subject_id"]))
    assert db.get.call_args_list == expected_calls
    db.scalars.assert_called_once()
    statement = db.scalars.call_args.args[0]
    assert statement.column_descriptions[0]["entity"].__tablename__ == "curriculum_contents"
    if expected_where is None:
        assert statement.whereclause is None
    else:
        # Verifica el filtro real: la respuesta del mock por si sola no lo prueba.
        actual_where = str(
            statement.whereclause.compile(
                dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
            )
        )
        assert actual_where == expected_where
    assert str(statement.compile(dialect=postgresql.dialect())).endswith(
        "ORDER BY curriculum_contents.id"
    )


@pytest.mark.parametrize("parameter", ["grade_id", "subject_id"])
@pytest.mark.parametrize("value", ["0", "-1", "abc"])
def test_contents_rejects_invalid_filters(catalog_client, parameter, value):
    client, db, _ = catalog_client

    response = client.get("/catalogs/contents", params={parameter: value})

    assert response.status_code == 422
    assert any(
        error["loc"] == ["query", parameter]
        for error in response.json()["detail"]
    )
    db.get.assert_not_called()
    db.scalars.assert_not_called()


@pytest.mark.parametrize(
    "params, detail, expected_lookups",
    [
        ({"grade_id": 99}, "Grado no encontrado", [("grade", 99)]),
        ({"subject_id": 99}, "Asignatura no encontrada", [("subject", 99)]),
        (
            {"grade_id": 99, "subject_id": 1},
            "Grado no encontrado",
            [("grade", 99)],
        ),
        (
            {"grade_id": 1, "subject_id": 99},
            "Asignatura no encontrada",
            [("grade", 1), ("subject", 99)],
        ),
        (
            {"grade_id": 99, "subject_id": 99},
            "Grado no encontrado",
            [("grade", 99)],
        ),
    ],
    ids=[
        "grado-inexistente",
        "asignatura-inexistente",
        "ambos-grado-inexistente",
        "ambos-asignatura-inexistente",
        "ambos-inexistentes-prioriza-grado",
    ],
)
def test_contents_rejects_missing_ids(catalog_client, params, detail, expected_lookups):
    from app.models.grade import Grade
    from app.models.subject import Subject

    client, db, _ = catalog_client
    models = {"grade": Grade, "subject": Subject}

    response = client.get("/catalogs/contents", params=params)

    assert response.status_code == 404
    assert response.json() == {"detail": detail}
    assert db.get.call_args_list == [
        call(models[model], identifier) for model, identifier in expected_lookups
    ]
    db.scalars.assert_not_called()


@pytest.mark.parametrize(
    "params",
    [{"grade_id": 1}, {"subject_id": 1}, {"grade_id": 1, "subject_id": 1}],
    ids=["grado-sin-contenidos", "asignatura-sin-contenidos", "ambos-sin-contenidos"],
)
def test_existing_ids_without_contents(catalog_client, params):
    from app.models.grade import Grade
    from app.models.subject import Subject

    client, db, _ = catalog_client
    db.scalars.return_value.all.return_value = []

    response = client.get("/catalogs/contents", params=params)

    assert response.status_code == 200
    assert response.json() == []
    expected_calls = []
    if "grade_id" in params:
        expected_calls.append(call(Grade, params["grade_id"]))
    if "subject_id" in params:
        expected_calls.append(call(Subject, params["subject_id"]))
    assert db.get.call_args_list == expected_calls
    db.scalars.assert_called_once()
    db.scalars.return_value.all.assert_called_once_with()


@pytest.mark.parametrize(
    "endpoint, table, names",
    [
        ("/catalogs/grades", "grades", ["Quinto", "Sexto"]),
        ("/catalogs/subjects", "subjects", ["Matematica", "Lengua"]),
    ],
)
def test_basic_catalogs(catalog_client, endpoint, table, names):
    client, db, _ = catalog_client
    rows = [SimpleNamespace(id=index, name=name) for index, name in enumerate(names, 1)]
    db.scalars.return_value.all.return_value = rows

    response = client.get(endpoint)

    assert response.status_code == 200
    assert response.json() == [vars(row) for row in rows]
    db.scalars.assert_called_once()
    statement = db.scalars.call_args.args[0]
    assert statement.column_descriptions[0]["entity"].__tablename__ == table
    assert statement.whereclause is None
    assert str(statement.compile(dialect=postgresql.dialect())).endswith(
        f"ORDER BY {table}.id"
    )


def test_catalogs_require_active_session(catalog_client):
    from app.api.catalogs import get_catalog_user

    client, db, app = catalog_client
    del app.dependency_overrides[get_catalog_user]

    response = client.get("/catalogs/grades")

    assert response.status_code == 401
    db.scalars.assert_not_called()
