"""Compact ablation study for deterministic LEMON perturbation scoring.

The ablation layer reuses the perturbed JSONL files and fixed factor
inventories recorded in LEM-05 scoring reports. It does not call an LLM.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from lemon_factor.factors.decomposition import PredicateDecompositionSet
from lemon_factor.perturbations.schema import PerturbedGraphTextRecord
from lemon_factor.scoring.baselines import (
    lemon_factor_proxy_score,
    predicate_match,
)
from lemon_factor.scoring.score_perturbations import _read_records

_DATASET_LABELS = {
    "webnlg": "WebNLG",
    "drugprot": "DrugProt",
    "bc5cdr": "BC5CDR",
}

_ABLATION_ORDER = [
    "full",
    "label_only",
    "unweighted",
    "minus_roles",
    "minus_direction",
    "minus_polarity",
    "minus_evidence",
]

_ABLATION_LABELS = {
    "full": "Damage proxy",
    "label_only": "Label-only",
    "unweighted": "Unweighted",
    "minus_roles": "- roles",
    "minus_direction": "- direction",
    "minus_polarity": "- polarity",
    "minus_evidence": "- evidence",
}

_EXCLUDED_GROUPS = {
    "full": frozenset(),
    "unweighted": frozenset(),
    "minus_roles": frozenset({"participant_roles", "entity_presence"}),
    "minus_direction": frozenset({"directionality"}),
    "minus_polarity": frozenset({"polarity"}),
    "minus_evidence": frozenset({"evidence_form", "predicate_specificity"}),
}


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _edge_predicates(record: PerturbedGraphTextRecord) -> list[str]:
    return [str(edge.get("pred", "")) for edge in record.edges if edge.get("pred")]


def _score_record_ablation(
    record: PerturbedGraphTextRecord,
    inventory: PredicateDecompositionSet,
    ablation: str,
) -> float:
    predicates = _edge_predicates(record)
    if not predicates:
        return 0.0
    if ablation == "label_only":
        return _mean([predicate_match(record.text, predicate) for predicate in predicates])
    unweighted = ablation == "unweighted"
    excluded = _EXCLUDED_GROUPS.get(ablation, frozenset())
    return _mean(
        [
            lemon_factor_proxy_score(
                record,
                predicate,
                inventory,
                excluded_groups=excluded,
                unweighted=unweighted,
            )
            for predicate in predicates
        ]
    )


def _load_report(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _resolve_path(path_value: str, *, base_dir: Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    direct = Path.cwd() / path
    if direct.exists():
        return direct
    return base_dir / path


def ablate_reports(paths: list[str | Path]) -> dict[str, Any]:
    """Run factor-group ablations for one or more LEM-05 scoring reports."""

    raw_rows: list[dict[str, Any]] = []
    summary_cells: dict[tuple[str, str], list[float]] = defaultdict(list)
    by_variant_cells: dict[tuple[str, str, str], list[float]] = defaultdict(list)

    for report_path in paths:
        report_path = Path(report_path)
        report = _load_report(report_path)
        dataset = str(report.get("dataset", "unknown"))
        base_dir = report_path.parent.parent if report_path.parent.name == "reports" else report_path.parent
        input_path = _resolve_path(str(report["input"]), base_dir=base_dir)
        inventory_path = _resolve_path(str(report["inventory"]), base_dir=base_dir)
        inventory = PredicateDecompositionSet.from_json_file(inventory_path)
        records = _read_records(input_path)
        if "record_count" in report:
            records = records[:report["record_count"]]

        for record in records:
            for ablation in _ABLATION_ORDER:
                score = _score_record_ablation(record, inventory, ablation)
                drop = max(0.0, min(1.0, 1.0 - score))
                summary_cells[(dataset, ablation)].append(drop)
                by_variant_cells[(dataset, ablation, record.variant)].append(drop)
                raw_rows.append(
                    {
                        "id": record.id,
                        "dataset": dataset,
                        "variant": record.variant,
                        "ablation": ablation,
                        "score": round(score, 6),
                        "drop": round(drop, 6),
                    }
                )

    datasets = sorted({dataset for dataset, _ in summary_cells.keys()})
    summary: list[dict[str, Any]] = []
    for ablation in _ABLATION_ORDER:
        row = {"ablation": ablation, "label": _ABLATION_LABELS[ablation], "datasets": {}}
        for dataset in datasets:
            values = summary_cells.get((dataset, ablation), [])
            row["datasets"][dataset] = {
                "mean_drop": round(_mean(values), 4),
                "records": len(values),
            }
        summary.append(row)

    by_variant: list[dict[str, Any]] = []
    for (dataset, ablation, variant), values in sorted(by_variant_cells.items()):
        by_variant.append(
            {
                "dataset": dataset,
                "ablation": ablation,
                "variant": variant,
                "mean_drop": round(_mean(values), 4),
                "records": len(values),
            }
        )

    return {
        "status": "passed",
        "schema_version": "factor-damage-ablation-v2",
        "evidence_source": "Intended damage metadata; internal proxy analysis, not text error detection.",
        "datasets": datasets,
        "ablation_order": _ABLATION_ORDER,
        "summary": summary,
        "by_variant": by_variant,
        "rows": raw_rows,
        "notes": {
            "mean_drop": "1 - deterministic factor score; higher values mean greater prescribed factor damage.",
            "llm": "No LLM calls are used in this ablation study.",
        },
    }


def render_markdown_table(report: dict[str, Any]) -> str:
    datasets = report["datasets"]
    headers = ["Ablation"] + [_DATASET_LABELS.get(dataset, dataset) for dataset in datasets]
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for row in report["summary"]:
        cells = [row["label"]]
        for dataset in datasets:
            cells.append(f"{row['datasets'][dataset]['mean_drop']:.4f}")
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def render_latex_table(report: dict[str, Any], *, caption: str, label: str) -> str:
    datasets = report["datasets"]
    colspec = "l" + "r" * len(datasets)
    dataset_headers = " & ".join(_DATASET_LABELS.get(dataset, dataset) for dataset in datasets)
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        rf"\caption{{{caption}}}",
        rf"\label{{{label}}}",
        r"\scriptsize",
        rf"\begin{{tabular}}{{{colspec}}}",
        r"\toprule",
        rf"Ablation & {dataset_headers} \\",
        r"\midrule",
    ]
    for row in report["summary"]:
        values = " & ".join(f"{row['datasets'][dataset]['mean_drop']:.4f}" for dataset in datasets)
        lines.append(rf"{row['label']} & {values} \\")
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", nargs="+", required=True, help="LEM-05 scoring report JSON files")
    parser.add_argument("--out", required=True, help="Ablation JSON output path")
    parser.add_argument("--table-out", default=None, help="Optional .tex or .md table output")
    parser.add_argument("--caption", default="Factor-group ablation: mean controlled-damage drop ($1-score$); higher is more sensitive.")
    parser.add_argument("--label", default="tab:ablation")
    args = parser.parse_args()

    report = ablate_reports(args.inputs)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.table_out:
        table_path = Path(args.table_out)
        table_path.parent.mkdir(parents=True, exist_ok=True)
        if table_path.suffix == ".tex":
            table_text = render_latex_table(report, caption=args.caption, label=args.label)
        else:
            table_text = render_markdown_table(report)
        table_path.write_text(table_text, encoding="utf-8")

    print(
        json.dumps(
            {"out": str(out_path), "status": report["status"], "datasets": report["datasets"]},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()
