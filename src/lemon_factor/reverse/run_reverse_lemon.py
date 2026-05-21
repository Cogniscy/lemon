"""Run reverse LEMON-Factor on reconstructed text-to-KG graphs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lemon_factor.datasets.unified_io import read_jsonl
from lemon_factor.factors.decomposition import PredicateDecompositionSet
from lemon_factor.reverse.reconstruct_graph import read_reconstructed_graphs
from lemon_factor.reverse.reverse_coverage import score_reverse_corpus, write_reverse_outputs


def write_reverse_table(report: dict[str, object], path: str | Path) -> None:
    lines = [
        "| Metric | Value |",
        "|---|---:|",
        f"| Examples | {report['examples']} |",
        f"| Edges | {report['edges']} |",
        f"| Recovered edges | {report['recovered_edges']} |",
        f"| Edge recovery rate | {float(report['edge_recovery_rate']):.4f} |",
        f"| Node recovery score | {float(report['node_recovery_score']):.4f} |",
        f"| Reverse LEMON-Factor coverage | {float(report['reverse_lemon_coverage']):.4f} |",
        f"| Missing decompositions | {report['missing_decompositions']} |",
    ]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", help="Unified GraphText JSONL")
    parser.add_argument("--reconstructed", required=True, help="Reconstructed graph JSONL")
    parser.add_argument("--decompositions", required=True, help="Predicate decompositions JSON")
    parser.add_argument("--out", required=True, help="Reverse LEMON report JSON")
    parser.add_argument("--details", required=True, help="Edge-level reverse LEMON details JSONL")
    parser.add_argument("--table", required=True, help="Markdown table")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    examples = read_jsonl(args.jsonl)
    records = read_reconstructed_graphs(args.reconstructed)
    decompositions = PredicateDecompositionSet.from_json_file(args.decompositions)
    report, example_results, edge_results = score_reverse_corpus(examples, records, decompositions)
    write_reverse_outputs(report, example_results, edge_results, out=args.out, details=args.details)
    write_reverse_table(report.model_dump(mode="json"), args.table)
    print(json.dumps({"out": args.out, "details": args.details, "table": args.table}, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
