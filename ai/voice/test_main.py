"""SEC-028/SEC-014 regression tests: voice auth + upload size cap.

Run with the backend venv: `backend/.venv/bin/python -m pytest ai/voice/test_main.py`
"""

import importlib.util
import sys
import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
TOKEN = "test-token"


class _FakeSegments:
    def __iter__(self):
        return iter(())


class _FakeInfo:
    language = "hi"


class _FakeWhisperModel:
    def __init__(self, *args, **kwargs):
        pass

    def transcribe(self, path, language=None):
        return _FakeSegments(), _FakeInfo()


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "faster_whisper",
        types.SimpleNamespace(WhisperModel=_FakeWhisperModel),
    )
    path = Path(__file__).with_name("main.py")
    spec = importlib.util.spec_from_file_location("voice_main_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return TestClient(module.app)


def _post(client, data=b"x", token: str | None = TOKEN):
    headers = {"Authorization": f"Bearer {token}"} if token is not None else {}
    return client.post(
        "/transcribe",
        files={"file": ("sample.wav", data)},
        headers=headers,
    )


def test_health_open(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"service": "voice", "status": "ok"}


def test_transcribe_rejects_missing_token(client, monkeypatch):
    monkeypatch.setenv("VOICE_SERVICE_TOKEN", TOKEN)
    resp = _post(client, token=None)
    assert resp.status_code == 401


def test_transcribe_rejects_wrong_token(client, monkeypatch):
    monkeypatch.setenv("VOICE_SERVICE_TOKEN", TOKEN)
    resp = _post(client, token="wrong")
    assert resp.status_code == 401


def test_transcribe_fails_closed_without_configured_token(client, monkeypatch):
    monkeypatch.delenv("VOICE_SERVICE_TOKEN", raising=False)
    resp = _post(client)
    assert resp.status_code == 503


def test_transcribe_rejects_oversized_upload(client, monkeypatch):
    monkeypatch.setenv("VOICE_SERVICE_TOKEN", TOKEN)
    resp = _post(client, data=b"x" * (MAX_UPLOAD_BYTES + 1))
    assert resp.status_code == 413


def test_transcribe_accepts_authorized_upload(client, monkeypatch):
    monkeypatch.setenv("VOICE_SERVICE_TOKEN", TOKEN)
    resp = _post(client, data=b"x")
    assert resp.status_code == 200
    assert resp.json() == {"language": "hi", "text": ""}
