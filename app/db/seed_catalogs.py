"""Valida y carga un catálogo curricular aprobado de forma explícita."""

import argparse
from dataclasses import dataclass
from datetime import date
import hashlib
import json
from pathlib import Path
import sys
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    ValidationError,
    field_validator,
    model_validator,
)
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import CurriculumContent, Grade, Subject


class CatalogInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CatalogSource(CatalogInput):
    name: str = Field(min_length=1, max_length=200)
    version: str = Field(min_length=1, max_length=100)
    reference: str = Field(min_length=1, max_length=500)
    url: HttpUrl | None = None
    approved_by: str = Field(min_length=1, max_length=120)
    approved_on: date

    @field_validator("name", "version", "reference", "approved_by", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class CatalogSubject(CatalogInput):
    name: str = Field(min_length=1, max_length=100)
    contents: list[Annotated[str, Field(min_length=1, max_length=2000)]] = Field(
        min_length=1
    )

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("contents", mode="before")
    @classmethod
    def strip_contents(cls, value: object) -> object:
        if isinstance(value, list):
            return [item.strip() if isinstance(item, str) else item for item in value]
        return value

    @model_validator(mode="after")
    def reject_duplicate_contents(self) -> "CatalogSubject":
        normalized = [content.casefold() for content in self.contents]
        if len(normalized) != len(set(normalized)):
            raise ValueError("Una asignatura no puede repetir contenidos")
        return self


class CatalogGrade(CatalogInput):
    name: str = Field(min_length=1, max_length=50)
    subjects: list[CatalogSubject] = Field(min_length=1)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def reject_duplicate_subjects(self) -> "CatalogGrade":
        normalized = [subject.name.casefold() for subject in self.subjects]
        if len(normalized) != len(set(normalized)):
            raise ValueError("Un grado no puede repetir asignaturas")
        return self


class CatalogDocument(CatalogInput):
    schema_version: Literal[1]
    source: CatalogSource
    grades: list[CatalogGrade] = Field(min_length=1)

    @model_validator(mode="after")
    def reject_duplicate_grades(self) -> "CatalogDocument":
        normalized = [grade.name.casefold() for grade in self.grades]
        if len(normalized) != len(set(normalized)):
            raise ValueError("El catálogo no puede repetir grados")
        return self


@dataclass(frozen=True)
class CatalogSeedResult:
    created_grades: int = 0
    created_subjects: int = 0
    created_contents: int = 0
    existing_grades: int = 0
    existing_subjects: int = 0
    existing_contents: int = 0


def load_catalog(path: Path) -> tuple[CatalogDocument, str]:
    raw = path.read_bytes()
    payload = json.loads(raw.decode("utf-8"))
    document = CatalogDocument.model_validate(payload)
    return document, hashlib.sha256(raw).hexdigest()


def seed_catalog(session: Session, document: CatalogDocument) -> CatalogSeedResult:
    counts = {
        "created_grades": 0,
        "created_subjects": 0,
        "created_contents": 0,
        "existing_grades": 0,
        "existing_subjects": 0,
        "existing_contents": 0,
    }
    subject_cache: dict[str, Subject] = {}

    try:
        for grade_entry in document.grades:
            grade = session.scalar(select(Grade).where(Grade.name == grade_entry.name))
            if grade is None:
                grade = Grade(name=grade_entry.name)
                session.add(grade)
                session.flush()
                counts["created_grades"] += 1
            else:
                counts["existing_grades"] += 1

            for subject_entry in grade_entry.subjects:
                subject = subject_cache.get(subject_entry.name)
                if subject is None:
                    subject = session.scalar(
                        select(Subject).where(Subject.name == subject_entry.name)
                    )
                    if subject is None:
                        subject = Subject(name=subject_entry.name)
                        session.add(subject)
                        session.flush()
                        counts["created_subjects"] += 1
                    else:
                        counts["existing_subjects"] += 1
                    subject_cache[subject_entry.name] = subject

                for description in subject_entry.contents:
                    existing = session.scalar(
                        select(CurriculumContent.id).where(
                            CurriculumContent.grade_id == grade.id,
                            CurriculumContent.subject_id == subject.id,
                            CurriculumContent.description == description,
                        )
                    )
                    if existing is None:
                        session.add(
                            CurriculumContent(
                                grade_id=grade.id,
                                subject_id=subject.id,
                                description=description,
                            )
                        )
                        counts["created_contents"] += 1
                    else:
                        counts["existing_contents"] += 1

        session.commit()
    except Exception:
        session.rollback()
        raise
    return CatalogSeedResult(**counts)


def catalog_totals(document: CatalogDocument) -> tuple[int, int, int]:
    subjects = {subject.name for grade in document.grades for subject in grade.subjects}
    contents = sum(
        len(subject.contents) for grade in document.grades for subject in grade.subjects
    )
    return len(document.grades), len(subjects), contents


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validar o cargar un catálogo curricular previamente aprobado."
    )
    parser.add_argument("file", type=Path, help="Archivo JSON del catálogo aprobado")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Guardar entradas ausentes; sin esta opción solo valida el archivo",
    )
    args = parser.parse_args()

    try:
        document, fingerprint = load_catalog(args.file)
    except (OSError, UnicodeError, json.JSONDecodeError, ValidationError) as error:
        print(f"Catálogo inválido: {error}", file=sys.stderr)
        return 2

    grades, subjects, contents = catalog_totals(document)
    print(
        f"Catálogo válido: {grades} grados, {subjects} asignaturas y "
        f"{contents} contenidos. SHA-256: {fingerprint}"
    )
    if not args.apply:
        print("Validación terminada; no se modificó la base de datos.")
        return 0

    from app.db.session import SessionLocal

    try:
        with SessionLocal() as session:
            result = seed_catalog(session, document)
    except SQLAlchemyError:
        print("No se pudo cargar el catálogo en la base de datos.", file=sys.stderr)
        return 1

    print(
        "Carga completada. Creados: "
        f"{result.created_grades} grados, {result.created_subjects} asignaturas y "
        f"{result.created_contents} contenidos. Ya existentes: "
        f"{result.existing_grades} grados, {result.existing_subjects} asignaturas y "
        f"{result.existing_contents} contenidos."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
