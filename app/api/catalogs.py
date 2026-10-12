
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.models.grade import Grade
from app.models.subject import Subject
from app.models.curriculum_content import CurriculumContent
from app.schemas.catalogs import (
    GradeRead,
    SubjectRead,
    CurriculumContentRead,
)


router = APIRouter(prefix="/catalogs", tags=["catalogs"])


@router.get("/grades", response_model=list[GradeRead])
def get_grades(db: Session = Depends(get_db_session)):
    statement = select(Grade).order_by(Grade.id)
    return db.scalars(statement).all()


@router.get("/subjects", response_model=list[SubjectRead])
def get_subjects(db: Session = Depends(get_db_session)):
    statement = select(Subject).order_by(Subject.id)
    return db.scalars(statement).all()


@router.get(
    "/contents",
    response_model=list[CurriculumContentRead],
)
def get_contents(db: Session = Depends(get_db_session)):
    statement = select(CurriculumContent).order_by(
        CurriculumContent.id
    )
    return db.scalars(statement).all()
