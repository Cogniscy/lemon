"""Run saved LLM reliability probe prompts through OpenRouter.

This runner is intentionally separate from the deterministic LEMON scoring path.
It reads JSONL prompt payloads created by ``prepare_llm_probe`` and writes
schema-valid ``LLMProbeJudgment`` JSONL records that can be summarized later.

The runner is conservative by default: it uses non-streaming chat completion,
requests structured JSON, can enable OpenRouter response healing, logs raw
responses for debugging, retries failed items, and prints lightweight progress.
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import random
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
Return one valid JSON object only. Do not use Markdown. Do not add prose before or after the JSON.
For each factor, choose exactly one of: covered, partial, absent.
Use short evidence phrases only; do not provide chain-of-thought.""",
    "no_rationale": """You are a semantic-coverage judge for an NLP reliability study.
Decide whether each semantic factor from a source graph edge is supported by the perturbed text.
Use no outside knowledge. Return one valid JSON object only. Do not use Markdown.
Set evidence to null for every decision.""",
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


def build_messages(prompt_payload: dict[str, Any], *, prompt_style: str, judge_id: str | None = None) -> list[dict[str, str]]:
    if prompt_style not in SYSTEM_PROMPTS:
        raise ValueError(f"Unknown prompt style: {prompt_style}")
    factor_ids = [str(factor["id"]) for factor in prompt_payload.get("factors", []) if isinstance(factor, dict) and factor.get("id")]
    expected = {
        "item_id": prompt_payload.get("item_id"),
        "judge_id": judge_id or "<judge_id>",
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
        "output_contract": {
            "format": "Return exactly one valid JSON object. No Markdown. No surrounding text.",
            "must_include_all_factor_ids_in_this_order": factor_ids,
            "allowed_decisions": ["covered", "partial", "absent"],
            "expected_json_shape": expected,
        },
        "decision_rules": {
            "covered": "The perturbed text clearly supports the factor.",
            "partial": "The perturbed text weakly or ambiguously supports the factor.",
            "absent": "The perturbed text does not support the factor or contradicts it.",
        },
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
    judge_id: str | None = None,
    prompt_style: str,
    temperature: float,
    max_tokens: int,
    response_format_mode: str,
    json_healing: bool = True,
    require_parameters: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": build_messages(prompt_payload, prompt_style=prompt_style, judge_id=judge_id),
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    fmt = response_format(response_format_mode)
    if fmt is not None:
        payload["response_format"] = fmt
    if json_healing and response_format_mode != "none":
        payload["plugins"] = [{"id": "response-healing"}]
    if require_parameters and response_format_mode != "none":
        payload["provider"] = {"require_parameters": True}
    return payload


def _extract_message_content(response: dict[str, Any]) -> str:
    if "error" in response:
        raise ValueError(f"OpenRouter error response: {response['error']!r}")
    try:
        choice = response["choices"][0]
        message = choice["message"]
        content = message.get("content")
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"Unexpected OpenRouter response shape: {response!r}") from exc

    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, dict):
                text = part.get("text") or part.get("content")
                if isinstance(text, str):
                    parts.append(text)
            elif isinstance(part, str):
                parts.append(part)
        content = "\n".join(parts)
    if not isinstance(content, str) or not content.strip():
        finish_reason = choice.get("finish_reason") if isinstance(choice, dict) else None
        raise ValueError(f"OpenRouter response did not contain non-empty message content; finish_reason={finish_reason!r}")
    return content


def _strip_fences(text: str) -> str:
    text = text.strip().lstrip("\ufeff")
    if text.startswith("```"):
        text = re.sub(r"^```(?:json|JSON)?\s*", "", text).strip()
        text = re.sub(r"\s*```$", "", text).strip()
    return text


def _balanced_json_slice(text: str) -> str | None:
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    # Truncated response: return from the first object start so repair can try.
    return text[start:]


def repair_json_text(text: str) -> str:
    """Apply conservative repairs for common LLM JSON defects."""

    text = _strip_fences(text)
    sliced = _balanced_json_slice(text)
    if sliced is not None:
        text = sliced
    replacements = {
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r",\s*([}\]])", r"\1", text)
    # Missing comma between adjacent objects or arrays is a common model error.
    text = re.sub(r"}\s*{", "},{", text)
    text = re.sub(r"\]\s*\"", "],\"", text)
    text = re.sub(r"}\s*\"", "},\"", text)
    return text.strip()


def extract_json_object(text: str) -> dict[str, Any]:
    """Extract one JSON object from a model response, with local repair fallback."""

    candidates = [_strip_fences(text), repair_json_text(text)]
    balanced = _balanced_json_slice(_strip_fences(text))
    if balanced:
        candidates.append(balanced)
        candidates.append(repair_json_text(balanced))

    errors: list[str] = []
    for candidate in candidates:
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError as exc:
            errors.append(str(exc))

    raise ValueError("Could not parse JSON object from model response after repair attempts: " + "; ".join(errors[-3:]))


def _normalise_decisions(raw: dict[str, Any], prompt_payload: dict[str, Any], *, judge_id: str, model: str, prompt_style: str) -> LLMProbeJudgment:
    item_id = str(prompt_payload.get("item_id") or raw.get("item_id") or "")
    factor_ids = [str(factor["id"]) for factor in prompt_payload.get("factors", []) if isinstance(factor, dict) and factor.get("id")]
    factor_set = set(factor_ids)
    raw_decisions = raw.get("decisions")
    if isinstance(raw_decisions, dict):
        raw_decisions = [
            {"factor_id": factor_id, **(value if isinstance(value, dict) else {"decision": value})}
            for factor_id, value in raw_decisions.items()
        ]
    if not isinstance(raw_decisions, list):
        raise ValueError("Judgment JSON has no decisions list")

    decisions_by_factor: dict[str, FactorJudgment] = {}
    for decision in raw_decisions:
        if not isinstance(decision, dict):
            continue
        factor_id = str(decision.get("factor_id") or decision.get("id") or "")
        if factor_id not in factor_set:
            continue
        label = str(decision.get("decision") or decision.get("coverage") or decision.get("status") or "").casefold().strip()
        label = {"yes": "covered", "no": "absent", "true": "covered", "false": "absent", "present": "covered", "missing": "absent"}.get(label, label)
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
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - explicit user-supplied API endpoint
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise ValueError(f"OpenRouter HTTP {exc.code}: {body[:1200]}") from exc
    except (http.client.IncompleteRead, TimeoutError, OSError) as exc:
        raise TimeoutError(f"OpenRouter transport/read failure: {exc}") from exc
    parsed = json.loads(body)
    if not isinstance(parsed, dict):
        raise ValueError("OpenRouter returned non-object JSON")
    return parsed


def _iter_prompts(
    prompts: Iterable[dict[str, Any]],
    *,
    limit: int | None,
    completed: set[str],
    offset: int = 0,
    dataset: str | None = None,
    variant: str | None = None,
    shuffle: bool = False,
    seed: int = 13,
) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for payload in prompts:
        item_id = str(payload.get("item_id") or "")
        if item_id in completed:
            continue
        if dataset and str(payload.get("dataset")) != dataset:
            continue
        if variant and str(payload.get("variant")) != variant:
            continue
        filtered.append(payload)
    if shuffle:
        random.Random(seed).shuffle(filtered)
    if offset:
        filtered = filtered[offset:]
    if limit is not None:
        filtered = filtered[:limit]
    return filtered


def _append_jsonl(path: str | Path | None, record: dict[str, Any]) -> None:
    if not path:
        return
    raw_path = Path(path)
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with raw_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def _write_report(path: str | Path | None, report: dict[str, Any]) -> None:
    if not path:
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


def _progress(index: int, total: int, *, written: int, failed: int, item_id: str, start_time: float) -> str:
    width = 24
    filled = int(width * index / total) if total else width
    bar = "█" * filled + "░" * (width - filled)
    elapsed = time.time() - start_time
    rate = index / elapsed if elapsed > 0 else 0.0
    eta = (total - index) / rate if rate > 0 else 0.0
    return f"[{bar}] {index}/{total} ok={written} fail={failed} eta={eta:5.1f}s item={item_id[:60]}"


def run_openrouter_judge(
    prompts_path: str | Path,
    out: str | Path,
    *,
    model: str,
    judge_id: str,
    prompt_style: str = "strict",
    response_format_mode: str = "json_schema",
    fallback_response_format_mode: str = "json_object",
    temperature: float = 0.0,
    max_tokens: int = 1200,
    limit: int | None = None,
    offset: int = 0,
    dataset: str | None = None,
    variant: str | None = None,
    shuffle: bool = False,
    seed: int = 13,
    resume: bool = True,
    timeout: float = 45.0,
    max_retries: int = 3,
    sleep_seconds: float = 0.0,
    api_key: str | None = None,
    referer: str | None = None,
    title: str | None = "LEMON-Factor Reliability Probe",
    json_healing: bool = True,
    require_parameters: bool = False,
    raw_out: str | Path | None = None,
    dry_run: bool = False,
    report_out: str | Path | None = None,
    progress: bool = True,
) -> dict[str, Any]:
    api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not dry_run and not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    prompts = _read_jsonl(prompts_path)
    completed = _completed_item_ids(out) if resume else set()
    selected = _iter_prompts(
        prompts,
        limit=limit,
        completed=completed,
        offset=offset,
        dataset=dataset,
        variant=variant,
        shuffle=shuffle,
        seed=seed,
    )
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)

    if dry_run:
        request_example = build_request_payload(
            selected[0] if selected else (prompts[0] if prompts else {}),
            model=model,
            judge_id=judge_id,
            prompt_style=prompt_style,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format_mode=response_format_mode,
            json_healing=json_healing,
            require_parameters=require_parameters,
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
            "json_healing": json_healing,
            "require_parameters": require_parameters,
            "request_example": request_example,
        }
        _write_report(report_out, report)
        return report

    written = 0
    failures: list[dict[str, Any]] = []
    mode = "a" if resume else "w"
    start_time = time.time()
    with path.open(mode, encoding="utf-8") as stream:
        for index, prompt_payload in enumerate(selected, start=1):
            last_error: str | None = None
            used_format = response_format_mode
            for attempt in range(1, max_retries + 1):
                # Fallback from strict schema to more widely supported JSON mode on later attempts.
                attempt_format = response_format_mode
                if attempt > 1 and fallback_response_format_mode != response_format_mode:
                    attempt_format = fallback_response_format_mode
                request_payload = build_request_payload(
                    prompt_payload,
                    model=model,
                    judge_id=judge_id,
                    prompt_style=prompt_style,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format_mode=attempt_format,
                    json_healing=json_healing,
                    require_parameters=require_parameters,
                )
                try:
                    response = _post_openrouter(request_payload, api_key=api_key or "", timeout=timeout, referer=referer, title=title)
                    raw_content = None
                    try:
                        raw_content = _extract_message_content(response)
                    except Exception:
                        raw_content = None
                    judgment = parse_judgment_from_response(response, prompt_payload, judge_id=judge_id, model=model, prompt_style=prompt_style)
                    stream.write(json.dumps(judgment.model_dump(mode="json"), ensure_ascii=False) + "\n")
                    stream.flush()
                    written += 1
                    used_format = attempt_format
                    _append_jsonl(
                        raw_out,
                        {
                            "item_id": prompt_payload.get("item_id"),
                            "attempt": attempt,
                            "status": "passed",
                            "response_format": attempt_format,
                            "raw_content": raw_content,
                        },
                    )
                    last_error = None
                    break
                except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError, OSError) as exc:
                    last_error = str(exc)
                    _append_jsonl(
                        raw_out,
                        {
                            "item_id": prompt_payload.get("item_id"),
                            "attempt": attempt,
                            "status": "failed",
                            "response_format": attempt_format,
                            "error": last_error,
                        },
                    )
                    if attempt < max_retries:
                        time.sleep(min(2 ** (attempt - 1), 8))
            if last_error:
                failures.append({"item_id": prompt_payload.get("item_id"), "error": last_error})
            if progress:
                print(
                    "\r" + _progress(index, len(selected), written=written, failed=len(failures), item_id=str(prompt_payload.get("item_id") or ""), start_time=start_time),
                    end="",
                    file=sys.stderr,
                    flush=True,
                )
            running_report = {
                "status": "running",
                "prompts_total": len(prompts),
                "prompts_selected": len(selected),
                "processed": index,
                "judgments_written": written,
                "failures": failures,
                "out": str(out),
                "model": model,
                "judge_id": judge_id,
                "prompt_style": prompt_style,
                "response_format": response_format_mode,
                "fallback_response_format": fallback_response_format_mode,
                "last_response_format": used_format,
                "resume": resume,
            }
            _write_report(report_out, running_report)
            if sleep_seconds and index < len(selected):
                time.sleep(sleep_seconds)
    if progress:
        print(file=sys.stderr)

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
        "fallback_response_format": fallback_response_format_mode,
        "json_healing": json_healing,
        "require_parameters": require_parameters,
        "resume": resume,
        "elapsed_seconds": round(time.time() - start_time, 3),
    }
    _write_report(report_out, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompts", required=True, help="JSONL prompts created by prepare_llm_probe")
    parser.add_argument("--out", required=True, help="Output JSONL judgments")
    parser.add_argument("--model", required=True, help="OpenRouter model id, e.g. google/gemini-2.0-flash-001")
    parser.add_argument("--judge-id", required=True, help="Stable identifier for this judge run")
    parser.add_argument("--prompt-style", choices=sorted(SYSTEM_PROMPTS), default="strict")
    parser.add_argument("--response-format", choices=["json_object", "json_schema", "none"], default="json_schema")
    parser.add_argument("--fallback-response-format", choices=["json_object", "json_schema", "none"], default="json_object")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=1200)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--dataset", default=None)
    parser.add_argument("--variant", default=None)
    parser.add_argument("--shuffle", action="store_true")
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--timeout", type=float, default=45.0)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    parser.add_argument("--referer", default=os.environ.get("OPENROUTER_HTTP_REFERER"))
    parser.add_argument("--title", default=os.environ.get("OPENROUTER_APP_TITLE", "LEMON-Factor Reliability Probe"))
    parser.add_argument("--no-json-healing", action="store_true")
    parser.add_argument("--require-parameters", action="store_true")
    parser.add_argument("--raw-out", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report-out", default=None)
    parser.add_argument("--no-progress", action="store_true")
    args = parser.parse_args()
    try:
        report = run_openrouter_judge(
            args.prompts,
            args.out,
            model=args.model,
            judge_id=args.judge_id,
            prompt_style=args.prompt_style,
            response_format_mode=args.response_format,
            fallback_response_format_mode=args.fallback_response_format,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            limit=args.limit,
            offset=args.offset,
            dataset=args.dataset,
            variant=args.variant,
            shuffle=args.shuffle,
            seed=args.seed,
            resume=not args.no_resume,
            timeout=args.timeout,
            max_retries=args.max_retries,
            sleep_seconds=args.sleep_seconds,
            referer=args.referer,
            title=args.title,
            json_healing=not args.no_json_healing,
            require_parameters=args.require_parameters,
            raw_out=args.raw_out,
            dry_run=args.dry_run,
            report_out=args.report_out,
            progress=not args.no_progress,
        )
    except Exception as exc:  # pragma: no cover - CLI boundary
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        raise SystemExit(1) from exc
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
