import socket
import urllib.error
import urllib.request

import pytest

from app.services.ai.errors import (
    OllamaConnectionError,
    OllamaTimeoutError,
    OllamaUnexpectedResponseError,
)
from app.services.ai.ollama_client import OllamaClient


class FakeResponse:
    def __init__(self, body: str) -> None:
        self.body = body

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body.encode("utf-8")


def test_ollama_client_returns_generated_json(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(
        request: urllib.request.Request,
        timeout: float,
    ) -> FakeResponse:
        assert request.full_url == "http://ollama.local/api/generate"
        assert timeout == 5
        return FakeResponse('{"response": "{\\"ok\\": true}"}')

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    client = OllamaClient(
        base_url="http://ollama.local/",
        model="qwen2.5:3b",
        timeout_seconds=5,
    )

    assert client.generate_json("Responde JSON") == {"ok": True}


def test_ollama_client_converts_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(
        request: urllib.request.Request,
        timeout: float,
    ) -> FakeResponse:
        raise socket.timeout("timed out")

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    client = OllamaClient(base_url="http://ollama.local", model="qwen2.5:3b")

    with pytest.raises(OllamaTimeoutError):
        client.generate_json("Responde JSON")


def test_ollama_client_converts_connection_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_urlopen(
        request: urllib.request.Request,
        timeout: float,
    ) -> FakeResponse:
        raise urllib.error.URLError(ConnectionRefusedError("refused"))

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    client = OllamaClient(base_url="http://ollama.local", model="qwen2.5:3b")

    with pytest.raises(OllamaConnectionError):
        client.generate_json("Responde JSON")


def test_ollama_client_rejects_invalid_outer_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse("not json"),
    )
    client = OllamaClient(base_url="http://ollama.local", model="qwen2.5:3b")

    with pytest.raises(OllamaUnexpectedResponseError):
        client.generate_json("Responde JSON")


def test_ollama_client_rejects_invalid_generated_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse('{"response": "not json"}'),
    )
    client = OllamaClient(base_url="http://ollama.local", model="qwen2.5:3b")

    with pytest.raises(OllamaUnexpectedResponseError):
        client.generate_json("Responde JSON")


def test_ollama_client_rejects_missing_response_field(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: FakeResponse('{"done": true}'),
    )
    client = OllamaClient(base_url="http://ollama.local", model="qwen2.5:3b")

    with pytest.raises(OllamaUnexpectedResponseError):
        client.generate_json("Responde JSON")
