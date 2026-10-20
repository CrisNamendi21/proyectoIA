
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models.grade import Grade
from app.models.subject import Subject
from app.models.curriculum_content import CurriculumContent
from app.models.user import User
from app.schemas.catalogs import (
    GradeRead,
    SubjectRead,
    CurriculumContentRead,
)


get_catalog_user = get_current_user


router = APIRouter(
    prefix="/catalogs",
    tags=["catalogs"],
    responses={401: {"description": "Sesión ausente, inválida o usuario inactivo"}},
)
CatalogUser = Annotated[User, Depends(get_catalog_user)]


@router.get("/grades", response_model=list[GradeRead])
def get_grades(_user: CatalogUser, db: Session = Depends(get_db_session)):
    statement = select(Grade).order_by(Grade.id)
    return db.scalars(statement).all()


@router.get("/subjects", response_model=list[SubjectRead])
def get_subjects(_user: CatalogUser, db: Session = Depends(get_db_session)):
    statement = select(Subject).order_by(Subject.id)
    return db.scalars(statement).all()


@router.get(
    "/contents",
    response_model=list[CurriculumContentRead],
    responses={404: {"description": "Grado o asignatura no encontrados"}},
)
def get_contents(
    _user: CatalogUser,
    db: Session = Depends(get_db_session),
    grade_id: int | None = Query(default=None, gt=0),
    subject_id: int | None = Query(default=None, gt=0),
):
    if grade_id is not None and db.get(Grade, grade_id) is None:
        raise HTTPException(status_code=404, detail="Grado no encontrado")
    if subject_id is not None and db.get(Subject, subject_id) is None:
        raise HTTPException(status_code=404, detail="Asignatura no encontrada")

    statement = select(CurriculumContent).order_by(
        CurriculumContent.id
    )
    if grade_id is not None:
        statement = statement.where(CurriculumContent.grade_id == grade_id)
    if subject_id is not None:
        statement = statement.where(CurriculumContent.subject_id == subject_id)
    return db.scalars(statement).all()
