"""CLI for deterministic LEMON-Factor coverage on WebNLG GraphText JSONL."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lemon_factor.coverage.graphtext_coverage import score_corpus_coverage, write_coverage_outputs
from lemon_factor.datasets.unified_io import read_jsonl
from lemon_factor.factors.decomposition import PredicateDecompositionSet


def load_lexical_cues(path: str | Path | None) -> dict[str, list[str]]:
    if path is None:
        return {}
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return {str(key): [str(item) for item in value] for key, value in raw.items()}


def write_markdown_table(report_path: str | Path, table_path: str | Path) -> None:
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    lines = [
        "| Metric | Value |",
        "|---|---:|",
        f"| Examples | {report['examples']} |",
        f"| Edges | {report['edges']} |",
        f"| Scored edges | {report['scored_edges']} |",
        f"| Missing decomposition rate | {report['missing_decomposition_rate']:.4f} |",
        f"| Exact label coverage | {report['exact_label_coverage']:.4f} |",
        f"| Predicate cue coverage | {report['predicate_cue_coverage']:.4f} |",
        f"| LEMON-Factor coverage | {report['lemon_factor_coverage']:.4f} |",
        f"| Low coverage edges | {report['low_coverage_edge_count']} |",
    ]
    table_path = Path(table_path)
    table_path.parent.mkdir(parents=True, exist_ok=True)
    table_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", help="Unified WebNLG dev JSONL")
    parser.add_argument("--decompositions", required=True, help="PredicateDecompositionSet JSON")
    parser.add_argument("--lexical-cues", default=None, help="Optional lexical cues JSON")
    parser.add_argument("--out", required=True, help="Corpus coverage JSON report")
    parser.add_argument("--details", required=True, help="Edge-level JSONL details")
    parser.add_argument("--table", required=True, help="Markdown table for paper")
    parser.add_argument("--low-coverage-threshold", type=float, default=0.5)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    examples = read_jsonl(args.jsonl)
    decompositions = PredicateDecompositionSet.from_json_file(args.decompositions)
    lexical_cues = load_lexical_cues(args.lexical_cues)
    report, example_results, edge_results = score_corpus_coverage(
        examples,
        decompositions,
        lexical_cues,
        low_coverage_threshold=args.low_coverage_threshold,
    )
    write_coverage_outputs(report, example_results, edge_results, out=args.out, details=args.details)
    write_markdown_table(args.out, args.table)
    print(
        json.dumps(
            {"out": args.out, "details": args.details, "table": args.table},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()
