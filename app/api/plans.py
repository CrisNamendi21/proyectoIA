from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.plans import PlanningCreate, PlanningRead
from app.services.plans import (
    PlanningCoherenceError,
    PlanningReferenceError,
    PlanningStorageError,
    create_planning,
    get_planning,
    list_plannings,
)


# Conserva el nombre exportado para los tests aislados del módulo de Alejandra.
get_planning_user = get_current_user


router = APIRouter(prefix="/plans", tags=["plans"])
Owner = Annotated[User, Depends(get_planning_user)]
Database = Annotated[Session, Depends(get_db_session)]

auth_errors = {401: {"description": "Sesión ausente, inválida o usuario inactivo"}}


@router.post(
    "", response_model=PlanningRead, status_code=201,
    responses={**auth_errors, 404: {"description": "Referencia curricular inexistente"},
               422: {"description": "Datos inválidos o referencias incompatibles"},
               500: {"description": "Error al guardar la planificación"}},
)
def post_plan(data: PlanningCreate, user: Owner, db: Database) -> PlanningRead:
    try:
        planning = create_planning(db, data, user.id)
    except PlanningReferenceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PlanningCoherenceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except PlanningStorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return PlanningRead.model_validate(planning)


@router.get("", response_model=list[PlanningRead], responses=auth_errors)
def get_plans(user: Owner, db: Database) -> list[PlanningRead]:
    return [PlanningRead.model_validate(plan) for plan in list_plannings(db, user.id)]


@router.get(
    "/{plan_id}", response_model=PlanningRead,
    responses={**auth_errors, 404: {"description": "Planificación no encontrada para el usuario"}},
)
def get_plan(
    plan_id: Annotated[int, Path(gt=0)], user: Owner, db: Database,
) -> PlanningRead:
    planning = get_planning(db, plan_id, user.id)
    if planning is None:
        raise HTTPException(status_code=404, detail="Planificación no encontrada")
    return PlanningRead.model_validate(planning)
