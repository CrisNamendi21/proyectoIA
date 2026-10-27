"""Servicio de generación de propuestas de planificación con IA."""

from dataclasses import dataclass

from pydantic import Field, HttpUrl, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.services.ai.errors import GeneratedPlanValidationError
from app.services.ai.ollama_client import OllamaClient
from app.services.ai.prompt_builder import (
    build_conversational_planning_prompt,
    build_planning_prompt,
)
from app.services.ai.schemas import (
    ChatHistoryMessage,
    ConversationalPlanningResponse,
    PlanningGenerationRequest,
    TeachingPlanDraft,
)


DEFAULT_OLLAMA_BASE_URL = "http://host.docker.internal:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5:3b"
DEFAULT_OLLAMA_TIMEOUT_SECONDS = 120.0


class OllamaSettings(BaseSettings):
    """Configuración propia de IA; el entorno prevalece sobre el .env local."""

    ollama_base_url: HttpUrl = Field(default=DEFAULT_OLLAMA_BASE_URL)
    ollama_model: str = Field(default=DEFAULT_OLLAMA_MODEL, min_length=1)
    ollama_timeout_seconds: float = Field(
        default=DEFAULT_OLLAMA_TIMEOUT_SECONDS, gt=0, allow_inf_nan=False
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


@dataclass(frozen=True)
class AIPlanningService:
    client: OllamaClient

    @classmethod
    def from_env(cls) -> "AIPlanningService":
        settings = OllamaSettings()
        client = OllamaClient(
            base_url=str(settings.ollama_base_url),
            model=settings.ollama_model,
            timeout_seconds=settings.ollama_timeout_seconds,
        )
        return cls(client=client)

    def generate_plan(
        self,
        request: PlanningGenerationRequest,
    ) -> TeachingPlanDraft:
        prompt = build_planning_prompt(request.context)
        generated_payload = self.client.generate_json(prompt, model=request.model)

        return self._validate_draft(generated_payload)

    def generate_conversational_plan(
        self,
        *,
        grade: str,
        subject: str,
        teacher_request: str,
        duration_minutes: int,
        history: list[ChatHistoryMessage],
        model: str | None = None,
    ) -> ConversationalPlanningResponse:
        prompt = build_conversational_planning_prompt(
            grade=grade,
            subject=subject,
            teacher_request=teacher_request,
            duration_minutes=duration_minutes,
            history=history,
        )
        generated_payload = self.client.generate_json(prompt, model=model)
        # El backend es la fuente de verdad para el contexto elegido. Estos campos
        # no se delegan al modelo y se fijan antes de validar el resto del borrador.
        generated_payload["schema_version"] = 1
        generated_payload["grade"] = grade
        generated_payload["subject"] = subject
        draft = self._validate_draft(generated_payload)

        checks: list[str] = ["Estructura pedagógica válida"]
        checks.append("Año fijado y verificado por el backend")
        checks.append("Asignatura fijada y verificada por el backend")

        generated_minutes = sum(activity.minutes for activity in draft.activities)
        if not duration_minutes * 0.5 <= generated_minutes <= duration_minutes * 1.5:
            raise GeneratedPlanValidationError(
                "La duración generada no es coherente con la solicitada."
            )
        if generated_minutes != duration_minutes:
            self._normalize_activity_minutes(draft, duration_minutes)
            checks.append(
                f"Duración ajustada y verificada: {duration_minutes} minutos"
            )
        else:
            checks.append(f"Duración verificada: {duration_minutes} minutos")

        return ConversationalPlanningResponse(
            assistant_message=(
                "Preparé un borrador profesional a partir de tu solicitud. "
                "Revísalo y ajústalo antes de guardarlo."
            ),
            draft=draft,
            quality_checks=checks,
        )

    @staticmethod
    def _validate_draft(generated_payload: object) -> TeachingPlanDraft:
        try:
            return TeachingPlanDraft.model_validate(generated_payload)
        except ValidationError as exc:
            raise GeneratedPlanValidationError(
                "La propuesta generada por IA no cumple el esquema esperado."
            ) from exc

    @staticmethod
    def _normalize_activity_minutes(
        draft: TeachingPlanDraft, requested_minutes: int
    ) -> None:
        """Escala la distribución generada sin cambiar la secuencia pedagógica."""
        current_total = sum(activity.minutes for activity in draft.activities)
        scaled = [
            max(1, round(activity.minutes * requested_minutes / current_total))
            for activity in draft.activities
        ]
        scaled[-1] += requested_minutes - sum(scaled)
        if scaled[-1] < 1:
            raise GeneratedPlanValidationError(
                "No fue posible ajustar la duración de las actividades."
            )
        for activity, minutes in zip(draft.activities, scaled, strict=True):
            activity.minutes = minutes
