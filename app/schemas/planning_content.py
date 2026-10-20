"""Contrato pedagógico versionado que comparten generación y planificaciones."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictContentModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LessonActivity(StrictContentModel):
    stage: Literal["inicio", "desarrollo", "cierre"]
    description: str = Field(min_length=1, max_length=1200)
    minutes: int = Field(ge=1, le=240)
    resources: list[str] = Field(default_factory=list, max_length=12)


class AssessmentSuggestion(StrictContentModel):
    criteria: list[str] = Field(min_length=1, max_length=8)
    evidence: str = Field(min_length=1, max_length=800)


class TeachingPlanDraft(StrictContentModel):
    schema_version: Literal[1] = 1
    title: str = Field(min_length=1, max_length=180)
    grade: str = Field(min_length=1, max_length=80)
    subject: str = Field(min_length=1, max_length=120)
    curriculum_content: str = Field(min_length=1, max_length=2000)
    learning_objective: str = Field(min_length=1, max_length=1000)
    activities: list[LessonActivity] = Field(min_length=3, max_length=8)
    assessment: AssessmentSuggestion
    materials: list[str] = Field(default_factory=list, max_length=12)
    teacher_notes: list[str] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def require_lesson_stages(self) -> "TeachingPlanDraft":
        present = {activity.stage for activity in self.activities}
        missing = {"inicio", "desarrollo", "cierre"} - present
        if missing:
            raise ValueError("Las actividades deben incluir inicio, desarrollo y cierre")
        return self
