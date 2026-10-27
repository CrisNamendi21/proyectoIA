from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models import User
from app.schemas.profile import TeacherProfileRead, TeacherProfileUpdate
from app.services.profile import (
    ProfileReferenceError,
    ProfileStorageError,
    read_teacher_profile,
    update_teacher_profile,
)


router = APIRouter(
    prefix="/profile",
    tags=["profile"],
    responses={401: {"description": "Sesión ausente, inválida o usuario inactivo."}},
)


@router.get("", response_model=TeacherProfileRead)
def get_profile(
    user: Annotated[User, Depends(get_current_user)],
) -> TeacherProfileRead:
    return read_teacher_profile(user)


@router.put(
    "",
    response_model=TeacherProfileRead,
    responses={
        404: {"description": "Grado o asignatura inexistente."},
        422: {"description": "Selección inválida."},
        500: {"description": "No se pudo guardar el perfil."},
    },
)
def put_profile(
    data: TeacherProfileUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> TeacherProfileRead:
    try:
        return update_teacher_profile(db, user, data)
    except ProfileReferenceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ProfileStorageError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
