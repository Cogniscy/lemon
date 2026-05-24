"""Score controlled perturbation JSONL files with deterministic baselines."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from lemon_factor.factors.decomposition import PredicateDecompositionSet
from lemon_factor.perturbations.schema import PerturbedGraphTextRecord
from lemon_factor.scoring.baselines import score_record

_METRIC_ORDER = [
    "entity_recall",
    "label_match",
    "triple_match",
    "mine_style",
    "lemon_label_only",
    "lemon_full",
]

_VARIANT_ORDER = [
    "node_deletion",
    "edge_deletion",
    "argument_swap",
    "polarity_flip",
    "relation_blur",
]

_VARIANT_LABELS = {
    "node_deletion": "Node deletion",
    "edge_deletion": "Relation cue deletion",
    "argument_swap": "Argument swap",
    "polarity_flip": "Polarity flip",
    "relation_blur": "Relation blur",
}

_METRIC_LABELS = {
    "entity_recall": "Entity",
    "label_match": "Label",
    "triple_match": "Triple",
    "mine_style": "MINE-style",
    "lemon_label_only": "LEMON label",
    "lemon_full": "LEMON full",
}


def _read_records(path: str | Path) -> list[PerturbedGraphTextRecord]:
    records: list[PerturbedGraphTextRecord] = []
    with Path(path).open("r", encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                records.append(PerturbedGraphTextRecord.model_validate_json(line))
            except Exception as exc:  # pragma: no cover - line context for CLI users
                raise ValueError(f"Invalid perturbed JSONL at {path}:{line_no}") from exc
    return records


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _aggregate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, float]]] = defaultdict(list)
    for row in rows:
        grouped[(row["dataset"], row["variant"])].append(row["scores"])
    summary: list[dict[str, Any]] = []
    for (dataset, variant), score_rows in sorted(
        grouped.items(), key=lambda item: (item[0][0], _VARIANT_ORDER.index(item[0][1]) if item[0][1] in _VARIANT_ORDER else 99)
    ):
        metrics = {
            metric: round(_mean([scores[metric] for scores in score_rows]), 4)
            for metric in _METRIC_ORDER
        }
        summary.append(
            {
                "dataset": dataset,
                "variant": variant,
                "records": len(score_rows),
                "metrics": metrics,
            }
        )
    return summary


def render_latex_table(
    summary: list[dict[str, Any]],
    *,
    caption: str,
    label: str,
) -> str:
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
        r"\scriptsize",
        r"\begin{tabular}{lrrrrrr}",
        r"\toprule",
        r"Perturbation & Entity & Label & Triple & MINE-style & LEMON-label & LEMON-full \\",
        r"\midrule",
    ]
    for row in summary:
        metrics = row["metrics"]
        name = _VARIANT_LABELS.get(row["variant"], row["variant"].replace("_", " ").title())
        lines.append(
            f"{name} & "
            f"{metrics['entity_recall']:.4f} & "
            f"{metrics['label_match']:.4f} & "
            f"{metrics['triple_match']:.4f} & "
            f"{metrics['mine_style']:.4f} & "
            f"{metrics['lemon_label_only']:.4f} & "
            f"{metrics['lemon_full']:.4f} \\\\".replace("\\\\\\", "\\\\")
        )
    lines.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}", ""])
    return "\n".join(lines)


def render_markdown_table(summary: list[dict[str, Any]]) -> str:
    lines = [
        "| Perturbation | Records | Entity | Label | Triple | MINE-style | LEMON-label | LEMON-full |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary:
        metrics = row["metrics"]
        name = _VARIANT_LABELS.get(row["variant"], row["variant"].replace("_", " ").title())
        lines.append(
            f"| {name} | {row['records']} | "
            f"{metrics['entity_recall']:.4f} | {metrics['label_match']:.4f} | "
            f"{metrics['triple_match']:.4f} | {metrics['mine_style']:.4f} | "
            f"{metrics['lemon_label_only']:.4f} | {metrics['lemon_full']:.4f} |"
        )
    return "\n".join(lines) + "\n"


def score_file(
    input_path: str | Path,
    inventory_path: str | Path,
    *,
    dataset: str | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    inventory = PredicateDecompositionSet.from_json_file(inventory_path)
    records = _read_records(input_path)
    if limit is not None:
        records = records[:limit]
    rows: list[dict[str, Any]] = []
    for record in records:
        row_dataset = dataset or record.dataset
        scores = score_record(record, inventory)
        rows.append(
            {
                "id": record.id,
                "dataset": row_dataset,
                "variant": record.variant,
                "scores": scores,
            }
        )
    summary = _aggregate(rows)
    return {
        "status": "passed",
        "input": str(input_path),
        "inventory": str(inventory_path),
        "dataset": dataset or (records[0].dataset if records else "unknown"),
        "record_count": len(rows),
        "metrics": _METRIC_ORDER,
        "summary": summary,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Perturbed GraphText JSONL")
    parser.add_argument("--inventory", required=True, help="Predicate-factor inventory JSON")
    parser.add_argument("--dataset", default=None, help="Optional dataset label override")
    parser.add_argument("--out", required=True, help="JSON output path")
    parser.add_argument("--table-out", default=None, help="Optional .tex or .md table output")
    parser.add_argument("--caption", default=None, help="LaTeX table caption")
    parser.add_argument("--label", default=None, help="LaTeX table label")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    report = score_file(args.input, args.inventory, dataset=args.dataset, limit=args.limit)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.table_out:
        table_path = Path(args.table_out)
        table_path.parent.mkdir(parents=True, exist_ok=True)
        if table_path.suffix == ".tex":
            caption = args.caption or "Deterministic scoring over controlled perturbations."
            label = args.label or f"tab:{report['dataset']}-scoring"
            text = render_latex_table(report["summary"], caption=caption, label=label)
        else:
            text = render_markdown_table(report["summary"])
        table_path.write_text(text, encoding="utf-8")

    print(
        json.dumps(
            {
                "out": str(out_path),
                "status": report["status"],
                "records": report["record_count"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()
