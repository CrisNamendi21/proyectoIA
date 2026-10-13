"""Construcción de prompts para propuestas de planificación docente."""

import json

from app.services.ai.schemas import CurriculumContext


def build_planning_prompt(context: CurriculumContext) -> str:
    context_payload = context.model_dump()
    context_json = json.dumps(context_payload, ensure_ascii=False, indent=2)

    return f"""
Eres un asistente pedagógico para docentes del Colegio Alfa.
Genera una propuesta inicial de planificación didáctica en español.

Usa exclusivamente este contexto curricular:
{context_json}

Reglas:
- Responde solo con JSON válido, sin Markdown ni texto adicional.
- No inventes datos personales, firmas, nombres de docentes ni información sensible.
- Mantén la propuesta como borrador editable, no como planificación oficial aprobada.
- Incluye actividades claras para inicio, desarrollo y cierre.
- Respeta la duración total aproximada indicada en minutos.

El JSON debe tener exactamente esta estructura:
{{
  "title": "string",
  "grade": "string",
  "subject": "string",
  "curriculum_content": "string",
  "learning_objective": "string",
  "activities": [
    {{
      "stage": "inicio",
      "description": "string",
      "minutes": 10,
      "resources": ["string"]
    }},
    {{
      "stage": "desarrollo",
      "description": "string",
      "minutes": 25,
      "resources": ["string"]
    }},
    {{
      "stage": "cierre",
      "description": "string",
      "minutes": 10,
      "resources": ["string"]
    }}
  ],
  "assessment": {{
    "criteria": ["string"],
    "evidence": "string"
  }},
  "materials": ["string"],
  "teacher_notes": ["string"]
}}
""".strip()
