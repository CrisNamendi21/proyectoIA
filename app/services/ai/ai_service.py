"""Servicio de generación de propuestas de planificación con IA."""

import os
from dataclasses import dataclass

from pydantic import ValidationError

from app.services.ai.errors import GeneratedPlanValidationError
from app.services.ai.ollama_client import OllamaClient
from app.services.ai.prompt_builder import build_planning_prompt
from app.services.ai.schemas import PlanningGenerationRequest, TeachingPlanDraft


DEFAULT_OLLAMA_BASE_URL = "http://host.docker.internal:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5:3b"
DEFAULT_OLLAMA_TIMEOUT_SECONDS = 120.0


@dataclass(frozen=True)
class AIPlanningService:
    client: OllamaClient

    @classmethod
    def from_env(cls) -> "AIPlanningService":
        timeout_value = os.getenv(
            "OLLAMA_TIMEOUT_SECONDS",
            str(DEFAULT_OLLAMA_TIMEOUT_SECONDS),
        )
        try:
            timeout_seconds = float(timeout_value)
        except ValueError:
            timeout_seconds = DEFAULT_OLLAMA_TIMEOUT_SECONDS

        client = OllamaClient(
            base_url=os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL),
            model=os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL),
            timeout_seconds=timeout_seconds,
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
