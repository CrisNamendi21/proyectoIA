"""Valida la línea Alembic completa sobre PostgreSQL desechable."""

import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys

from dotenv import dotenv_values
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL, make_url


DATABASE_PATTERN = re.compile(r"colegio_alfa_migration_test_[0-9a-f]{32}")
EXPECTED_TABLES = {
    "alembic_version",
    "curriculum_contents",
    "grades",
    "plannings",
    "subjects",
    "users",
}
UNIQUE_CONSTRAINT = "uq_curriculum_contents_grade_subject_description"


def redact(output: str, source_url: URL) -> str:
    values = {
        source_url.render_as_string(hide_password=False),
        source_url.render_as_string(hide_password=True),
    }
    if source_url.password:
        values.add(source_url.password)
    for value in sorted(values, key=len, reverse=True):
        output = output.replace(value, "[REDACTED]")
    return output


def run_alembic(root: Path, env: dict[str, str], source_url: URL, *args: str) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output = redact(result.stdout + result.stderr, source_url)
    if output:
        print(output, end="" if output.endswith("\n") else "\n")
    if result.returncode != 0:
        raise RuntimeError(f"Alembic devolvió código {result.returncode}: {' '.join(args)}")


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    values = dotenv_values(root / ".env")
    raw_url = os.environ.get("DATABASE_URL") or values.get("DATABASE_URL")
    if not raw_url:
        print("Falta DATABASE_URL; no se mostraron valores privados.", file=sys.stderr)
        return 2

    source_url = make_url(raw_url)
    if source_url.drivername != "postgresql+psycopg":
        print("Se requiere PostgreSQL con Psycopg 3.", file=sys.stderr)
        return 2
    port = int(os.environ.get("POSTGRES_PORT") or values.get("POSTGRES_PORT") or 5432)
    admin_url = source_url.set(host="127.0.0.1", port=port, database="postgres")
    database_name = f"colegio_alfa_migration_test_{secrets.token_hex(16)}"
    assert DATABASE_PATTERN.fullmatch(database_name)
    database_url = admin_url.set(database=database_name)
    admin = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    database = create_engine(database_url)
    created = False
    try:
        with admin.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{database_name}"'))
            created = True

        env = os.environ.copy()
        env["DATABASE_URL"] = database_url.render_as_string(hide_password=False)
        run_alembic(root, env, source_url, "upgrade", "head")
        run_alembic(root, env, source_url, "check")

        schema = inspect(database)
        tables_at_head = set(schema.get_table_names())
        constraints = {
            item["name"]
            for item in schema.get_unique_constraints("curriculum_contents")
        }
        if tables_at_head != EXPECTED_TABLES or UNIQUE_CONSTRAINT not in constraints:
            raise RuntimeError("El esquema en head no coincide con el contrato esperado.")

        database.dispose()
        run_alembic(root, env, source_url, "downgrade", "base")
        database = create_engine(database_url)
        tables_at_base = set(inspect(database).get_table_names())
        if tables_at_base != {"alembic_version"}:
            raise RuntimeError("El downgrade a base dejó tablas funcionales.")

        database.dispose()
        run_alembic(root, env, source_url, "upgrade", "head")
        run_alembic(root, env, source_url, "check")
        print(
            json.dumps(
                {
                    "upgrade_head": True,
                    "alembic_check": True,
                    "downgrade_base": True,
                    "second_upgrade_head": True,
                    "expected_tables": len(EXPECTED_TABLES),
                    "unique_constraint": True,
                }
            )
        )
        return 0
    except Exception as error:
        print(
            f"Verificación de migraciones interrumpida: {type(error).__name__}; "
            "detalles privados omitidos.",
            file=sys.stderr,
        )
        return 1
    finally:
        database.dispose()
        if created:
            with admin.connect() as connection:
                connection.execute(
                    text(f'DROP DATABASE IF EXISTS "{database_name}" WITH (FORCE)')
                )
        admin.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
