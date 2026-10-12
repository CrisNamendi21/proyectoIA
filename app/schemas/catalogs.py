
from pydantic import BaseModel, ConfigDict


class GradeRead(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class SubjectRead(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class CurriculumContentRead(BaseModel):
    id: int
    grade_id: int
    subject_id: int
    description: str

    model_config = ConfigDict(from_attributes=True)
