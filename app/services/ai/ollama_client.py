"""Cliente HTTP mínimo para Ollama usando solo la biblioteca estándar."""

from __future__ import annotations

import http.client
import json
import math
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from app.services.ai.errors import (
    OllamaConnectionError,
    OllamaTimeoutError,
    OllamaUnexpectedResponseError,
)


@dataclass(frozen=True)
class OllamaClient:
    base_url: str
    model: str
    timeout_seconds: float = 120.0

    def __post_init__(self) -> None:
        self._validate_timeout(self.timeout_seconds)

    @staticmethod
    def _validate_timeout(value: float) -> None:
        if not math.isfinite(value) or value <= 0:
            raise ValueError("El timeout de Ollama debe ser positivo y finito.")

    def generate_json(
        self,
        prompt: str,
        *,
        model: str | None = None,
        timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        effective_timeout = (
            self.timeout_seconds if timeout_seconds is None else timeout_seconds
        )
        self._validate_timeout(effective_timeout)
        payload = {
            "model": model or self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
        }
        request = urllib.request.Request(
            url=f"{self.base_url.rstrip('/')}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=effective_timeout,
            ) as response:
                response_body = response.read().decode("utf-8")
        except TimeoutError as exc:
            raise OllamaTimeoutError("Ollama no respondió antes del timeout.") from exc
        except urllib.error.HTTPError as exc:
            raise OllamaConnectionError(
                f"Ollama respondió con estado HTTP {exc.code}."
            ) from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, TimeoutError | socket.timeout):
                raise OllamaTimeoutError(
                    "Ollama no respondió antes del timeout."
                ) from exc
            raise OllamaConnectionError("No se pudo conectar con Ollama.") from exc
        except UnicodeDecodeError as exc:
            raise OllamaUnexpectedResponseError(
                "Ollama devolvió una respuesta que no es UTF-8 válido."
            ) from exc
        except (OSError, http.client.HTTPException) as exc:
            raise OllamaConnectionError(
                "Se interrumpió la comunicación con Ollama."
            ) from exc

        outer_payload = self._load_json_object(response_body, "respuesta HTTP de Ollama")
        response_text = outer_payload.get("response")
        if not isinstance(response_text, str) or not response_text.strip():
            raise OllamaUnexpectedResponseError(
                "Ollama no devolvió el campo esperado 'response'."
            )

        return self._load_json_object(response_text, "contenido generado por Ollama")

    @staticmethod
    def _load_json_object(raw_value: str, source: str) -> dict[str, Any]:
        try:
            parsed = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise OllamaUnexpectedResponseError(
                f"No se pudo interpretar como JSON el {source}."
            ) from exc

        if not isinstance(parsed, dict):
            raise OllamaUnexpectedResponseError(
                f"El {source} no contiene un objeto JSON."
            )
        return parsed
