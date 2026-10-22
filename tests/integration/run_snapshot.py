"""Prueba el código publicado de Cris sin fusionarlo ni usar datos de desarrollo.

Ejecutar desde la raíz: uv run python tests/integration/run_snapshot.py
La opción --real-ollama ejecuta únicamente una generación real y su flujo persistido.
"""

import argparse
import io
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import quote
import zipfile

from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="origin/Cris-develop")
    parser.add_argument("--real-ollama", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    revision = subprocess.check_output(
        ["git", "rev-parse", "--verify", f"{args.ref}^{{commit}}"],
        cwd=root, text=True,
    ).strip()
    archive = subprocess.check_output(
        ["git", "archive", "--format=zip", revision], cwd=root,
    )
    values = dotenv_values(root / ".env")
    source = os.environ.get("DATABASE_URL") or values.get("DATABASE_URL")
    if not source:
        raise SystemExit("Falta DATABASE_URL local; no se mostraron valores privados.")
    source_url = make_url(source)
    if source_url.drivername != "postgresql+psycopg":
        raise SystemExit("Se requiere PostgreSQL con Psycopg 3.")
    port = int(os.environ.get("POSTGRES_PORT") or values.get("POSTGRES_PORT") or 5432)
    admin_url = source_url.set(host="127.0.0.1", port=port, database="postgres")
    env = os.environ.copy()
    env["DATABASE_URL"] = admin_url.render_as_string(hide_password=False)
    env["COLEGIO_ALFA_INTEGRATION_ADMIN_URL"] = env["DATABASE_URL"]
    env["COLEGIO_ALFA_TEST_POSTGRES"] = "1"
    env["COLEGIO_ALFA_TEST_AI_FLOW"] = "1"
    env["COLEGIO_ALFA_TEST_REAL_OLLAMA"] = "1" if args.real_ollama else "0"
    env["SESSION_SECRET_KEY"] = secrets.token_urlsafe(48)
    env["SESSION_COOKIE_SECURE"] = "false"
    env["OLLAMA_BASE_URL"] = "http://localhost:11434"
    env["OLLAMA_MODEL"] = "qwen2.5:3b"
    env["OLLAMA_TIMEOUT_SECONDS"] = "120"
    # No .env privado se copia a la extracción del código.
    private = {
        value for key, value in values.items()
        if value and ("PASSWORD" in key or "SECRET" in key or key == "DATABASE_URL")
    }
    if source_url.password:
        private.add(source_url.password)
    private.add(env["SESSION_SECRET_KEY"])
    private.update(quote(value, safe="") for value in list(private))
    catalog_query = text(
        "SELECT datname FROM pg_database WHERE datname ~ "
        "'^colegio_alfa_(flow|auth|seed|ai_flow)_test_[0-9a-f]{32}$' ORDER BY datname"
    )
    admin = create_engine(admin_url)
    try:
        with admin.connect() as connection:
            if connection.execute(text("SELECT current_database()")).scalar_one() != "postgres":
                raise RuntimeError("La conexión administrativa no está aislada.")
            before = set(connection.execute(catalog_query).scalars())
        with tempfile.TemporaryDirectory(prefix="colegio-alfa-integrated-") as directory:
            snapshot = Path(directory)
            with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
                zipped.extractall(snapshot)
            if (snapshot / "uv.lock").read_bytes() != (root / "uv.lock").read_bytes():
                raise SystemExit("El lockfile remoto cambió; coordinar el entorno antes de probar.")
            target = snapshot / "tests" / "integration"
            target.mkdir(parents=True, exist_ok=True)
            for filename in (
                "conftest.py",
                "test_ai_planning_flow.py",
                "test_official_data_seed.py",
                "test_patch_persistence_alejandra.py",
            ):
                shutil.copy2(root / "tests" / "integration" / filename, target / filename)
            command = [sys.executable, "-m", "pytest", "-q"]
            if args.real_ollama:
                command.extend([
                    "-s", "tests/integration/test_ai_planning_flow.py::test_real_ollama_persisted_flow",
                ])
            print(json.dumps({
                "snapshot_commit": revision, "admin_database": "postgres",
                "mode": "real Ollama" if args.real_ollama else "mock Ollama + full suite",
            }), flush=True)
            result = subprocess.run(
                command, cwd=snapshot, env=env, capture_output=True,
                text=True, encoding="utf-8", errors="replace",
            )
            output = result.stdout + result.stderr
            for value in sorted(private, key=len, reverse=True):
                output = output.replace(value, "[REDACTED]")
            print(output, flush=True)
        with admin.connect() as connection:
            after = set(connection.execute(catalog_query).scalars())
        print(json.dumps({
            "pytest_exit_code": result.returncode,
            "temporary_database_catalog_unchanged": before == after,
            "new_leftover_databases": len(after - before),
        }), flush=True)
        return result.returncode if before == after else 1
    except Exception as exc:
        # La excepción SQL original podría revelar la configuración del equipo.
        print(f"Verificación interrumpida: {type(exc).__name__}; detalles privados omitidos.", file=sys.stderr)
        return 1
    finally:
        admin.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
