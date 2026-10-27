import socket
import http.client
import json
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


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
def test_ollama_client_rejects_invalid_timeout(value: float) -> None:
    with pytest.raises(ValueError):
        OllamaClient(base_url="http://ollama.local", model="test", timeout_seconds=value)
    client = OllamaClient(base_url="http://ollama.local", model="test")
    with pytest.raises(ValueError):
        client.generate_json("JSON", timeout_seconds=value)


def test_ollama_client_sends_model_override_and_timeout(monkeypatch) -> None:
    def urlopen(request, timeout):
        assert request.get_method() == "POST"
        assert request.get_header("Content-type") == "application/json"
        assert json.loads(request.data) == {
            "model": "other", "prompt": "JSON", "stream": False,
            "format": "json", "options": {"temperature": 0}
        }
        assert timeout == 7
        return FakeResponse('{"response": "{}"}')
    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    client = OllamaClient(base_url="http://ollama.local", model="test")
    assert client.generate_json("JSON", model="other", timeout_seconds=7) == {}


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (urllib.error.HTTPError("http://ollama.local", 404, "missing", {}, None), OllamaConnectionError),
        (urllib.error.URLError(socket.timeout()), OllamaTimeoutError),
        (ConnectionResetError(), OllamaConnectionError),
        (http.client.IncompleteRead(b"partial"), OllamaConnectionError),
        (UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid"), OllamaUnexpectedResponseError),
    ],
)
def test_ollama_client_controls_transport_failures(monkeypatch, error, expected) -> None:
    def urlopen(request, timeout):
        raise error
    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    with pytest.raises(expected):
        OllamaClient(base_url="http://ollama.local", model="test").generate_json("JSON")


@pytest.mark.parametrize("body", ['[]', '{"response": "[]"}', '{"response": ""}', '{"response": 7}'])
def test_ollama_client_rejects_non_object_or_empty_response(monkeypatch, body) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", lambda request, timeout: FakeResponse(body))
    with pytest.raises(OllamaUnexpectedResponseError):
        OllamaClient(base_url="http://ollama.local", model="test").generate_json("JSON")
