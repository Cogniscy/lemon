"""Minimal OpenRouter client for optional LLM candidate generation.

No API key is required for tests or dry-runs. Live calls read
OPENROUTER_API_KEY from the environment and never include the key in payloads or
stored records.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY_ENV = "OPENROUTER_API_KEY"


class OpenRouterConfigurationError(RuntimeError):
    """Raised when a live OpenRouter call is requested without credentials."""


class OpenRouterAPIError(RuntimeError):
    """Raised when OpenRouter returns an HTTP or malformed response error."""


def has_openrouter_key() -> bool:
    """Return True when OPENROUTER_API_KEY is present."""

    return bool(os.getenv(OPENROUTER_API_KEY_ENV))


def build_response_format(schema: dict[str, Any], *, name: str = "predicate_decomposition") -> dict[str, Any]:
    """Build OpenRouter/OpenAI-compatible JSON Schema response_format."""

    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "strict": True,
            "schema": schema,
        },
    }


def build_chat_payload(
    *,
    model: str,
    messages: list[dict[str, str]],
    response_schema: dict[str, Any] | None = None,
    temperature: float = 0.0,
    max_tokens: int = 1200,
) -> dict[str, Any]:
    """Build a serializable chat completion payload without credentials."""

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if response_schema is not None:
        payload["response_format"] = build_response_format(response_schema)
    return payload


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Cogniscy/lemon",
        "X-Title": "LEMON-Factor",
    }


def call_openrouter(
    payload: dict[str, Any],
    *,
    timeout: float = 60.0,
    retries: int = 1,
    url: str = OPENROUTER_URL,
) -> dict[str, Any]:
    """Call OpenRouter and return the parsed JSON response.

    The API key is read at call time and is never stored in the payload.
    """

    api_key = os.getenv(OPENROUTER_API_KEY_ENV)
    if not api_key:
        raise OpenRouterConfigurationError(
            f"{OPENROUTER_API_KEY_ENV} is not set; use --dry-run or --offline-fixture."
        )

    body = json.dumps(payload).encode("utf-8")
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        request = urllib.request.Request(url, data=body, headers=_headers(api_key), method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(1.0 * (attempt + 1))
                continue
            break
    raise OpenRouterAPIError(f"OpenRouter call failed: {last_error}")


def extract_message_content(response: dict[str, Any]) -> str:
    """Extract assistant message content from an OpenAI-compatible response."""

    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenRouterAPIError("Response does not contain choices[0].message.content") from exc
    if not isinstance(content, str):
        raise OpenRouterAPIError("Response content is not a string")
    return content
