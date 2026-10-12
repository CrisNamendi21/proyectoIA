import pytest

from app.services.ai.ai_service import AIPlanningService
from app.services.ai.errors import GeneratedPlanValidationError
from app.services.ai.prompt_builder import build_planning_prompt
from app.services.ai.schemas import CurriculumContext, PlanningGenerationRequest


def valid_generated_payload() -> dict:
    return {
        "title": "Planificación sobre fracciones",
        "grade": "Quinto grado",
        "subject": "Matemática",
        "curriculum_content": "Fracciones equivalentes",
        "learning_objective": "Reconocer fracciones equivalentes en situaciones cotidianas.",
        "activities": [
            {
                "stage": "inicio",
                "description": "Activar saberes previos con ejemplos visuales.",
                "minutes": 10,
                "resources": ["pizarra"],
            },
            {
                "stage": "desarrollo",
                "description": "Resolver ejercicios guiados en equipos.",
                "minutes": 25,
                "resources": ["tarjetas"],
            },
            {
                "stage": "cierre",
                "description": "Compartir conclusiones y dudas.",
                "minutes": 10,
                "resources": ["cuaderno"],
            },
        ],
        "assessment": {
            "criteria": ["Identifica equivalencias", "Explica su procedimiento"],
            "evidence": "Ejercicios resueltos y participación oral.",
        },
        "materials": ["pizarra", "tarjetas"],
        "teacher_notes": ["Ajustar apoyo si el grupo requiere más ejemplos."],
    }


class StubClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.received_prompt = ""
        self.received_model = None

    def generate_json(self, prompt: str, *, model: str | None = None) -> dict:
        self.received_prompt = prompt
        self.received_model = model
        return self.payload


def build_request() -> PlanningGenerationRequest:
    return PlanningGenerationRequest(
        context=CurriculumContext(
            grade="Quinto grado",
            subject="Matemática",
            curriculum_content="Fracciones equivalentes",
            duration_minutes=45,
            learning_goal="Comparar representaciones de fracciones.",
            resources=["pizarra", "tarjetas"],
        ),
        model="qwen2.5:3b",
    )


def test_generate_plan_validates_successful_payload() -> None:
    client = StubClient(valid_generated_payload())
    service = AIPlanningService(client=client)

    result = service.generate_plan(build_request())

    assert result.title == "Planificación sobre fracciones"
    assert result.activities[0].stage == "inicio"
    assert client.received_model == "qwen2.5:3b"
    assert "Fracciones equivalentes" in client.received_prompt


def test_generate_plan_rejects_missing_required_fields() -> None:
    payload = valid_generated_payload()
    payload.pop("learning_objective")
    service = AIPlanningService(client=StubClient(payload))

    with pytest.raises(GeneratedPlanValidationError):
        service.generate_plan(build_request())


def test_prompt_instructs_spanish_json_output() -> None:
    prompt = build_planning_prompt(build_request().context)

    assert "español" in prompt
    assert "JSON válido" in prompt
    assert "inicio" in prompt
    assert "desarrollo" in prompt
    assert "cierre" in prompt
