"""Errores controlados del módulo de IA."""


class AIServiceError(Exception):
    """Error base para la integración de IA."""


class OllamaConnectionError(AIServiceError):
    """Ollama no está disponible o rechazó la conexión."""


class OllamaTimeoutError(AIServiceError):
    """Ollama tardó más de lo permitido en responder."""


class OllamaUnexpectedResponseError(AIServiceError):
    """Ollama devolvió una respuesta que no coincide con lo esperado."""


class GeneratedPlanValidationError(AIServiceError):
    """La propuesta generada no cumple el esquema local del módulo."""
