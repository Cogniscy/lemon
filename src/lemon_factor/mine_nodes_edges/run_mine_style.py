"""Run deterministic MINE-style node/edge information retention on WebNLG."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lemon_factor.datasets.unified_io import read_jsonl
from lemon_factor.mine_nodes_edges.scoring import score_mine_style_corpus, write_mine_style_outputs
from lemon_factor.reverse.reconstruct_graph import read_reconstructed_graphs


def write_mine_style_table(report: dict[str, object], path: str | Path) -> None:
    lines = [
        "| Metric | Value |",
        "|---|---:|",
        f"| Examples | {report['examples']} |",
        f"| Facts | {report['facts']} |",
        f"| Node information | {float(report['node_information']):.4f} |",
        f"| Edge information | {float(report['edge_information']):.4f} |",
        f"| Retrieved edge hit rate | {float(report['retrieved_edge_hit_rate']):.4f} |",
        f"| Fact recoverability | {float(report['fact_recoverability']):.4f} |",
        f"| MINE-style score | {float(report['mine_style_score']):.4f} |",
    ]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", help="Unified GraphText JSONL")
    parser.add_argument("--reconstructed", required=True, help="Reconstructed graph JSONL")
    parser.add_argument("--out", required=True, help="MINE-style report JSON")
    parser.add_argument("--scores", required=True, help="Fact-level MINE-style scores JSONL")
    parser.add_argument("--table", required=True, help="Markdown table")
    parser.add_argument("--top-k", type=int, default=2, help="Retrieved nodes per fact")
    parser.add_argument("--hops", type=int, default=2, help="Subgraph expansion hops")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    examples = read_jsonl(args.jsonl)
    records = read_reconstructed_graphs(args.reconstructed)
    report, scores = score_mine_style_corpus(examples, records, top_k=args.top_k, hops=args.hops)
    write_mine_style_outputs(report, scores, out=args.out, scores_path=args.scores)
    write_mine_style_table(report.model_dump(mode="json"), args.table)
    print(json.dumps({"out": args.out, "scores": args.scores, "table": args.table}, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
