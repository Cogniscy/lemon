"""Compare forward LEMON, reverse LEMON, and MINE-style text-to-KG scores."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_bidirectional_comparison(
    *,
    forward: dict[str, Any],
    reverse: dict[str, Any],
    mine_style: dict[str, Any],
    baseline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rows = [
        {
            "method": "Forward LEMON-Factor",
            "direction": "KG→Text",
            "uses_factors": True,
            "uses_retrieval": False,
            "uses_llm_judge": False,
            "score_key": "lemon_factor_coverage",
            "score": round(float(forward.get("lemon_factor_coverage", 0.0)), 6),
            "diagnostic_level": "factor/edge/example/corpus",
            "interpretation": "Checks whether gold graph predicate factors are covered by text.",
        },
        {
            "method": "Reverse LEMON-Factor",
            "direction": "Text→KG",
            "uses_factors": True,
            "uses_retrieval": False,
            "uses_llm_judge": False,
            "score_key": "reverse_lemon_coverage",
            "score": round(float(reverse.get("reverse_lemon_coverage", 0.0)), 6),
            "diagnostic_level": "factor/edge/example/corpus",
            "interpretation": "Checks whether reconstructed graph retains gold predicate factors.",
        },
        {
            "method": "MINE-style nodes/edges",
            "direction": "Text→KG",
            "uses_factors": False,
            "uses_retrieval": True,
            "uses_llm_judge": False,
            "score_key": "mine_style_score",
            "score": round(float(mine_style.get("mine_style_score", 0.0)), 6),
            "diagnostic_level": "node/edge/fact/corpus",
            "interpretation": "Measures node and edge information retained in reconstructed graphs.",
        },
    ]
    if baseline is not None:
        lexical = baseline.get("lexical_graph_text_baselines", {})
        rows.extend(
            [
                {
                    "method": "Graph-text token cosine",
                    "direction": "KG↔Text",
                    "uses_factors": False,
                    "uses_retrieval": False,
                    "uses_llm_judge": False,
                    "score_key": "token_cosine",
                    "score": round(float(lexical.get("token_cosine", 0.0)), 6),
                    "diagnostic_level": "corpus",
                    "interpretation": "Bag-of-words lexical similarity control.",
                },
                {
                    "method": "Graph-text token Jaccard",
                    "direction": "KG↔Text",
                    "uses_factors": False,
                    "uses_retrieval": False,
                    "uses_llm_judge": False,
                    "score_key": "token_jaccard",
                    "score": round(float(lexical.get("token_jaccard", 0.0)), 6),
                    "diagnostic_level": "corpus",
                    "interpretation": "Shared-token lexical control.",
                },
            ]
        )
    return {
        "examples": forward.get("examples", reverse.get("examples", mine_style.get("examples"))),
        "edges": forward.get("edges", reverse.get("edges", mine_style.get("facts"))),
        "rows": rows,
        "notes": [
            "Reverse LEMON and MINE-style scores use deterministic reconstructed graphs, not a full KGGen extractor.",
            "MINE-style here is a WebNLG adaptation of node/edge information retention, without an LLM judge.",
            "Forward and reverse LEMON use the same predicate-factor decomposition schema.",
        ],
    }


def write_bidirectional_table(report: dict[str, Any], path: str | Path) -> None:
    lines = [
        "| Method | Direction | Factors | Retrieval | LLM judge | Score | Diagnostic level |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in report["rows"]:
        lines.append(
            "| {method} | {direction} | {factors} | {retrieval} | {judge} | {score:.4f} | {level} |".format(
                method=row["method"],
                direction=row["direction"],
                factors="yes" if row["uses_factors"] else "no",
                retrieval="yes" if row["uses_retrieval"] else "no",
                judge="yes" if row["uses_llm_judge"] else "no",
                score=float(row["score"]),
                level=row["diagnostic_level"],
            )
        )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--forward", required=True, help="Forward LEMON coverage JSON")
    parser.add_argument("--reverse", required=True, help="Reverse LEMON coverage JSON")
    parser.add_argument("--mine-style", required=True, help="MINE-style report JSON")
    parser.add_argument("--baseline", default=None, help="Optional baseline comparison JSON")
    parser.add_argument("--out", required=True, help="Output comparison JSON")
    parser.add_argument("--table", required=True, help="Output markdown table")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    report = build_bidirectional_comparison(
        forward=load_json(args.forward),
        reverse=load_json(args.reverse),
        mine_style=load_json(args.mine_style),
        baseline=load_json(args.baseline) if args.baseline else None,
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_bidirectional_table(report, args.table)
    print(json.dumps({"out": args.out, "table": args.table}, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
