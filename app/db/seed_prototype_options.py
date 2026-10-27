"""Carga opciones demostrativas para evaluar el onboarding del frontend.

No representa un catálogo curricular oficial y no crea contenidos curriculares.
La ejecución exige ``--apply`` para evitar mutaciones accidentales.
"""

import argparse

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Grade, Subject


PROTOTYPE_GRADES = (
    "Séptimo grado",
    "Octavo grado",
    "Noveno grado",
    "Décimo grado",
    "Undécimo grado",
)

PROTOTYPE_SUBJECTS = (
    "Lengua y Literatura",
    "Matemática",
    "Inglés",
    "Ciencias Naturales",
    "Estudios Sociales",
    "Física",
    "Química",
    "Biología",
    "Educación Física",
    "Informática",
)


def seed_prototype_options(session: Session) -> tuple[int, int]:
    created_grades = 0
    created_subjects = 0
    try:
        for name in PROTOTYPE_GRADES:
            if session.scalar(select(Grade.id).where(Grade.name == name)) is None:
                session.add(Grade(name=name))
                created_grades += 1
        for name in PROTOTYPE_SUBJECTS:
            if session.scalar(select(Subject.id).where(Subject.name == name)) is None:
                session.add(Subject(name=name))
                created_subjects += 1
        session.commit()
    except Exception:
        session.rollback()
        raise
    return created_grades, created_subjects


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cargar años y asignaturas demostrativas, no oficiales."
    )
    parser.add_argument(
        "--apply", action="store_true", help="Confirmar la carga en PostgreSQL"
    )
    args = parser.parse_args()
    if not args.apply:
        print(
            f"Prototipo listo: {len(PROTOTYPE_GRADES)} años y "
            f"{len(PROTOTYPE_SUBJECTS)} asignaturas. Usa --apply para cargarlos."
        )
        return 0

    from app.db.session import SessionLocal

    try:
        with SessionLocal() as session:
            grades, subjects = seed_prototype_options(session)
    except SQLAlchemyError:
        print("No se pudieron cargar las opciones del prototipo.")
        return 1
    print(
        f"Opciones cargadas. Creadas: {grades} años y {subjects} asignaturas."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
