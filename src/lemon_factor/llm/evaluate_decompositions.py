"""Evaluate LLM predicate decompositions against seed/reference decompositions."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from lemon_factor.factors.decomposition import PredicateDecompositionSet
from lemon_factor.llm.schema import LLMDecompositionRecord, read_llm_records


def _factor_set(record: LLMDecompositionRecord | Any) -> set[str]:
    if isinstance(record, LLMDecompositionRecord):
        return {component.factor for component in record.decomposition.components}
    return {component.factor for component in record.components}


def _factor_role_set(record: LLMDecompositionRecord | Any) -> set[tuple[str, str]]:
    if isinstance(record, LLMDecompositionRecord):
        return {(component.factor, component.role) for component in record.decomposition.components}
    return {(component.factor, component.role) for component in record.components}


def _weights_by_factor(record: LLMDecompositionRecord | Any) -> dict[str, float]:
    if isinstance(record, LLMDecompositionRecord):
        components = record.decomposition.components
    else:
        components = record.components
    return {component.factor: component.weight for component in components}


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def score_decomposition(
    candidate: LLMDecompositionRecord,
    reference_set: PredicateDecompositionSet,
) -> dict[str, Any]:
    """Score one LLM decomposition against a reference decomposition."""

    reference = reference_set.decompositions[candidate.predicate]
    predicted_factors = _factor_set(candidate)
    reference_factors = _factor_set(reference)
    matched_factors = predicted_factors & reference_factors
    precision = _safe_div(len(matched_factors), len(predicted_factors))
    recall = _safe_div(len(matched_factors), len(reference_factors))
    f1 = _safe_div(2 * precision * recall, precision + recall)

    predicted_roles = _factor_role_set(candidate)
    reference_roles = _factor_role_set(reference)
    matched_roles = predicted_roles & reference_roles
    role_accuracy = _safe_div(len(matched_roles), len(reference_roles))

    predicted_weights = _weights_by_factor(candidate)
    reference_weights = _weights_by_factor(reference)
    shared = sorted(reference_factors | predicted_factors)
    weight_mae = mean(
        abs(predicted_weights.get(factor, 0.0) - reference_weights.get(factor, 0.0))
        for factor in shared
    ) if shared else 0.0

    return {
        "model": candidate.model,
        "predicate": candidate.predicate,
        "factor_precision": round(precision, 6),
        "factor_recall": round(recall, 6),
        "factor_f1": round(f1, 6),
        "role_accuracy": round(role_accuracy, 6),
        "weight_mae": round(weight_mae, 6),
        "predicted_factors": sorted(predicted_factors),
        "reference_factors": sorted(reference_factors),
    }


def aggregate_scores(scores: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate scores by model."""

    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for score in scores:
        by_model[score["model"]].append(score)
    payload: dict[str, Any] = {"models": {}, "items": scores}
    for model, items in sorted(by_model.items()):
        payload["models"][model] = {
            "items": len(items),
            "factor_precision": round(mean(item["factor_precision"] for item in items), 6),
            "factor_recall": round(mean(item["factor_recall"] for item in items), 6),
            "factor_f1": round(mean(item["factor_f1"] for item in items), 6),
            "role_accuracy": round(mean(item["role_accuracy"] for item in items), 6),
            "weight_mae": round(mean(item["weight_mae"] for item in items), 6),
        }
    return payload


def evaluate_records(
    records: list[LLMDecompositionRecord],
    reference_set: PredicateDecompositionSet,
) -> dict[str, Any]:
    """Evaluate all records that have a matching reference predicate."""

    scores = [
        score_decomposition(record, reference_set)
        for record in records
        if record.predicate in reference_set.decompositions
    ]
    result = aggregate_scores(scores)
    result["records_total"] = len(records)
    result["records_scored"] = len(scores)
    return result


def write_markdown_table(result: dict[str, Any], path: str | Path) -> None:
    """Write model-level evaluation table."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "| Model | Items | Factor precision | Factor recall | Factor F1 | Role accuracy | Weight MAE |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for model, stats in sorted(result["models"].items()):
        lines.append(
            f"| {model} | {stats['items']} | {stats['factor_precision']:.3f} | "
            f"{stats['factor_recall']:.3f} | {stats['factor_f1']:.3f} | "
            f"{stats['role_accuracy']:.3f} | {stats['weight_mae']:.3f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_review_csv(result: dict[str, Any], path: str | Path) -> None:
    """Write item-level CSV for expert review."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "model",
        "predicate",
        "factor_f1",
        "role_accuracy",
        "weight_mae",
        "predicted_factors",
        "reference_factors",
        "expert_accept",
        "expert_notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for item in result["items"]:
            writer.writerow(
                {
                    "model": item["model"],
                    "predicate": item["predicate"],
                    "factor_f1": item["factor_f1"],
                    "role_accuracy": item["role_accuracy"],
                    "weight_mae": item["weight_mae"],
                    "predicted_factors": "; ".join(item["predicted_factors"]),
                    "reference_factors": "; ".join(item["reference_factors"]),
                    "expert_accept": "",
                    "expert_notes": "",
                }
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidates")
    parser.add_argument("reference")
    parser.add_argument("--out", default="data/reports/llm_decomposition_eval.json")
    parser.add_argument("--table", default="paper/tables/table_llm_decomposition_eval.md")
    parser.add_argument("--review-out", default="data/annotation/llm_decomposition_review.csv")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = read_llm_records(args.candidates)
    reference_set = PredicateDecompositionSet.from_json_file(args.reference)
    result = evaluate_records(records, reference_set)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_table(result, args.table)
    write_review_csv(result, args.review_out)
    print(json.dumps({"out": args.out, "table": args.table, "review": args.review_out}, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
