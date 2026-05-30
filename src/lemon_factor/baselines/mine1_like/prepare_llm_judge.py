"""Prepare MINE-1-compatible LLM judge prompt payloads."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import read_jsonl, write_jsonl
from .prompts import build_prompt_payload


def prepare(items: str, out: str, *, model: str, judge_id: str, limit: int | None = None, top_k: int = 3, hops: int = 2) -> dict[str, object]:
    rows = read_jsonl(items)
    if limit is not None:
        rows = rows[:limit]
    payloads = [build_prompt_payload(item, model=model, judge_id=judge_id, top_k=top_k, hops=hops) for item in rows]
    write_jsonl(out, payloads)
    report = {"status": "passed", "items": len(payloads), "out": out, "model": model, "judge_id": judge_id, "top_k": top_k, "hops": hops}
    Path(out).with_suffix(".report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--model", default="google/gemini-2.0-flash-001")
    parser.add_argument("--judge-id", default="mine1_like_llm")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--hops", type=int, default=2)
    args = parser.parse_args()
    report = prepare(args.items, args.out, model=args.model, judge_id=args.judge_id, limit=args.limit, top_k=args.top_k, hops=args.hops)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
