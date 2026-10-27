from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.catalogs import GradeRead, SubjectRead


class TeacherProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grade_ids: list[int] = Field(min_length=1, max_length=8)
    subject_ids: list[int] = Field(min_length=1, max_length=16)

    @field_validator("grade_ids", "subject_ids")
    @classmethod
    def require_unique_positive_ids(cls, values: list[int]) -> list[int]:
        if any(isinstance(value, bool) or value <= 0 for value in values):
            raise ValueError("Los identificadores deben ser enteros positivos")
        if len(values) != len(set(values)):
            raise ValueError("No se permiten identificadores repetidos")
        return values


class TeacherProfileRead(BaseModel):
    completed: bool
    completed_at: datetime | None
    grades: list[GradeRead]
    subjects: list[SubjectRead]
