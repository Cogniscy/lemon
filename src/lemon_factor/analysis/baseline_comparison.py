"""Compare LEMON-Factor coverage with simple graph-text baselines."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from lemon_factor.baselines.text_similarity import score_corpus_graph_text_similarity
from lemon_factor.datasets.unified_io import read_jsonl


METHOD_ROWS = [
    ("exact_label_coverage", "Exact entity-label overlap", "surface"),
    ("predicate_cue_coverage", "Predicate lexical cue coverage", "lexical_relation"),
    ("token_cosine", "Graph-text token cosine", "lexical_graph_text"),
    ("token_jaccard", "Graph-text token Jaccard", "lexical_graph_text"),
    ("lemon_factor_coverage", "LEMON-Factor coverage", "factor_semantic"),
]


def load_report(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _value(report: dict[str, Any], key: str) -> float:
    value = report.get(key, 0.0)
    if isinstance(value, (int, float)):
        return round(float(value), 6)
    return 0.0


def _delta(before: float | None, after: float | None) -> float | None:
    if before is None or after is None:
        return None
    return round(after - before, 6)


def build_comparison_report(
    examples: list[dict[str, Any]],
    baseline_report: dict[str, Any],
    expanded_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a method-comparison report for paper tables."""

    lexical = score_corpus_graph_text_similarity(examples)
    baseline_augmented = {**baseline_report, **{k: lexical[k] for k in ("token_jaccard", "token_cosine")}}
    expanded_augmented = None
    if expanded_report is not None:
        expanded_augmented = {**expanded_report, **{k: lexical[k] for k in ("token_jaccard", "token_cosine")}}

    rows: list[dict[str, Any]] = []
    for key, label, family in METHOD_ROWS:
        before = _value(baseline_augmented, key)
        after = _value(expanded_augmented, key) if expanded_augmented is not None else None
        rows.append(
            {
                "method": label,
                "metric_key": key,
                "family": family,
                "baseline_value": before,
                "expanded_value": after,
                "delta": _delta(before, after),
                "interpretation": method_interpretation(key),
            }
        )

    return {
        "examples": baseline_report.get("examples", len(examples)),
        "edges": baseline_report.get("edges", 0),
        "expanded_edges": expanded_report.get("edges", 0) if expanded_report else None,
        "rows": rows,
        "lexical_graph_text_baselines": {
            "token_jaccard": lexical["token_jaccard"],
            "token_cosine": lexical["token_cosine"],
        },
        "notes": [
            "Token baselines are lightweight lexical controls, not neural embedding metrics.",
            "LEMON-Factor expanded uses rule-based decomposition and lexical-cue expansion; it is not human gold.",
        ],
    }


def method_interpretation(key: str) -> str:
    if key == "exact_label_coverage":
        return "Checks whether entity labels are mentioned, but not whether relations are semantically covered."
    if key == "predicate_cue_coverage":
        return "Checks explicit relation lexical cues and is sensitive to cue dictionary coverage."
    if key == "token_cosine":
        return "Measures bag-of-words graph/text lexical similarity without role weighting."
    if key == "token_jaccard":
        return "Measures shared normalized graph/text tokens without term frequency or role structure."
    if key == "lemon_factor_coverage":
        return "Scores weighted role-aware semantic factors derived from source predicates."
    return ""


def write_comparison_table(report: dict[str, Any], path: str | Path) -> None:
    """Write a compact Markdown comparison table."""

    has_expanded = any(row.get("expanded_value") is not None for row in report["rows"])
    if has_expanded:
        lines = [
            "| Method | Family | Baseline | Expanded | Delta |",
            "|---|---|---:|---:|---:|",
        ]
        for row in report["rows"]:
            after = "—" if row["expanded_value"] is None else f"{row['expanded_value']:.4f}"
            delta = "—" if row["delta"] is None else f"{row['delta']:+.4f}"
            lines.append(
                f"| {row['method']} | {row['family']} | {row['baseline_value']:.4f} | {after} | {delta} |"
            )
    else:
        lines = ["| Method | Family | Value |", "|---|---|---:|"]
        for row in report["rows"]:
            lines.append(f"| {row['method']} | {row['family']} | {row['baseline_value']:.4f} |")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", help="Unified WebNLG dev JSONL")
    parser.add_argument("--baseline-report", required=True, help="Original LEMON-Factor coverage JSON")
    parser.add_argument("--expanded-report", default=None, help="Expanded LEMON-Factor coverage JSON")
    parser.add_argument("--out", required=True, help="Comparison report JSON")
    parser.add_argument("--table", required=True, help="Markdown table for paper")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    examples = [example.model_dump() for example in read_jsonl(args.jsonl)]
    baseline_report = load_report(args.baseline_report)
    expanded_report = load_report(args.expanded_report) if args.expanded_report else None
    report = build_comparison_report(examples, baseline_report, expanded_report)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_comparison_table(report, args.table)
    print(json.dumps({"out": args.out, "table": args.table}, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
