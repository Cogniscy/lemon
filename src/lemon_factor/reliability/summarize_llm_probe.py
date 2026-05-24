"""Summarize saved LLM factor-judgment outputs for reliability analysis."""

from __future__ import annotations

import argparse
import glob
import json
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

from lemon_factor.reliability.schema import LLMProbeItem, LLMProbeJudgment

_DECISION_TO_SCORE = {"absent": 0.0, "partial": 0.5, "covered": 1.0}


def _read_items(path: str | Path) -> dict[str, LLMProbeItem]:
    items: dict[str, LLMProbeItem] = {}
    with Path(path).open("r", encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                item = LLMProbeItem.model_validate_json(line)
            except Exception as exc:  # pragma: no cover
                raise ValueError(f"Invalid probe item at {path}:{line_no}") from exc
            items[item.id] = item
    return items


def _expand_judgment_paths(patterns: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        matched = glob.glob(pattern)
        if matched:
            paths.extend(Path(path) for path in matched)
        else:
            paths.append(Path(pattern))
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def _read_judgments(paths: list[str]) -> list[LLMProbeJudgment]:
    judgments: list[LLMProbeJudgment] = []
    for path in _expand_judgment_paths(paths):
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as stream:
            for line_no, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                try:
                    judgments.append(LLMProbeJudgment.model_validate_json(line))
                except Exception as exc:  # pragma: no cover
                    raise ValueError(f"Invalid judgment at {path}:{line_no}") from exc
    return judgments


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _deterministic_expected(item: LLMProbeItem, factor_id: str) -> str:
    factors = {factor.id: factor for factor in item.factors}
    factor = factors.get(factor_id)
    if factor is None:
        return "covered"
    targets = set(item.target_factor_groups)
    if factor.group in targets:
        return "absent"
    # Variant-level coarse mapping mirrors perturbation design.
    if item.variant == "node_deletion" and factor.group in {"participant_roles", "entity_presence"}:
        return "absent"
    if item.variant == "edge_deletion" and factor.group in {"predicate_meaning", "evidence_form"}:
        return "absent"
    if item.variant == "argument_swap" and factor.group in {"directionality", "participant_roles"}:
        return "absent"
    if item.variant == "polarity_flip" and factor.group in {"polarity", "predicate_meaning"}:
        return "absent"
    if item.variant == "relation_blur" and factor.group in {"predicate_specificity", "evidence_form", "predicate_meaning"}:
        return "partial"
    return "covered"


def _pairwise_agreement(decisions_by_judge: dict[str, dict[str, str]]) -> float | None:
    judge_ids = sorted(decisions_by_judge)
    if len(judge_ids) < 2:
        return None
    agreements: list[float] = []
    for left, right in combinations(judge_ids, 2):
        left_decisions = decisions_by_judge[left]
        right_decisions = decisions_by_judge[right]
        keys = sorted(set(left_decisions) & set(right_decisions))
        if not keys:
            continue
        agreements.append(sum(left_decisions[key] == right_decisions[key] for key in keys) / len(keys))
    return _mean(agreements)


def summarize(items_path: str | Path, judgment_paths: list[str], *, out: str | Path | None = None, examples_out: str | Path | None = None) -> dict[str, Any]:
    items = _read_items(items_path)
    judgments = _read_judgments(judgment_paths)
    if not judgments:
        report = {
            "status": "no_judgments",
            "item_count": len(items),
            "judgment_count": 0,
            "judge_count": 0,
            "summary": [],
            "deterministic_agreement": [],
            "examples": [],
        }
        if out:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            Path(out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report

    by_item: dict[str, list[LLMProbeJudgment]] = defaultdict(list)
    judges: set[str] = set()
    for judgment in judgments:
        if judgment.item_id in items:
            by_item[judgment.item_id].append(judgment)
            judges.add(judgment.judge_id)

    aggregate_rows: dict[tuple[str, str], list[float]] = defaultdict(list)
    pairwise_rows: dict[tuple[str, str], list[float]] = defaultdict(list)
    deterministic_rows: dict[tuple[str, str], list[float]] = defaultdict(list)
    examples: list[dict[str, Any]] = []

    for item_id, item_judgments in by_item.items():
        item = items[item_id]
        factor_ids = [factor.id for factor in item.factors]
        decisions_by_judge: dict[str, dict[str, str]] = {}
        for judgment in item_judgments:
            decisions_by_judge[judgment.judge_id] = {
                decision.factor_id: decision.decision for decision in judgment.decisions if decision.factor_id in factor_ids
            }
            for decision in judgment.decisions:
                if decision.factor_id in factor_ids:
                    aggregate_rows[(item.dataset, item.variant)].append(_DECISION_TO_SCORE[decision.decision])
                    expected = _deterministic_expected(item, decision.factor_id)
                    deterministic_rows[(item.dataset, item.variant)].append(float(decision.decision == expected))
        pair_agreement = _pairwise_agreement(decisions_by_judge)
        if pair_agreement is not None:
            pairwise_rows[(item.dataset, item.variant)].append(pair_agreement)

        if len(examples) < 25:
            disagreements: list[dict[str, Any]] = []
            for factor_id in factor_ids:
                votes = [judge_decisions.get(factor_id) for judge_decisions in decisions_by_judge.values() if factor_id in judge_decisions]
                if len(set(votes)) > 1:
                    disagreements.append({"factor_id": factor_id, "votes": votes})
            if disagreements:
                examples.append(
                    {
                        "item_id": item.id,
                        "dataset": item.dataset,
                        "variant": item.variant,
                        "edge": item.source_edge.model_dump(mode="json"),
                        "disagreements": disagreements[:5],
                    }
                )

    summary: list[dict[str, Any]] = []
    for key in sorted(aggregate_rows):
        dataset, variant = key
        summary.append(
            {
                "dataset": dataset,
                "variant": variant,
                "mean_llm_score": round(_mean(aggregate_rows[key]) or 0.0, 4),
                "pairwise_agreement": round(_mean(pairwise_rows.get(key, [])) or 0.0, 4) if pairwise_rows.get(key) else None,
                "deterministic_agreement": round(_mean(deterministic_rows.get(key, [])) or 0.0, 4) if deterministic_rows.get(key) else None,
                "factor_votes": len(aggregate_rows[key]),
            }
        )

    deterministic_agreement = [
        {
            "dataset": dataset,
            "variant": variant,
            "agreement": round(_mean(values) or 0.0, 4),
            "comparisons": len(values),
        }
        for (dataset, variant), values in sorted(deterministic_rows.items())
    ]

    report = {
        "status": "passed",
        "item_count": len(items),
        "judgment_count": len(judgments),
        "judge_count": len(judges),
        "summary": summary,
        "deterministic_agreement": deterministic_agreement,
        "examples": examples,
    }
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if examples_out:
        Path(examples_out).parent.mkdir(parents=True, exist_ok=True)
        lines = ["# LLM reliability disagreement examples", ""]
        if not examples:
            lines.append("No cross-judge disagreements were found in the provided judgments.\n")
        for example in examples:
            lines.extend(
                [
                    f"## {example['item_id']}",
                    f"Dataset: `{example['dataset']}`; variant: `{example['variant']}`.",
                    f"Edge: `{example['edge']['subject']} --{example['edge']['predicate']}--> {example['edge']['object']}`.",
                    "",
                    "| Factor | Votes |",
                    "|---|---|",
                ]
            )
            for disagreement in example["disagreements"]:
                votes = ", ".join(str(vote) for vote in disagreement["votes"])
                lines.append(f"| {disagreement['factor_id']} | {votes} |")
            lines.append("")
        Path(examples_out).write_text("\n".join(lines), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--items", required=True, help="Prepared probe items JSONL")
    parser.add_argument("--judgments", nargs="+", required=True, help="Judgment JSONL file(s) or glob patterns")
    parser.add_argument("--out", required=True, help="Summary JSON output")
    parser.add_argument("--examples-out", default=None, help="Optional Markdown disagreement examples")
    args = parser.parse_args()
    report = summarize(args.items, args.judgments, out=args.out, examples_out=args.examples_out)
    print(json.dumps({"out": args.out, "status": report["status"], "judgments": report["judgment_count"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
