"""Smoke HTTP real sobre un clon/proyecto Compose desechable ya preparado.

No arranca ni elimina recursos. El manifiesto de verificación debe identificar un
proyecto alfa-clean-<uuid>, sus puertos y el clon con credenciales nuevas.
Ejecutar con el Python de ese clon, después de su suite y de init_db.
"""

import argparse
from http.cookiejar import CookieJar
import json
import os
from pathlib import Path
import re
import runpy
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request


class HttpClient:
    def __init__(self, base_url, events):
        self.base_url = base_url
        self.events = events
        self.cookies = CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies))

    def request(self, method, path, body=None):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        request = urllib.request.Request(self.base_url + path, data=data, method=method)
        if data is not None:
            request.add_header("Content-Type", "application/json")
        try:
            response = self.opener.open(request, timeout=160)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            status = response.code
            raw = response.read()
        payload = json.loads(raw) if raw else None
        self.events.append({"method": method, "path": path, "status": status})
        return status, payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    project = manifest["project"]
    assert re.fullmatch(r"alfa-clean-[0-9a-f]{12}", project), "Proyecto no desechable"
    repo = Path(manifest["repo"]).resolve()
    assert (repo / ".git").is_dir(), "Falta el clon real"
    for service in ("backend", "alfa-db"):
        container = subprocess.check_output(
            manifest["compose"] + ["ps", "-q", service], cwd=repo, text=True,
        ).strip()
        assert container, "Servicio temporal no disponible"
        label = subprocess.check_output([
            "docker", "inspect", "--format", '{{ index .Config.Labels "com.docker.compose.project" }}', container,
        ], text=True).strip()
        assert label == project, "La identidad Docker no corresponde al entorno temporal"
    os.chdir(repo)
    sys.path.insert(0, str(repo))
    from dotenv import dotenv_values
    from sqlalchemy import create_engine, func, select, text
    from sqlalchemy.engine import make_url
    from sqlalchemy.orm import Session

    values = dotenv_values(repo / ".env")
    internal_url = make_url(values["DATABASE_URL"])
    assert internal_url.database == "colegio_alfa_clean_" + project.rsplit("-", 1)[1]
    assert internal_url.username == "alfa_clean_user"
    url = internal_url.set(host="127.0.0.1", port=manifest["postgres_port"])
    os.environ["DATABASE_URL"] = url.render_as_string(hide_password=False)
    os.environ["SESSION_SECRET_KEY"] = values["SESSION_SECRET_KEY"]
    os.environ["COLEGIO_ALFA_TEST_AI_FLOW"] = "1"
    from app.db.seed_users import create_user_if_missing
    from app.models import CurriculumContent, Grade, Planning, Subject, User
    from app.schemas.plans import PlanningCreate
    from app.services.ai.schemas import TeachingPlanDraft

    # Reutiliza la entrada curricular de las pruebas propias, sin TestClient.
    helpers = runpy.run_path(str(repo / "tests/integration/test_ai_planning_flow.py"))
    generation_request = helpers["generation_request"]()
    engine = create_engine(url)
    events = []
    stage = "initialization"
    started = time.perf_counter()
    try:
        # Este entorno nuevo no debe contener datos de otro desarrollador.
        with Session(engine) as session:
            assert session.scalar(select(func.count()).select_from(User)) == 0, "Usuarios preexistentes inesperados"
            assert session.scalar(select(func.count()).select_from(Planning)) == 0, "Planes preexistentes inesperados"
            password_a, password_b = secrets.token_urlsafe(24), secrets.token_urlsafe(24)
            assert create_user_if_missing(session, "docente_http_a_ficticio", password_a)
            assert create_user_if_missing(session, "docente_http_b_ficticio", password_b)
            assert not create_user_if_missing(session, "docente_http_a_ficticio", password_a)
            grade = Grade(name="Quinto grado")
            subject = Subject(name="Matemática")
            session.add_all([grade, subject])
            session.flush()
            content = CurriculumContent(grade_id=grade.id, subject_id=subject.id, description="Fracciones equivalentes")
            session.add(content)
            session.commit()
            grade_id, subject_id, content_id = grade.id, subject.id, content.id

        base_url = f"http://127.0.0.1:{manifest['backend_port']}"
        first, second = HttpClient(base_url, events), HttpClient(base_url, events)
        stage = "health and OpenAPI"
        assert first.request("GET", "/health") == (200, {"status": "ok"})
        status, specification = first.request("GET", "/openapi.json")
        paths = specification["paths"]
        assert status == 200 and {
            "/auth/login", "/auth/me", "/auth/logout", "/catalogs/grades", "/catalogs/subjects",
            "/catalogs/contents", "/generation", "/plans", "/plans/{plan_id}",
        } <= set(paths), "Faltan rutas integradas"
        assert first.request("GET", "/auth/me")[0] == 401
        assert first.request("POST", "/generation", generation_request)[0] == 401
        stage = "login and catalogs"
        assert first.request("POST", "/auth/login", {"username": "docente_http_a_ficticio", "password": "incorrecta"})[0] == 401
        status, identity_a = first.request("POST", "/auth/login", {"username": "docente_http_a_ficticio", "password": password_a})
        assert status == 200 and first.request("GET", "/auth/me") == (200, identity_a)
        assert any(cookie.name == "colegio_alfa_session" for cookie in first.cookies)
        for path, identifier in (("grades", grade_id), ("subjects", subject_id)):
            status, rows = first.request("GET", f"/catalogs/{path}")
            assert status == 200 and identifier in [row["id"] for row in rows]
        status, rows = first.request("GET", f"/catalogs/contents?grade_id={grade_id}&subject_id={subject_id}")
        assert status == 200 and len(rows) == 1 and rows[0]["id"] == content_id
        assert first.request("POST", "/generation", {"context": {}})[0] == 422
        stage = "single real Ollama generation"
        generation_started = time.perf_counter()
        status, generated = first.request("POST", "/generation", generation_request)
        assert status == 200, f"Generación real respondió HTTP {status}; no se reintenta"
        generation_seconds = round(time.perf_counter() - generation_started, 2)
        draft = TeachingPlanDraft.model_validate(generated)
        with Session(engine) as session:
            assert session.scalar(select(func.count()).select_from(Planning)) == 0
        draft.teacher_notes.append("Revisión HTTP simulada: usar tarjetas de apoyo.")
        draft.activities[0].description = "Comparar dibujos con apoyo de tarjetas."
        reviewed = TeachingPlanDraft.model_validate(draft.model_dump(mode="json"))
        body = PlanningCreate(
            grade_id=grade_id, subject_id=subject_id, curriculum_content_id=content_id,
            content=reviewed.model_dump(mode="json"),
        ).model_dump(mode="json")
        stage = "persistence and owner checks"
        assert first.request("POST", "/plans", {**body, "grade_id": 999999})[0] == 404
        assert first.request("POST", "/plans", {**body, "user_id": identity_a["id"]})[0] == 422
        status, saved = first.request("POST", "/plans", body)
        assert status == 201 and saved["content"] == body["content"]
        assert saved["user_id"] == identity_a["id"]
        plan_id = saved["id"]
        engine.dispose()
        with Session(engine) as session:
            persisted = session.get(Planning, plan_id)
            assert persisted.content == body["content"] and persisted.user_id == identity_a["id"]
            assert session.scalar(text("SELECT pg_typeof(content)::text FROM plannings WHERE id=:id"), {"id": plan_id}) == "jsonb"
        assert first.request("GET", "/plans") == (200, [saved])
        assert first.request("GET", f"/plans/{plan_id}") == (200, saved)
        status, identity_b = second.request("POST", "/auth/login", {"username": "docente_http_b_ficticio", "password": password_b})
        assert status == 200 and identity_b["id"] != identity_a["id"]
        assert second.request("GET", "/plans") == (200, [])
        assert second.request("GET", f"/plans/{plan_id}")[0] == 404
        status, own = second.request("POST", "/plans", body)
        assert status == 201 and own["user_id"] == identity_b["id"]
        assert first.request("GET", f"/plans/{own['id']}")[0] == 404
        assert first.request("GET", "/plans") == (200, [saved])
        stage = "logout"
        assert first.request("POST", "/auth/logout")[0] == 204
        assert not any(cookie.name == "colegio_alfa_session" for cookie in first.cookies)
        assert first.request("GET", "/auth/me")[0] == 401
        assert first.request("GET", "/plans")[0] == 401
        assert first.request("POST", "/generation", generation_request)[0] == 401
        assert first.request("POST", "/plans", body)[0] == 401
        with Session(engine) as session:
            assert session.scalar(select(func.count()).select_from(Planning)) == 2
        result = {
            "docker_http_flow": "passed", "commit": manifest["commit"],
            "http_requests": len(events), "generation_calls": 1,
            "generation_seconds": generation_seconds, "total_seconds": round(time.perf_counter() - started, 2),
            "postgres_jsonb": "verified from new connection", "owner_isolation": "both directions",
            "edit_route_integrated": "patch" in paths["/plans/{plan_id}"], "requests": events,
        }
        (args.manifest.parent / "http-result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result), flush=True)
        return 0
    except Exception as exc:
        error = {"docker_http_flow": "failed", "stage": stage, "type": type(exc).__name__, "requests": events}
        if isinstance(exc, AssertionError):
            error["check"] = str(exc)
        print(json.dumps(error), flush=True)
        return 1
    finally:
        engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
