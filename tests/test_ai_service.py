import pytest
from pydantic import ValidationError

from app.services.ai.ai_service import AIPlanningService, DEFAULT_OLLAMA_TIMEOUT_SECONDS
from app.services.ai.errors import GeneratedPlanValidationError
from app.services.ai.prompt_builder import build_planning_prompt
from app.services.ai.schemas import CurriculumContext, PlanningGenerationRequest


def valid_generated_payload() -> dict:
    return {
        "schema_version": 1,
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


def test_default_timeout_allows_local_ollama_generation_window() -> None:
    assert DEFAULT_OLLAMA_TIMEOUT_SECONDS == 120.0


def test_from_env_loads_dotenv_and_environment_takes_precedence(
    monkeypatch: pytest.MonkeyPatch, tmp_path,
) -> None:
    monkeypatch.chdir(tmp_path)
    for key in ("OLLAMA_BASE_URL", "OLLAMA_MODEL", "OLLAMA_TIMEOUT_SECONDS"):
        monkeypatch.delenv(key, raising=False)
    (tmp_path / ".env").write_text(
        "OLLAMA_BASE_URL=http://localhost:11434\n"
        "OLLAMA_MODEL=qwen2.5:3b\nOLLAMA_TIMEOUT_SECONDS=75\n"
        "DATABASE_URL=unused-test-value\n",
        encoding="utf-8",
    )
    service = AIPlanningService.from_env()
    assert service.client.base_url.rstrip("/") == "http://localhost:11434"
    assert service.client.timeout_seconds == 75
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "90")
    assert AIPlanningService.from_env().client.timeout_seconds == 90


@pytest.mark.parametrize("value", ["0", "-1", "nan", "inf", "invalid"])
def test_from_env_rejects_invalid_timeout(monkeypatch, tmp_path, value) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", value)
    with pytest.raises(ValidationError):
        AIPlanningService.from_env()


def test_from_env_rejects_non_http_url(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OLLAMA_BASE_URL", "file:///private")
    with pytest.raises(ValidationError):
        AIPlanningService.from_env()
