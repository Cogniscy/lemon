"""Error analysis for low-coverage LEMON-Factor edges."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from lemon_factor.coverage.missing_analysis import read_details_jsonl


class CoverageErrorReport(BaseModel):
    total_edges: int
    low_coverage_edges: int
    threshold: float
    error_counts: dict[str, int]
    examples: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)

    def to_json_file(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")


def classify_edge_error(row: dict[str, Any], *, threshold: float = 0.5) -> str | None:
    score = float(row.get("score") or 0.0)
    if score >= threshold:
        return None
    if row.get("missing_decomposition"):
        return "missing_decomposition"
    if float(row.get("predicate_cue_score") or 0.0) == 0.0:
        return "missing_lexical_cue"
    if float(row.get("exact_label_score") or 0.0) < 0.5:
        return "entity_label_not_mentioned"
    components = row.get("components") or []
    if any(not component.get("covered") for component in components):
        return "relation_paraphrase_not_detected"
    return "overly_strict_factor"


def build_error_report(
    rows: list[dict[str, Any]],
    *,
    threshold: float = 0.5,
    max_examples_per_type: int = 5,
) -> CoverageErrorReport:
    counts: Counter[str] = Counter()
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        error_type = classify_edge_error(row, threshold=threshold)
        if error_type is None:
            continue
        counts[error_type] += 1
        if len(examples[error_type]) < max_examples_per_type:
            examples[error_type].append(
                {
                    "example_id": row.get("example_id"),
                    "predicate": row.get("predicate"),
                    "subject": row.get("subject"),
                    "object": row.get("object"),
                    "score": row.get("score"),
                    "exact_label_score": row.get("exact_label_score"),
                    "predicate_cue_score": row.get("predicate_cue_score"),
                }
            )
    return CoverageErrorReport(
        total_edges=len(rows),
        low_coverage_edges=sum(counts.values()),
        threshold=threshold,
        error_counts=dict(sorted(counts.items(), key=lambda item: (-item[1], item[0]))),
        examples=dict(examples),
    )


def write_error_table(report: CoverageErrorReport, path: str | Path) -> None:
    lines = ["| Error type | Count | Example |", "|---|---:|---|"]
    for error_type, count in report.error_counts.items():
        example = report.examples.get(error_type, [{}])[0]
        edge = "—"
        if example:
            edge = f"{example.get('subject')} — {example.get('predicate')} → {example.get('object')}"
        lines.append(f"| `{error_type}` | {count} | {edge} |")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("details", help="Edge-level coverage details JSONL")
    parser.add_argument("--out", required=True, help="Error analysis JSON report")
    parser.add_argument("--table", required=True, help="Markdown error table")
    parser.add_argument("--threshold", type=float, default=0.5)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    report = build_error_report(read_details_jsonl(args.details), threshold=args.threshold)
    report.to_json_file(args.out)
    write_error_table(report, args.table)
    print(json.dumps({"out": args.out, "table": args.table}, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
