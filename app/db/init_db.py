import sys
from pathlib import Path

from alembic import command
from alembic.config import Config


ROOT = Path(__file__).resolve().parents[2]


def init_db() -> None:
    """Actualiza la base hasta la última revisión de Alembic."""
    config = Config(ROOT / "alembic.ini")
    command.upgrade(config, "head")


def main() -> int:
    try:
        init_db()
    except Exception:
        print("No se pudo inicializar la base de datos.", file=sys.stderr)
        return 1
    print("Base de datos inicializada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
