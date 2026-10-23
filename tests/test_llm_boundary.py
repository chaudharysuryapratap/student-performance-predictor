"""Provider-boundary tests use synthetic input and mocked HTTP only."""

import io
import json

import pytest

from core.conversation import Conversation
from core.llm.provider_openai import OpenAIClient
from core.validation import feature_spec


def test_structured_provider_request(monkeypatch):
    captured = []
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-test-key")
    monkeypatch.setenv("OPENAI_MODEL", "synthetic-test-model")

    def fake_urlopen(request, timeout):
        captured.append(json.loads(request.data))
        values = {f["name"]: None for f in feature_spec()["features"]}
        values["Attendance_Rate"] = 70
        return io.BytesIO(
            json.dumps({"choices": [{"message": {"content": json.dumps(values)}}]}).encode()
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = OpenAIClient().extract_fields(
        "ExamplePerson says attendance 70% example@example.test", "Attendance_Rate"
    )
    assert result["Attendance_Rate"] == 70
    body = captured[0]
    assert body["response_format"]["json_schema"]["strict"]
    serialized = json.dumps(body)
    assert "ExamplePerson" not in serialized and "example@example" not in serialized
    assert "score" not in body["response_format"]["json_schema"]["schema"]["properties"]


def test_unconfigured_provider_falls_back(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    c = Conversation()
    c.consent()
    c.submit("22")
    assert c.values == {"Study_Hours_per_Week": 22.0}


@pytest.mark.llm_integration
def test_live_provider():
    import os

    if not (
        os.getenv("RUN_LLM_INTEGRATION") == "true"
        and os.getenv("OPENAI_API_KEY")
        and os.getenv("OPENAI_MODEL")
    ):
        pytest.skip("Requires explicit live-test opt-in, model and credentials.")
    output = OpenAIClient().extract_fields("attendance 70 percent", "Attendance_Rate")
    assert output["Attendance_Rate"] == 70
