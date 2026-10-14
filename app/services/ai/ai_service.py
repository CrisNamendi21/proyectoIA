"""Servicio de generación de propuestas de planificación con IA."""

from dataclasses import dataclass

from pydantic import Field, HttpUrl, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.services.ai.errors import GeneratedPlanValidationError
from app.services.ai.ollama_client import OllamaClient
from app.services.ai.prompt_builder import build_planning_prompt
from app.services.ai.schemas import PlanningGenerationRequest, TeachingPlanDraft


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

        try:
            return TeachingPlanDraft.model_validate(generated_payload)
        except ValidationError as exc:
            raise GeneratedPlanValidationError(
                "La propuesta generada por IA no cumple el esquema esperado."
            ) from exc
