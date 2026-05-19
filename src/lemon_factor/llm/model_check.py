"""Preflight checks for OpenRouter model configuration.

This module is intentionally lightweight: it does not require an API key for the
public models endpoint, but it will include OPENROUTER_API_KEY when available.
It helps avoid expensive runs that fail with HTTP 404 because a configured model
id is unavailable or deprecated.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lemon_factor.llm.decompose_predicates import read_model_config
from lemon_factor.llm.openrouter_client import OPENROUTER_API_KEY_ENV

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"


@dataclass(frozen=True)
class ModelCheckResult:
    """One OpenRouter model preflight result."""

    model: str
    available: bool
    supports_structured_outputs: bool | None = None
    supported_parameters: tuple[str, ...] = ()
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "available": self.available,
            "supports_structured_outputs": self.supports_structured_outputs,
            "supported_parameters": list(self.supported_parameters),
            "reason": self.reason,
        }


def _headers() -> dict[str, str]:
    headers = {"Accept": "application/json"}
    api_key = os.getenv(OPENROUTER_API_KEY_ENV)
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def fetch_openrouter_models(*, url: str = OPENROUTER_MODELS_URL, timeout: float = 30.0) -> list[dict[str, Any]]:
    """Fetch the OpenRouter model catalog.

    The public endpoint normally works without authentication. If an API key is
    present, it is passed only as an HTTP header and is not returned or logged.
    """

    request = urllib.request.Request(url, headers=_headers(), method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"OpenRouter model catalog request failed: {exc}") from exc

    data = payload.get("data") if isinstance(payload, dict) else payload
    if not isinstance(data, list):
        raise RuntimeError("OpenRouter model catalog response does not contain a model list")
    return [item for item in data if isinstance(item, dict)]


def supported_parameters(model_info: dict[str, Any]) -> tuple[str, ...]:
    """Return supported parameter names from heterogeneous OpenRouter metadata."""

    raw = model_info.get("supported_parameters") or model_info.get("supportedParams") or []
    if not isinstance(raw, list):
        return ()
    return tuple(str(item) for item in raw)


def supports_structured_outputs(model_info: dict[str, Any]) -> bool | None:
    """Infer whether a model advertises structured-output support.

    OpenRouter metadata evolves, so this is a best-effort check. A return value
    of None means the model is available but the catalog does not explicitly say
    whether response_format/json_schema is supported.
    """

    params = set(supported_parameters(model_info))
    if {"response_format", "structured_outputs", "json_schema"} & params:
        return True

    # Some catalog entries expose capability-like objects. Keep this permissive
    # and conservative: only explicit True becomes True; otherwise unknown.
    for key in ("capabilities", "features", "architecture"):
        value = model_info.get(key)
        if isinstance(value, dict):
            for capability_key in (
                "structured_outputs",
                "structuredOutputs",
                "json_schema",
                "response_format",
            ):
                if value.get(capability_key) is True:
                    return True
        elif isinstance(value, list):
            lowered = {str(item).lower() for item in value}
            if {"structured_outputs", "json_schema", "response_format"} & lowered:
                return True
    return None


def catalog_by_id(models: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Index catalog entries by model id."""

    indexed: dict[str, dict[str, Any]] = {}
    for item in models:
        model_id = item.get("id")
        if isinstance(model_id, str) and model_id:
            indexed[model_id] = item
    return indexed


def check_models(model_ids: list[str], catalog: list[dict[str, Any]]) -> list[ModelCheckResult]:
    """Check configured model ids against an OpenRouter catalog."""

    indexed = catalog_by_id(catalog)
    results: list[ModelCheckResult] = []
    for model in model_ids:
        info = indexed.get(model)
        if info is None:
            results.append(
                ModelCheckResult(
                    model=model,
                    available=False,
                    reason="model id not present in OpenRouter catalog",
                )
            )
            continue
        params = supported_parameters(info)
        structured = supports_structured_outputs(info)
        reason = "available"
        if structured is None:
            reason = "available; structured-output support not explicit in catalog"
        elif structured is False:
            reason = "available; structured-output support not advertised"
        results.append(
            ModelCheckResult(
                model=model,
                available=True,
                supports_structured_outputs=structured,
                supported_parameters=params,
                reason=reason,
            )
        )
    return results


def read_models_from_args(args: argparse.Namespace) -> list[str]:
    models: list[str] = []
    if args.models:
        models.extend(read_model_config(args.models))
    if args.model:
        models.extend(args.model)
    return list(dict.fromkeys(models))


def write_results(results: list[ModelCheckResult], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "models": [result.to_dict() for result in results],
        "summary": {
            "total": len(results),
            "available": sum(1 for result in results if result.available),
            "unavailable": sum(1 for result in results if not result.available),
            "structured_explicit": sum(
                1 for result in results if result.supports_structured_outputs is True
            ),
            "structured_unknown": sum(
                1 for result in results if result.available and result.supports_structured_outputs is None
            ),
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", help="YAML-like model config")
    parser.add_argument("--model", action="append", help="Single model id; may be repeated")
    parser.add_argument("--out", default="data/reports/openrouter_model_check.json")
    parser.add_argument("--strict-structured", action="store_true", help="Exit non-zero if structured output support is not explicitly advertised")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_ids = read_models_from_args(args)
    if not model_ids:
        raise SystemExit("No models supplied; use --models or --model.")
    catalog = fetch_openrouter_models()
    results = check_models(model_ids, catalog)
    write_results(results, args.out)
    print(json.dumps({"out": args.out, "models": [r.to_dict() for r in results]}, indent=2))

    failed = [result for result in results if not result.available]
    if args.strict_structured:
        failed.extend(
            result
            for result in results
            if result.available and result.supports_structured_outputs is not True
        )
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
