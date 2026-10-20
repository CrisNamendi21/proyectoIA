from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import CurriculumContent, Grade, Planning, Subject
from app.schemas.plans import PlanningCreate, PlanningUpdate


class PlanningReferenceError(ValueError):
    """Una referencia curricular no existe."""


class PlanningCoherenceError(ValueError):
    """Las referencias no corresponden al contenido curricular."""


class PlanningStorageError(Exception):
    """La transacción no pudo completarse."""


def validate_references(db: Session, data: PlanningCreate) -> None:
    for model, identifier, label, expected in (
        (Grade, data.grade_id, "Grado", data.content.grade),
        (Subject, data.subject_id, "Asignatura", data.content.subject),
    ):
        if identifier is not None:
            reference = db.get(model, identifier)
            if reference is None:
                raise PlanningReferenceError(f"{label} no encontrado")
            if reference.name != expected:
                raise PlanningCoherenceError(
                    f"{label} no coincide con el contenido de la planificación"
                )

    if data.curriculum_content_id is not None:
        curriculum = db.get(CurriculumContent, data.curriculum_content_id)
        if curriculum is None:
            raise PlanningReferenceError("Contenido curricular no encontrado")
        if data.grade_id is not None and data.grade_id != curriculum.grade_id:
            raise PlanningCoherenceError("El contenido curricular no corresponde al grado")
        if data.subject_id is not None and data.subject_id != curriculum.subject_id:
            raise PlanningCoherenceError("El contenido curricular no corresponde a la asignatura")
        if curriculum.description != data.content.curriculum_content:
            raise PlanningCoherenceError(
                "El contenido curricular no coincide con el contenido de la planificación"
            )


def create_planning(db: Session, data: PlanningCreate, owner_id: int) -> Planning:
    try:
        validate_references(db, data)
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


def update_planning(
    db: Session, plan_id: int, data: PlanningUpdate, owner_id: int,
) -> Planning | None:
    try:
        planning = get_planning(db, plan_id, owner_id)
        if planning is None:
            return None
        changes = data.model_dump(mode="json", exclude_unset=True)
        final = PlanningCreate.model_validate({
            field: changes.get(field, getattr(planning, field))
            for field in PlanningCreate.model_fields
        })
        validate_references(db, final)
        for field, value in changes.items():
            setattr(planning, field, value)
        db.flush()
        db.commit()
        return planning
    except (PlanningReferenceError, PlanningCoherenceError):
        db.rollback()
        raise
    except SQLAlchemyError as exc:
        db.rollback()
        raise PlanningStorageError("No se pudo actualizar la planificación") from exc
