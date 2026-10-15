import argparse
import getpass
import sys

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.core.validation import normalize_username
from app.models import User


def user_exists(session: Session, username: str) -> bool:
    return session.scalar(select(User.id).where(User.username == username)) is not None


def create_user_if_missing(session: Session, username: str, password: str) -> bool:
    normalized = normalize_username(username)
    if user_exists(session, normalized):
        return False
    if not password:
        raise ValueError("La contraseña no puede estar vacía.")

    session.add(
        User(
            username=normalized,
            password_hash=hash_password(password),
            is_active=True,
        )
    )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        if user_exists(session, normalized):
            return False
        raise
    except Exception:
        session.rollback()
        raise
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Crear una cuenta docente precreada.")
    parser.add_argument("username", help="Nombre de usuario de la cuenta")
    args = parser.parse_args()

    try:
        username = normalize_username(args.username)
    except ValueError as error:
        parser.error(str(error))

    from app.db.session import SessionLocal

    try:
        with SessionLocal() as session:
            if user_exists(session, username):
                print("La cuenta ya existe; no se modificó.")
                return 0
    except SQLAlchemyError:
        print("No se pudo consultar la base de datos.", file=sys.stderr)
        return 1

    if not sys.stdin.isatty():
        print("Ejecuta el comando en una terminal interactiva.", file=sys.stderr)
        return 2

    try:
        password = getpass.getpass("Contraseña inicial: ")
        confirmation = getpass.getpass("Repite la contraseña: ")
    except (EOFError, KeyboardInterrupt):
        print("Entrada cancelada.", file=sys.stderr)
        return 2

    if not password or password != confirmation:
        print("La contraseña está vacía o no coincide.", file=sys.stderr)
        return 2

    try:
        with SessionLocal() as session:
            created = create_user_if_missing(session, username, password)
    except SQLAlchemyError:
        print("No se pudo guardar la cuenta en la base de datos.", file=sys.stderr)
        return 1

    if created:
        print("Cuenta creada.")
    else:
        print("La cuenta ya existe; no se modificó.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
