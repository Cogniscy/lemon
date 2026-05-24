"""Run saved LLM reliability probe prompts through OpenRouter.

This runner is intentionally separate from the deterministic LEMON scoring path.
It reads JSONL prompt payloads created by ``prepare_llm_probe`` and writes
schema-valid ``LLMProbeJudgment`` JSONL records that can be summarized later.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Iterable

from lemon_factor.reliability.schema import FactorJudgment, LLMProbeJudgment

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPTS = {
    "strict": """You are a careful semantic-coverage judge for an NLP reliability study.
Decide whether each semantic factor from a source graph edge is supported by the perturbed text.
Use the original text only as context. Do not use outside knowledge.
Return JSON only. For each factor, choose exactly one of: covered, partial, absent.
Use short evidence phrases only; do not provide chain-of-thought.""",
    "no_rationale": """You are a semantic-coverage judge for an NLP reliability study.
Decide whether each semantic factor from a source graph edge is supported by the perturbed text.
Return JSON only. Use no outside knowledge. Set evidence to null for every decision.""",
}


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL record at {path}:{line_no}") from exc
    return records


def _completed_item_ids(path: str | Path) -> set[str]:
    out = Path(path)
    if not out.exists():
        return set()
    completed: set[str] = set()
    with out.open("r", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            item_id = record.get("item_id")
            if isinstance(item_id, str):
                completed.add(item_id)
    return completed


def _judgment_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["item_id", "judge_id", "decisions"],
        "properties": {
            "item_id": {"type": "string"},
            "judge_id": {"type": "string"},
            "decisions": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["factor_id", "decision"],
                    "properties": {
                        "factor_id": {"type": "string"},
                        "decision": {"type": "string", "enum": ["covered", "partial", "absent"]},
                        "confidence": {"type": ["number", "null"], "minimum": 0.0, "maximum": 1.0},
                        "evidence": {"type": ["string", "null"]},
                    },
                },
            },
            "notes": {"type": ["string", "null"]},
        },
    }


def response_format(mode: str) -> dict[str, Any] | None:
    """Return an OpenRouter response_format payload for the requested mode."""

    if mode == "none":
        return None
    if mode == "json_object":
        return {"type": "json_object"}
    if mode == "json_schema":
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "lemon_factor_judgment",
                "strict": True,
                "schema": _judgment_schema(),
            },
        }
    raise ValueError(f"Unknown response format mode: {mode}")


def build_messages(prompt_payload: dict[str, Any], *, prompt_style: str) -> list[dict[str, str]]:
    if prompt_style not in SYSTEM_PROMPTS:
        raise ValueError(f"Unknown prompt style: {prompt_style}")
    factor_ids = [str(factor["id"]) for factor in prompt_payload.get("factors", []) if isinstance(factor, dict) and factor.get("id")]
    expected = {
        "item_id": prompt_payload.get("item_id"),
        "judge_id": "<set this to the judge id supplied by the caller>",
        "decisions": [
            {
                "factor_id": factor_id,
                "decision": "covered|partial|absent",
                "confidence": 0.0,
                "evidence": None,
            }
            for factor_id in factor_ids
        ],
        "notes": None,
    }
    user_content = {
        "task": "Judge factor coverage in the perturbed text.",
        "allowed_decisions": ["covered", "partial", "absent"],
        "decision_rules": {
            "covered": "The perturbed text clearly supports the factor.",
            "partial": "The perturbed text weakly or ambiguously supports the factor.",
            "absent": "The perturbed text does not support the factor or contradicts it.",
        },
        "expected_json_shape": expected,
        "input_item": prompt_payload,
    }
    return [
        {"role": "system", "content": SYSTEM_PROMPTS[prompt_style]},
        {"role": "user", "content": json.dumps(user_content, ensure_ascii=False, indent=2)},
    ]


def build_request_payload(
    prompt_payload: dict[str, Any],
    *,
    model: str,
    prompt_style: str,
    temperature: float,
    max_tokens: int,
    response_format_mode: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": build_messages(prompt_payload, prompt_style=prompt_style),
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    fmt = response_format(response_format_mode)
    if fmt is not None:
        payload["response_format"] = fmt
    return payload


def _extract_message_content(response: dict[str, Any]) -> str:
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"Unexpected OpenRouter response shape: {response!r}") from exc
    if not isinstance(content, str) or not content.strip():
        raise ValueError("OpenRouter response did not contain non-empty message content")
    return content


def extract_json_object(text: str) -> dict[str, Any]:
    """Extract one JSON object from a model response."""

    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"\s*```$", "", text).strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model response")
    parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("Extracted JSON is not an object")
    return parsed


def _normalise_decisions(raw: dict[str, Any], prompt_payload: dict[str, Any], *, judge_id: str, model: str, prompt_style: str) -> LLMProbeJudgment:
    item_id = str(prompt_payload.get("item_id") or raw.get("item_id") or "")
    factor_ids = [str(factor["id"]) for factor in prompt_payload.get("factors", []) if isinstance(factor, dict) and factor.get("id")]
    factor_set = set(factor_ids)
    raw_decisions = raw.get("decisions")
    if not isinstance(raw_decisions, list):
        raise ValueError("Judgment JSON has no decisions list")

    decisions_by_factor: dict[str, FactorJudgment] = {}
    for decision in raw_decisions:
        if not isinstance(decision, dict):
            continue
        factor_id = str(decision.get("factor_id") or "")
        if factor_id not in factor_set:
            continue
        label = str(decision.get("decision") or "").casefold().strip()
        if label not in {"covered", "partial", "absent"}:
            continue
        confidence = decision.get("confidence")
        if confidence is not None:
            try:
                confidence = max(0.0, min(1.0, float(confidence)))
            except (TypeError, ValueError):
                confidence = None
        evidence = decision.get("evidence")
        if evidence is not None:
            evidence = str(evidence).strip() or None
        if prompt_style == "no_rationale":
            evidence = None
        decisions_by_factor[factor_id] = FactorJudgment(
            factor_id=factor_id,
            decision=label,  # type: ignore[arg-type]
            confidence=confidence,
            evidence=evidence,
        )

    missing = [factor_id for factor_id in factor_ids if factor_id not in decisions_by_factor]
    if missing:
        raise ValueError(f"Judgment missing factor decisions: {missing[:5]}")

    notes = raw.get("notes")
    judgment = LLMProbeJudgment(
        item_id=item_id,
        judge_id=judge_id,
        decisions=[decisions_by_factor[factor_id] for factor_id in factor_ids],
        notes=str(notes).strip() if notes else None,
        metadata={"model": model, "prompt_style": prompt_style, "transport": "openrouter"},
    )
    return judgment


def parse_judgment_from_response(response: dict[str, Any], prompt_payload: dict[str, Any], *, judge_id: str, model: str, prompt_style: str) -> LLMProbeJudgment:
    raw_text = _extract_message_content(response)
    raw_json = extract_json_object(raw_text)
    return _normalise_decisions(raw_json, prompt_payload, judge_id=judge_id, model=model, prompt_style=prompt_style)


def _post_openrouter(payload: dict[str, Any], *, api_key: str, timeout: float, referer: str | None, title: str | None) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if referer:
        headers["HTTP-Referer"] = referer
    if title:
        headers["X-OpenRouter-Title"] = title
    request = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - explicit user-supplied API endpoint
        body = response.read().decode("utf-8")
    parsed = json.loads(body)
    if not isinstance(parsed, dict):
        raise ValueError("OpenRouter returned non-object JSON")
    return parsed


def _iter_prompts(prompts: Iterable[dict[str, Any]], *, limit: int | None, completed: set[str]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for payload in prompts:
        item_id = str(payload.get("item_id") or "")
        if item_id in completed:
            continue
        selected.append(payload)
        if limit is not None and len(selected) >= limit:
            break
    return selected


def run_openrouter_judge(
    prompts_path: str | Path,
    out: str | Path,
    *,
    model: str,
    judge_id: str,
    prompt_style: str = "strict",
    response_format_mode: str = "json_object",
    temperature: float = 0.0,
    max_tokens: int = 1200,
    limit: int | None = None,
    resume: bool = True,
    timeout: float = 90.0,
    max_retries: int = 3,
    sleep_seconds: float = 0.0,
    api_key: str | None = None,
    referer: str | None = None,
    title: str | None = "LEMON-Factor Reliability Probe",
    dry_run: bool = False,
    report_out: str | Path | None = None,
) -> dict[str, Any]:
    api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not dry_run and not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    prompts = _read_jsonl(prompts_path)
    completed = _completed_item_ids(out) if resume else set()
    selected = _iter_prompts(prompts, limit=limit, completed=completed)
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)

    if dry_run:
        request_example = build_request_payload(
            selected[0] if selected else (prompts[0] if prompts else {}),
            model=model,
            prompt_style=prompt_style,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format_mode=response_format_mode,
        ) if prompts else {}
        report = {
            "status": "dry_run",
            "prompts_total": len(prompts),
            "prompts_selected": len(selected),
            "out": str(out),
            "model": model,
            "judge_id": judge_id,
            "prompt_style": prompt_style,
            "response_format": response_format_mode,
            "request_example": request_example,
        }
        if report_out:
            Path(report_out).parent.mkdir(parents=True, exist_ok=True)
            Path(report_out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report

    written = 0
    failures: list[dict[str, Any]] = []
    mode = "a" if resume else "w"
    with path.open(mode, encoding="utf-8") as stream:
        for index, prompt_payload in enumerate(selected, start=1):
            last_error: str | None = None
            request_payload = build_request_payload(
                prompt_payload,
                model=model,
                prompt_style=prompt_style,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format_mode=response_format_mode,
            )
            for attempt in range(1, max_retries + 1):
                try:
                    response = _post_openrouter(request_payload, api_key=api_key or "", timeout=timeout, referer=referer, title=title)
                    judgment = parse_judgment_from_response(response, prompt_payload, judge_id=judge_id, model=model, prompt_style=prompt_style)
                    stream.write(json.dumps(judgment.model_dump(mode="json"), ensure_ascii=False) + "\n")
                    stream.flush()
                    written += 1
                    last_error = None
                    break
                except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
                    last_error = str(exc)
                    if attempt < max_retries:
                        time.sleep(min(2 ** (attempt - 1), 10))
            if last_error:
                failures.append({"item_id": prompt_payload.get("item_id"), "error": last_error})
            if sleep_seconds and index < len(selected):
                time.sleep(sleep_seconds)

    report = {
        "status": "passed" if not failures else "partial",
        "prompts_total": len(prompts),
        "prompts_selected": len(selected),
        "judgments_written": written,
        "failures": failures,
        "out": str(out),
        "model": model,
        "judge_id": judge_id,
        "prompt_style": prompt_style,
        "response_format": response_format_mode,
        "resume": resume,
    }
    if report_out:
        Path(report_out).parent.mkdir(parents=True, exist_ok=True)
        Path(report_out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompts", required=True, help="JSONL prompts created by prepare_llm_probe")
    parser.add_argument("--out", required=True, help="Output JSONL judgments")
    parser.add_argument("--model", required=True, help="OpenRouter model id, e.g. openai/gpt-4o-mini")
    parser.add_argument("--judge-id", required=True, help="Stable identifier for this judge run")
    parser.add_argument("--prompt-style", choices=sorted(SYSTEM_PROMPTS), default="strict")
    parser.add_argument("--response-format", choices=["json_object", "json_schema", "none"], default="json_object")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=1200)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    parser.add_argument("--referer", default=os.environ.get("OPENROUTER_HTTP_REFERER"))
    parser.add_argument("--title", default=os.environ.get("OPENROUTER_APP_TITLE", "LEMON-Factor Reliability Probe"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report-out", default=None)
    args = parser.parse_args()
    try:
        report = run_openrouter_judge(
            args.prompts,
            args.out,
            model=args.model,
            judge_id=args.judge_id,
            prompt_style=args.prompt_style,
            response_format_mode=args.response_format,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            limit=args.limit,
            resume=not args.no_resume,
            timeout=args.timeout,
            max_retries=args.max_retries,
            sleep_seconds=args.sleep_seconds,
            referer=args.referer,
            title=args.title,
            dry_run=args.dry_run,
            report_out=args.report_out,
        )
    except Exception as exc:  # pragma: no cover - CLI boundary
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(1) from exc
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
