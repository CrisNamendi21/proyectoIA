from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import CurriculumContent, Grade, Planning, Subject
from app.schemas.plans import PlanningCreate


class PlanningReferenceError(ValueError):
    """Una referencia curricular no existe."""


class PlanningCoherenceError(ValueError):
    """Las referencias no corresponden al contenido curricular."""


class PlanningStorageError(Exception):
    """La transacción no pudo completarse."""


def create_planning(db: Session, data: PlanningCreate, owner_id: int) -> Planning:
    try:
        for model, identifier, label in (
            (Grade, data.grade_id, "Grado"),
            (Subject, data.subject_id, "Asignatura"),
        ):
            if identifier is not None and db.get(model, identifier) is None:
                raise PlanningReferenceError(f"{label} no encontrado")

        if data.curriculum_content_id is not None:
            curriculum = db.get(CurriculumContent, data.curriculum_content_id)
            if curriculum is None:
                raise PlanningReferenceError("Contenido curricular no encontrado")
            if data.grade_id is not None and data.grade_id != curriculum.grade_id:
                raise PlanningCoherenceError("El contenido curricular no corresponde al grado")
            if data.subject_id is not None and data.subject_id != curriculum.subject_id:
                raise PlanningCoherenceError("El contenido curricular no corresponde a la asignatura")

        planning = Planning(user_id=owner_id, **data.model_dump(mode="json"))
        db.add(planning)
        # Populate generated IDs/timestamps before commit; no fallible refresh afterwards.
        db.flush()
        db.commit()
        return planning
    except (PlanningReferenceError, PlanningCoherenceError):
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise PlanningStorageError("No se pudo guardar la planificación") from exc


def list_plannings(db: Session, owner_id: int) -> list[Planning]:
    statement = select(Planning).where(Planning.user_id == owner_id).order_by(Planning.id)
    return list(db.scalars(statement).all())


def get_planning(db: Session, plan_id: int, owner_id: int) -> Planning | None:
    statement = select(Planning).where(
        Planning.id == plan_id, Planning.user_id == owner_id
    )
    return db.scalars(statement).one_or_none()
