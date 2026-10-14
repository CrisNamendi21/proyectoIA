"""Generación aislada: Cris debe elegir la ruta HTTP antes de registrarla.

Los esquemas reutilizados siguen siendo provisionales; no definen Planning.content.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_current_user
from app.services.ai.ai_service import AIPlanningService
from app.services.ai.errors import (
    GeneratedPlanValidationError,
    OllamaConnectionError,
    OllamaTimeoutError,
    OllamaUnexpectedResponseError,
)
from app.services.ai.schemas import PlanningGenerationRequest, TeachingPlanDraft


def get_ai_service() -> AIPlanningService:
    try:
        return AIPlanningService.from_env()
    except ValueError:
        raise HTTPException(
            status_code=503, detail="Configuración de IA no disponible."
        ) from None


def generate_plan(
    request: PlanningGenerationRequest,
    service: Annotated[AIPlanningService, Depends(get_ai_service)],
) -> TeachingPlanDraft:
    """FastAPI ejecuta esta función síncrona en su pool de hilos."""
    try:
        return service.generate_plan(request)
    except OllamaTimeoutError:
        raise HTTPException(
            status_code=504, detail="Ollama excedió el tiempo de espera."
        ) from None
    except OllamaConnectionError:
        raise HTTPException(
            status_code=503, detail="Ollama no está disponible."
        ) from None
    except (OllamaUnexpectedResponseError, GeneratedPlanValidationError):
        raise HTTPException(
            status_code=502, detail="Ollama devolvió una propuesta inválida."
        ) from None


def create_generation_router(path: str) -> APIRouter:
    """Exporta el router sin inventar una ruta compartida ni registrar en main.py."""
    router = APIRouter(tags=["generation"])
    router.add_api_route(
        path,
        generate_plan,
        methods=["POST"],
        response_model=TeachingPlanDraft,
        dependencies=[Depends(get_current_user)],
        responses={
            401: {"description": "Sesión ausente, inválida o usuario inactivo."},
            422: {"description": "Solicitud inválida."},
            502: {"description": "Respuesta de IA inválida."},
            503: {"description": "Ollama o su configuración no disponibles."},
            504: {"description": "Tiempo de espera de Ollama excedido."},
        },
    )
    return router
