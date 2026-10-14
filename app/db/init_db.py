import sys

from sqlalchemy.exc import SQLAlchemyError

from app.db.base import Base
from app.db.session import engine


def init_db() -> None:
    import app.models

    Base.metadata.create_all(bind=engine)


def main() -> int:
    try:
        init_db()
    except SQLAlchemyError:
        print("No se pudo inicializar la base de datos.", file=sys.stderr)
        return 1
    print("Base de datos inicializada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
