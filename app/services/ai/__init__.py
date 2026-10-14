"""Integración base con servicios locales de inteligencia artificial."""

from app.services.ai.ai_service import AIPlanningService
from app.services.ai.schemas import PlanningGenerationRequest, TeachingPlanDraft

__all__ = [
    "AIPlanningService",
    "PlanningGenerationRequest",
    "TeachingPlanDraft",
]
