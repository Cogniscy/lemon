"""Score prepared MINE-1-compatible items.

Modes:
* lexical: deterministic retrieval + lexical binary judge.
* llm_saved: retrieval + saved binary LLM judgments.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import parse_recoverability_judgment, read_jsonl, score_item, score_item_with_judgment, summarize_scores, write_jsonl


def _judgment_map(path: str) -> dict[str, dict[str, object]]:
    mapping: dict[str, dict[str, object]] = {}
    for row in read_jsonl(path):
        parsed = parse_recoverability_judgment(row)
        mapping[str(parsed["item_id"])] = parsed
    return mapping


def score(
    items_path: str,
    out: str,
    scores_out: str | None = None,
    mode: str = "lexical",
    top_k: int = 3,
    hops: int = 2,
    judgments: str | None = None,
) -> dict[str, object]:
    items = read_jsonl(items_path)
    if mode == "lexical":
        rows = [score_item(item, top_k=top_k, hops=hops) for item in items]
    elif mode == "llm_saved":
        if not judgments:
            raise ValueError("--judgments is required for --mode llm_saved")
        by_id = _judgment_map(judgments)
        rows = []
        missing: list[str] = []
        for item in items:
            item_id = str(item.get("id"))
            judgment = by_id.get(item_id)
            if judgment is None:
                missing.append(item_id)
                continue
            rows.append(score_item_with_judgment(item, judgment, top_k=top_k, hops=hops))
        if missing:
            # Missing judgments are allowed for pilot runs but are explicitly reported.
            pass
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    summary = summarize_scores(rows)
    report = {"status": "passed", "mode": mode, "top_k": top_k, "hops": hops, **summary}
    if mode == "llm_saved":
        report["judgments"] = judgments
        report["items_requested"] = len(items)
        report["items_scored"] = len(rows)
        report["items_missing_judgment"] = len(items) - len(rows)
    target = Path(out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")
    if scores_out:
        write_jsonl(scores_out, rows)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--scores-out", default=None)
    parser.add_argument("--mode", choices=["lexical", "llm_saved"], default="lexical")
    parser.add_argument("--judgments", default=None)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--hops", type=int, default=2)
    args = parser.parse_args()
    report = score(args.items, args.out, scores_out=args.scores_out, mode=args.mode, judgments=args.judgments, top_k=args.top_k, hops=args.hops)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
