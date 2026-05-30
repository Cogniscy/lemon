"""Run MINE-1-compatible LLM judge payloads through OpenRouter.

The command expects prompt payloads from prepare_llm_judge.py and writes one
normalized judgment JSON object per line. It uses only the Python standard
library to keep the patch dependency-light.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request

from .core import read_jsonl, write_jsonl

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def _extract_json_content(response: dict[str, object]) -> str:
    choices = response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("OpenRouter response has no choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict):
        raise ValueError("OpenRouter response has no message")
    content = message.get("content")
    if isinstance(content, list):
        content = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)
    if not isinstance(content, str) or not content.strip():
        raise ValueError("OpenRouter response has empty content")
    return content.strip()


def _post(payload: dict[str, object], api_key: str, timeout: int) -> dict[str, object]:
    body = {
        "model": payload.get("model"),
        "messages": payload.get("messages"),
        "response_format": payload.get("response_format"),
        "temperature": 0,
        "plugins": [{"id": "response-healing"}],
    }
    data = json.dumps(body).encode("utf8")
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=data,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - user-provided endpoint intentionally used
        return json.loads(resp.read().decode("utf8"))


def run(prompts: str, out: str, *, limit: int | None = None, timeout: int = 60, max_retries: int = 3, dry_run: bool = False) -> dict[str, object]:
    payloads = read_jsonl(prompts)
    if limit is not None:
        payloads = payloads[:limit]
    rows: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not dry_run and not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required unless --dry-run is set")

    for i, payload in enumerate(payloads, start=1):
        item_id = str(payload.get("item_id"))
        if dry_run:
            rows.append({"item_id": item_id, "recoverable": False, "confidence": 0.0, "evidence": "dry_run", "judge_id": payload.get("judge_id"), "model": payload.get("model")})
            continue
        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                raw = _post(payload, api_key, timeout)
                content = _extract_json_content(raw)
                parsed = json.loads(content)
                parsed.setdefault("item_id", item_id)
                parsed.setdefault("judge_id", payload.get("judge_id"))
                parsed.setdefault("model", payload.get("model"))
                rows.append(parsed)
                break
            except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
                last_error = str(exc)
                time.sleep(min(2 * attempt, 8))
        else:
            failures.append({"item_id": item_id, "error": last_error})
        print(f"[{i}/{len(payloads)}] ok={len(rows)} fail={len(failures)} item={item_id}", flush=True)

    write_jsonl(out, rows)
    report = {"status": "passed" if not failures else "partial", "prompts": len(payloads), "judgments": len(rows), "failures": failures, "out": out}
    Path(out).with_suffix(".report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompts", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    report = run(args.prompts, args.out, limit=args.limit, timeout=args.timeout, max_retries=args.max_retries, dry_run=args.dry_run)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
