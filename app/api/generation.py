"""Rutas de generación estructurada y conversación pedagógica."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db_session
from app.models import Grade, Subject, User
from app.services.ai.ai_service import AIPlanningService
from app.services.ai.errors import (
    GeneratedPlanValidationError,
    OllamaConnectionError,
    OllamaTimeoutError,
    OllamaUnexpectedResponseError,
)
from app.services.ai.schemas import (
    ConversationalPlanningRequest,
    ConversationalPlanningResponse,
    PlanningGenerationRequest,
    TeachingPlanDraft,
)


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


def generate_conversational_plan(
    request: ConversationalPlanningRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
    service: Annotated[AIPlanningService, Depends(get_ai_service)],
) -> ConversationalPlanningResponse:
    if user.profile_completed_at is None:
        raise HTTPException(
            status_code=409,
            detail="Completa tu perfil docente antes de iniciar una conversación.",
        )
    grade = db.get(Grade, request.grade_id)
    subject = db.get(Subject, request.subject_id)
    if grade is None or grade not in user.grades:
        raise HTTPException(
            status_code=422, detail="El año no pertenece al perfil docente."
        )
    if subject is None or subject not in user.subjects:
        raise HTTPException(
            status_code=422, detail="La asignatura no pertenece al perfil docente."
        )
    try:
        return service.generate_conversational_plan(
            grade=grade.name,
            subject=subject.name,
            teacher_request=request.message,
            duration_minutes=request.duration_minutes,
            history=request.history,
            model=request.model,
        )
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
            status_code=502,
            detail="La IA no produjo un borrador válido. Intenta reformular tu solicitud.",
        ) from None


def create_generation_router(path: str, *, include_chat: bool = False) -> APIRouter:
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
    if include_chat:
        router.add_api_route(
            "/chat/generate",
            generate_conversational_plan,
            methods=["POST"],
            response_model=ConversationalPlanningResponse,
            responses={
                401: {"description": "Sesión ausente, inválida o usuario inactivo."},
                409: {"description": "Perfil docente incompleto."},
                422: {"description": "Solicitud o contexto docente inválido."},
                502: {"description": "Respuesta de IA inválida."},
                503: {"description": "Ollama o su configuración no disponibles."},
                504: {"description": "Tiempo de espera de Ollama excedido."},
            },
        )
    return router
