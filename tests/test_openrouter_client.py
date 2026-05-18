from __future__ import annotations

import os

import pytest

from lemon_factor.llm.openrouter_client import (
    OpenRouterConfigurationError,
    build_chat_payload,
    build_response_format,
    call_openrouter,
    extract_message_content,
)


def test_build_chat_payload_does_not_include_api_key(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "secret-token")
    payload = build_chat_payload(
        model="test/model",
        messages=[{"role": "user", "content": "hello"}],
        response_schema={"type": "object"},
    )
    serialized = str(payload)
    assert "secret-token" not in serialized
    assert payload["model"] == "test/model"
    assert payload["temperature"] == 0.0
    assert payload["response_format"]["type"] == "json_schema"


def test_build_response_format_uses_strict_json_schema():
    response_format = build_response_format({"type": "object"}, name="x")
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    assert response_format["json_schema"]["schema"] == {"type": "object"}


def test_call_openrouter_without_key_raises(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(OpenRouterConfigurationError):
        call_openrouter({"model": "x", "messages": []})


def test_extract_message_content():
    response = {"choices": [{"message": {"content": "{}"}}]}
    assert extract_message_content(response) == "{}"
