"""Esquemas internos del módulo IA.

Estos modelos validan la propuesta generada antes de exponerla o guardarla.
No representan todavía el contrato compartido de `Planning.content`.
"""

from typing import Literal

from pydantic import BaseModel, Field


class CurriculumContext(BaseModel):
    grade: str = Field(min_length=1, max_length=80)
    subject: str = Field(min_length=1, max_length=120)
    curriculum_content: str = Field(min_length=1, max_length=2000)
    duration_minutes: int = Field(default=45, ge=15, le=240)
    learning_goal: str | None = Field(default=None, max_length=1000)
    student_needs: str | None = Field(default=None, max_length=1000)
    resources: list[str] = Field(default_factory=list, max_length=12)


class PlanningGenerationRequest(BaseModel):
    context: CurriculumContext
    model: str | None = Field(default=None, min_length=1, max_length=120)


class LessonActivity(BaseModel):
    stage: Literal["inicio", "desarrollo", "cierre"]
    description: str = Field(min_length=1, max_length=1200)
    minutes: int = Field(ge=1, le=240)
    resources: list[str] = Field(default_factory=list, max_length=12)


class AssessmentSuggestion(BaseModel):
    criteria: list[str] = Field(min_length=1, max_length=8)
    evidence: str = Field(min_length=1, max_length=800)


class TeachingPlanDraft(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    grade: str = Field(min_length=1, max_length=80)
    subject: str = Field(min_length=1, max_length=120)
    curriculum_content: str = Field(min_length=1, max_length=2000)
    learning_objective: str = Field(min_length=1, max_length=1000)
    activities: list[LessonActivity] = Field(min_length=3, max_length=8)
    assessment: AssessmentSuggestion
    materials: list[str] = Field(default_factory=list, max_length=12)
    teacher_notes: list[str] = Field(default_factory=list, max_length=8)
