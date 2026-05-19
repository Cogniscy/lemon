"""Run expanded LEMON-Factor coverage and write before/after delta table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from lemon_factor.coverage.graphtext_coverage import score_corpus_coverage, write_coverage_outputs
from lemon_factor.coverage.run_webnlg_coverage import load_lexical_cues
from lemon_factor.datasets.unified_io import read_jsonl
from lemon_factor.factors.decomposition import PredicateDecompositionSet

DELTA_KEYS = [
    "scored_edges",
    "missing_decomposition_rate",
    "exact_label_coverage",
    "predicate_cue_coverage",
    "lemon_factor_coverage",
    "low_coverage_edge_count",
]


def _load_report(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _delta_value(before: Any, after: Any) -> Any:
    if isinstance(before, (int, float)) and isinstance(after, (int, float)):
        return round(after - before, 6)
    return "—"


def write_delta_table(before: dict[str, Any], after: dict[str, Any], path: str | Path) -> None:
    lines = ["| Metric | Before | After | Delta |", "|---|---:|---:|---:|"]
    for key in DELTA_KEYS:
        b = before.get(key, 0)
        a = after.get(key, 0)
        d = _delta_value(b, a)
        label = key.replace("_", " ").title()
        lines.append(f"| {label} | {b} | {a} | {d} |")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", help="Unified WebNLG dev JSONL")
    parser.add_argument("--before", required=True, help="Baseline coverage JSON report")
    parser.add_argument("--expanded-decompositions", required=True, help="Expanded PredicateDecompositionSet JSON")
    parser.add_argument("--expanded-lexical-cues", required=True, help="Expanded lexical cues JSON")
    parser.add_argument("--out", required=True, help="Expanded coverage JSON report")
    parser.add_argument("--details", required=True, help="Expanded edge-level JSONL details")
    parser.add_argument("--table", required=True, help="Before/after markdown delta table")
    parser.add_argument("--low-coverage-threshold", type=float, default=0.5)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    examples = read_jsonl(args.jsonl)
    decompositions = PredicateDecompositionSet.from_json_file(args.expanded_decompositions)
    lexical_cues = load_lexical_cues(args.expanded_lexical_cues)
    report, example_results, edge_results = score_corpus_coverage(
        examples,
        decompositions,
        lexical_cues,
        low_coverage_threshold=args.low_coverage_threshold,
    )
    write_coverage_outputs(report, example_results, edge_results, out=args.out, details=args.details)
    before = _load_report(args.before)
    after = _load_report(args.out)
    write_delta_table(before, after, args.table)
    print(json.dumps({"out": args.out, "details": args.details, "table": args.table}, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
