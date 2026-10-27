from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Grade, Subject, User
from app.schemas.profile import TeacherProfileRead, TeacherProfileUpdate


class ProfileReferenceError(ValueError):
    """Uno o más grados o asignaturas no existen."""


class ProfileStorageError(Exception):
    """No fue posible guardar el perfil."""


def read_teacher_profile(user: User) -> TeacherProfileRead:
    return TeacherProfileRead(
        completed=user.profile_completed_at is not None,
        completed_at=user.profile_completed_at,
        grades=sorted(user.grades, key=lambda item: item.name.casefold()),
        subjects=sorted(user.subjects, key=lambda item: item.name.casefold()),
    )


def update_teacher_profile(
    db: Session, user: User, data: TeacherProfileUpdate
) -> TeacherProfileRead:
    try:
        grades = list(
            db.scalars(select(Grade).where(Grade.id.in_(data.grade_ids))).all()
        )
        subjects = list(
            db.scalars(select(Subject).where(Subject.id.in_(data.subject_ids))).all()
        )
        if {item.id for item in grades} != set(data.grade_ids):
            raise ProfileReferenceError("Uno o más años seleccionados no existen.")
        if {item.id for item in subjects} != set(data.subject_ids):
            raise ProfileReferenceError("Una o más asignaturas seleccionadas no existen.")

        user.grades = grades
        user.subjects = subjects
        user.profile_completed_at = datetime.now(timezone.utc)
        db.flush()
        db.commit()
        return read_teacher_profile(user)
    except ProfileReferenceError:
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise ProfileStorageError("No se pudo guardar el perfil docente.") from exc
