"""Aggregate LEM-05 scoring reports into a combined table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from lemon_factor.scoring.score_perturbations import render_latex_table, render_markdown_table


_DATASET_LABELS = {
    "drugprot": "DrugProt",
    "bc5cdr": "BC5CDR",
    "webnlg": "WebNLG",
}


def aggregate_reports(paths: list[str | Path]) -> dict[str, Any]:
    reports = [json.loads(Path(path).read_text(encoding="utf-8")) for path in paths]
    summary: list[dict[str, Any]] = []
    for report in reports:
        dataset = report.get("dataset", "unknown")
        for row in report.get("summary", []):
            merged = dict(row)
            merged["dataset"] = dataset
            summary.append(merged)
    return {
        "status": "passed",
        "report_count": len(reports),
        "datasets": [report.get("dataset", "unknown") for report in reports],
        "summary": summary,
    }


def render_combined_latex(summary: list[dict[str, Any]], *, caption: str, label: str) -> str:
    # Group by dataset. Use the same columns as the per-dataset table, with an
    # additional dataset column to keep the paper table compact.
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
        r"\scriptsize",
        r"\begin{tabular}{llrrrrrr}",
        r"\toprule",
        r"Dataset & Perturbation & Entity & Label & Triple & MINE-style & LEMON-label & LEMON-full \\",
        r"\midrule",
    ]
    variant_labels = {
        "node_deletion": "Node deletion",
        "edge_deletion": "Relation cue deletion",
        "argument_swap": "Argument swap",
        "polarity_flip": "Polarity flip",
        "relation_blur": "Relation blur",
    }
    for row in summary:
        metrics = row["metrics"]
        dataset = _DATASET_LABELS.get(row["dataset"], row["dataset"])
        perturbation = variant_labels.get(row["variant"], row["variant"].replace("_", " ").title())
        lines.append(
            f"{dataset} & {perturbation} & "
            f"{metrics['entity_recall']:.4f} & {metrics['label_match']:.4f} & "
            f"{metrics['triple_match']:.4f} & {metrics['mine_style']:.4f} & "
            f"{metrics['lemon_label_only']:.4f} & {metrics['lemon_full']:.4f} \\\\".replace("\\\\\\", "\\\\")
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", nargs="+", required=True, help="Scoring report JSON files")
    parser.add_argument("--out", required=True, help="Combined JSON output path")
    parser.add_argument("--table-out", default=None, help="Optional .tex or .md table output")
    parser.add_argument("--caption", default="Biomedical perturbation scoring summary.")
    parser.add_argument("--label", default="tab:biomedical-final")
    args = parser.parse_args()

    report = aggregate_reports(args.inputs)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.table_out:
        table_path = Path(args.table_out)
        table_path.parent.mkdir(parents=True, exist_ok=True)
        if table_path.suffix == ".tex":
            text = render_combined_latex(report["summary"], caption=args.caption, label=args.label)
        else:
            text = render_markdown_table(report["summary"])
        table_path.write_text(text, encoding="utf-8")

    print(
        json.dumps(
            {"out": str(out_path), "status": report["status"], "datasets": report["datasets"]},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()
