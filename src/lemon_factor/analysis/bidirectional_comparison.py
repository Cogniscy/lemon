"""Compare forward LEMON, reverse LEMON, and MINE-style text-to-KG scores."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _mine_row(mine_style: dict[str, Any], *, llm: bool = False) -> dict[str, Any]:
    metadata = mine_style.get("metadata", {})
    judge_mode = metadata.get("judge_mode", "llm" if llm else "deterministic")
    is_llm = bool(llm or judge_mode == "llm")
    label = "MINE-style composite node/edge"
    score_key = "composite_node_edge_score"
    score = mine_style.get("composite_node_edge_score", mine_style.get("mine_style_score", 0.0))
    interpretation = "Composite node/edge information retention; partial node credit can raise the score."
    if is_llm:
        label = "MINE-style LLM fact recoverability"
        score_key = "llm_fact_recoverability"
        score = mine_style.get("llm_fact_recoverability", mine_style.get("fact_recoverability", mine_style.get("mine_style_score", 0.0)))
        interpretation = "Binary fact recoverability judged from retrieved nodes and edges; not the node/edge composite score."
    elif judge_mode == "offline":
        label = "MINE-style offline fact recoverability"
        score_key = "fact_recoverability"
        score = mine_style.get("fact_recoverability", mine_style.get("mine_style_score", 0.0))
        interpretation = "Offline binary fact recoverability over retrieved nodes and edges."
    return {
        "method": label,
        "direction": "Text→KG",
        "uses_factors": False,
        "uses_retrieval": True,
        "uses_llm_judge": is_llm,
        "score_key": score_key,
        "score": round(float(score or 0.0), 6),
        "diagnostic_level": "node/edge/fact/corpus",
        "interpretation": interpretation,
        "facts": mine_style.get("facts"),
        "judged_facts": mine_style.get("judged_facts"),
    }


def _mine_subset_comparison(mine_style_llm: dict[str, Any] | None) -> dict[str, Any] | None:
    if not mine_style_llm:
        return None
    required = [
        "deterministic_score_on_subset",
        "deterministic_node_information_on_subset",
        "deterministic_edge_information_on_subset",
        "deterministic_fact_recoverability_on_subset",
        "llm_fact_recoverability",
    ]
    if not any(key in mine_style_llm and mine_style_llm.get(key) is not None for key in required):
        return None
    return {
        "facts": mine_style_llm.get("facts"),
        "deterministic_node_information": mine_style_llm.get("deterministic_node_information_on_subset"),
        "deterministic_edge_information": mine_style_llm.get("deterministic_edge_information_on_subset"),
        "deterministic_composite_node_edge_score": mine_style_llm.get("deterministic_score_on_subset"),
        "deterministic_fact_recoverability": mine_style_llm.get("deterministic_fact_recoverability_on_subset"),
        "llm_fact_recoverability": mine_style_llm.get("llm_fact_recoverability", mine_style_llm.get("fact_recoverability")),
        "judge_agreement_with_deterministic": mine_style_llm.get("judge_agreement_with_deterministic"),
        "parse_success_rate": mine_style_llm.get("parse_success_rate", mine_style_llm.get("judge_parse_success_rate")),
        "mean_judge_confidence": mine_style_llm.get("mean_judge_confidence"),
        "note": "Composite node/edge score and binary fact recoverability are different score semantics.",
    }


def build_bidirectional_comparison(
    *,
    forward: dict[str, Any],
    reverse: dict[str, Any],
    mine_style: dict[str, Any],
    mine_style_llm: dict[str, Any] | None = None,
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
        _mine_row(mine_style, llm=False),
    ]
    if mine_style_llm is not None:
        rows.append(_mine_row(mine_style_llm, llm=True))
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
    notes = [
        "Reverse LEMON and MINE-style scores use deterministic reconstructed graphs, not a full KGGen extractor.",
        "MINE-style here is a WebNLG adaptation of node/edge information retention.",
        "Forward and reverse LEMON use the same predicate-factor decomposition schema.",
    ]
    if mine_style_llm is not None:
        notes.append("LLM-judged MINE-style uses a provisional LLM judge over retrieved subgraphs; it is not human validation.")
    else:
        notes.append("The deterministic MINE-style score does not use an LLM judge.")
    return {
        "examples": forward.get("examples", reverse.get("examples", mine_style.get("examples"))),
        "edges": forward.get("edges", reverse.get("edges", mine_style.get("facts"))),
        "rows": rows,
        "mine_subset_comparison": _mine_subset_comparison(mine_style_llm),
        "notes": notes,
    }


def write_mine_subset_comparison_table(report: dict[str, Any], path: str | Path) -> None:
    subset = report.get("mine_subset_comparison")
    lines = [
        "| Metric | Value |",
        "|---|---:|",
    ]
    if not subset:
        lines.append("| MINE-style fixed-subset comparison | not available |")
    else:
        rows = [
            ("Facts", subset.get("facts")),
            ("Deterministic node information", subset.get("deterministic_node_information")),
            ("Deterministic edge information", subset.get("deterministic_edge_information")),
            ("Deterministic composite node/edge score", subset.get("deterministic_composite_node_edge_score")),
            ("Deterministic fact recoverability", subset.get("deterministic_fact_recoverability")),
            ("LLM fact recoverability", subset.get("llm_fact_recoverability")),
            ("Judge agreement with deterministic", subset.get("judge_agreement_with_deterministic")),
            ("Parse success rate", subset.get("parse_success_rate")),
            ("Mean judge confidence", subset.get("mean_judge_confidence")),
        ]
        for name, value in rows:
            if isinstance(value, float):
                rendered = f"{value:.4f}"
            else:
                rendered = "—" if value is None else str(value)
            lines.append(f"| {name} | {rendered} |")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    parser.add_argument("--mine-style", required=True, help="Deterministic MINE-style report JSON")
    parser.add_argument("--mine-style-llm", default=None, help="Optional LLM-judged MINE-style report JSON")
    parser.add_argument("--baseline", default=None, help="Optional baseline comparison JSON")
    parser.add_argument("--out", required=True, help="Output comparison JSON")
    parser.add_argument("--table", required=True, help="Output markdown table")
    parser.add_argument("--mine-subset-table", default=None, help="Optional Markdown table comparing deterministic and LLM MINE on the same subset")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    report = build_bidirectional_comparison(
        forward=load_json(args.forward),
        reverse=load_json(args.reverse),
        mine_style=load_json(args.mine_style),
        mine_style_llm=load_json(args.mine_style_llm) if args.mine_style_llm else None,
        baseline=load_json(args.baseline) if args.baseline else None,
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_bidirectional_table(report, args.table)
    if args.mine_subset_table:
        write_mine_subset_comparison_table(report, args.mine_subset_table)
    print(json.dumps({"out": args.out, "table": args.table, "mine_subset_table": args.mine_subset_table}, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
