from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.planning_content import TeachingPlanDraft


PositiveId = Annotated[int, Field(strict=True, gt=0)]


class PlanningReferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    grade_id: PositiveId | None = None
    subject_id: PositiveId | None = None
    curriculum_content_id: PositiveId | None = None


class PlanningCreate(PlanningReferences):
    content: TeachingPlanDraft


class PlanningUpdate(PlanningReferences):
    content: TeachingPlanDraft | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_null_content(cls, value: object) -> object:
        if isinstance(value, dict) and "content" in value and value["content"] is None:
            raise ValueError("content no puede ser nulo")
        return value

    @model_validator(mode="after")
    def require_changes(self) -> "PlanningUpdate":
        if not self.model_fields_set:
            raise ValueError("Debe proporcionar al menos un campo para actualizar")
        return self


class PlanningRead(PlanningCreate):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: PositiveId
    user_id: PositiveId
    created_at: datetime
    updated_at: datetime
