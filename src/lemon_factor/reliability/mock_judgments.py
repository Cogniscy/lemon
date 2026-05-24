"""Create deterministic mock judgments for testing the reliability pipeline.

This command is not a substitute for LLM judging. It creates schema-valid sample
judgments from perturbation metadata so that the summarizer and downstream
reports can be tested offline.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lemon_factor.reliability.prepare_llm_probe import factor_group
from lemon_factor.reliability.schema import LLMProbeItem, LLMProbeJudgment, FactorJudgment


def _decision(item: LLMProbeItem, factor_group_name: str, judge_id: str) -> str:
    targets = set(item.target_factor_groups)
    if factor_group_name in targets:
        return "absent" if judge_id != "mock_lenient" else "partial"
    if item.variant == "relation_blur" and factor_group_name in {"predicate_meaning", "evidence_form"}:
        return "partial"
    if item.variant == "polarity_flip" and factor_group_name == "polarity":
        return "absent"
    return "covered"


def make_mock_judgments(items_path: str | Path, out: str | Path, *, judge_id: str = "mock_strict", limit: int | None = None) -> dict:
    items: list[LLMProbeItem] = []
    with Path(items_path).open("r", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                items.append(LLMProbeItem.model_validate_json(line))
    if limit is not None:
        items = items[:limit]

    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as stream:
        for item in items:
            decisions = []
            for factor in item.factors:
                group = factor.group or factor_group(factor.id, factor.role)
                decisions.append(
                    FactorJudgment(
                        factor_id=factor.id,
                        decision=_decision(item, group, judge_id),
                        confidence=0.8,
                        evidence=None,
                    )
                )
            judgment = LLMProbeJudgment(item_id=item.id, judge_id=judge_id, decisions=decisions, notes="Offline mock judgment for pipeline testing.")
            stream.write(json.dumps(judgment.model_dump(mode="json"), ensure_ascii=False) + "\n")
            count += 1
    return {"status": "passed", "out": str(out), "judge_id": judge_id, "judgments": count}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--judge-id", default="mock_strict")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    report = make_mock_judgments(args.items, args.out, judge_id=args.judge_id, limit=args.limit)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
