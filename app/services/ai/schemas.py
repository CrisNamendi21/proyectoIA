"""Esquemas internos del módulo IA.

Estos modelos validan la propuesta generada antes de exponerla o guardarla.
`TeachingPlanDraft` versión 1 es también el contrato de `Planning.content` del MVP.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.planning_content import (
    AssessmentSuggestion,
    LessonActivity,
    TeachingPlanDraft,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CurriculumContext(StrictModel):
    grade: str = Field(min_length=1, max_length=80)
    subject: str = Field(min_length=1, max_length=120)
    curriculum_content: str = Field(min_length=1, max_length=2000)
    duration_minutes: int = Field(default=45, ge=15, le=240)
    learning_goal: str | None = Field(default=None, max_length=1000)
    student_needs: str | None = Field(default=None, max_length=1000)
    resources: list[str] = Field(default_factory=list, max_length=12)


class PlanningGenerationRequest(StrictModel):
    context: CurriculumContext
    model: str | None = Field(default=None, min_length=1, max_length=120)


class ChatHistoryMessage(StrictModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=1200)


class ConversationalPlanningRequest(StrictModel):
    grade_id: int = Field(gt=0)
    subject_id: int = Field(gt=0)
    message: str = Field(min_length=3, max_length=4000)
    duration_minutes: int = Field(default=45, ge=15, le=240)
    history: list[ChatHistoryMessage] = Field(default_factory=list, max_length=8)
    model: str | None = Field(default=None, min_length=1, max_length=120)


class ConversationalPlanningResponse(StrictModel):
    assistant_message: str = Field(min_length=1, max_length=500)
    draft: TeachingPlanDraft
    quality_checks: list[str] = Field(min_length=1, max_length=8)


__all__ = [
    "AssessmentSuggestion",
    "CurriculumContext",
    "ChatHistoryMessage",
    "ConversationalPlanningRequest",
    "ConversationalPlanningResponse",
    "LessonActivity",
    "PlanningGenerationRequest",
    "TeachingPlanDraft",
]
