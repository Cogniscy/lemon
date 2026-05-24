"""Recompute compact publication aggregates for LEMON-Factor results.

This module is intentionally presentation-oriented. It does not change the
underlying scoring pipeline. It reads existing scoring/ablation/LLM reliability
reports and produces simpler paper-facing aggregates:

* perturbation sensitivity as mean score drop, where larger means more sensitive;
* ablation sensitivity as mean drop and factor gain, without Spearman/Viol fields;
* LLM reliability as a compact exploratory probe summary.

Usage:
    python -m lemon_factor.analysis.recompute_paper_aggregates \
      --scoring reports/scoring_webnlg.json reports/scoring_drugprot.json reports/scoring_bc5cdr.json \
      --ablation reports/ablation_summary.json \
      --llm reports/llm_reliability_summary_3judges.json \
      --out-dir reports \
      --table-dir paper/tables
"""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

DEFAULT_METRICS = [
    "entity_recall",
    "triple_match",
    "mine_style",
    "lemon_label_only",
    "lemon_full",
]

METRIC_LABELS = {
    "entity_recall": "Entity",
    "triple_match": "Triple",
    "mine_style": "Node/edge",
    "lemon_label_only": "Label-only",
    "lemon_full": "LEMON-Factor",
}

VARIANT_ORDER = [
    "node_deletion",
    "edge_deletion",
    "argument_swap",
    "polarity_flip",
    "relation_blur",
]

VARIANT_LABELS = {
    "node_deletion": "Node deletion",
    "edge_deletion": "Edge deletion",
    "argument_swap": "Argument swap",
    "polarity_flip": "Polarity flip",
    "relation_blur": "Relation blur",
}

ABLATION_ORDER = [
    "full",
    "label_only",
    "unweighted",
    "minus_roles",
    "minus_direction",
    "minus_polarity",
    "minus_evidence",
]

ABLATION_LABELS = {
    "full": "LEMON-full",
    "label_only": "Label-only",
    "unweighted": "Unweighted",
    "minus_roles": "Minus roles",
    "minus_direction": "Minus direction",
    "minus_polarity": "Minus polarity",
    "minus_evidence": "Minus evidence",
}


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def _fmt(value: float | None, digits: int = 3) -> str:
    if value is None:
        return "--"
    return f"{value:.{digits}f}"


def _bootstrap_ci(values: list[float], *, seed: int = 13, samples: int = 0) -> tuple[float, float] | None:
    if not values:
        return None
    if len(values) == 1:
        return (values[0], values[0])
    if samples <= 0:
        return None
    rng = random.Random(seed)
    n = len(values)
    boots = []
    for _ in range(samples):
        boots.append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    boots.sort()
    low_idx = int(0.025 * (samples - 1))
    high_idx = int(0.975 * (samples - 1))
    return boots[low_idx], boots[high_idx]


def load_scoring_rows(scoring_paths: Iterable[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in scoring_paths:
        data = _read_json(path)
        dataset = data.get("dataset") or Path(path).stem.replace("scoring_", "")
        for row in data.get("rows", []):
            scores = row.get("scores", {})
            rows.append(
                {
                    "dataset": row.get("dataset", dataset),
                    "variant": row.get("variant"),
                    "scores": scores,
                }
            )
    return rows


def compute_sensitivity(rows: list[dict[str, Any]], metrics: list[str]) -> dict[str, Any]:
    """Compute score drops. For preservation-style scores, drop = 1 - score.

    Larger values therefore mean stronger sensitivity to the perturbation.
    """
    by_variant_metric: dict[tuple[str, str], list[float]] = defaultdict(list)
    by_dataset_metric: dict[tuple[str, str], list[float]] = defaultdict(list)
    by_dataset_variant_metric: dict[tuple[str, str, str], list[float]] = defaultdict(list)

    for row in rows:
        dataset = row["dataset"]
        variant = row["variant"]
        scores = row["scores"]
        for metric in metrics:
            if metric not in scores:
                continue
            drop = 1.0 - float(scores[metric])
            by_variant_metric[(variant, metric)].append(drop)
            by_dataset_metric[(dataset, metric)].append(drop)
            by_dataset_variant_metric[(dataset, variant, metric)].append(drop)

    variant_rows: list[dict[str, Any]] = []
    for variant in VARIANT_ORDER:
        out: dict[str, Any] = {
            "variant": variant,
            "label": VARIANT_LABELS.get(variant, variant),
        }
        for metric in metrics:
            vals = by_variant_metric.get((variant, metric), [])
            ci = _bootstrap_ci(vals)
            out[metric] = {
                "mean_drop": mean(vals) if vals else None,
                "ci95": ci,
                "n": len(vals),
            }
        variant_rows.append(out)

    dataset_rows: list[dict[str, Any]] = []
    for dataset in sorted({r["dataset"] for r in rows}):
        out = {"dataset": dataset}
        for metric in metrics:
            vals = by_dataset_metric.get((dataset, metric), [])
            ci = _bootstrap_ci(vals)
            out[metric] = {
                "mean_drop": mean(vals) if vals else None,
                "ci95": ci,
                "n": len(vals),
            }
        dataset_rows.append(out)

    dataset_variant_rows: list[dict[str, Any]] = []
    for dataset in sorted({r["dataset"] for r in rows}):
        for variant in VARIANT_ORDER:
            out = {"dataset": dataset, "variant": variant}
            for metric in metrics:
                vals = by_dataset_variant_metric.get((dataset, variant, metric), [])
                out[metric] = mean(vals) if vals else None
            dataset_variant_rows.append(out)

    return {
        "status": "passed",
        "definition": "mean_drop = 1 - preservation_score; larger means more sensitivity to perturbation",
        "metrics": metrics,
        "by_variant": variant_rows,
        "by_dataset": dataset_rows,
        "by_dataset_variant": dataset_variant_rows,
    }


def compute_ablation_gain(ablation_path: Path) -> dict[str, Any]:
    data = _read_json(ablation_path)
    summary = {row["ablation"]: row for row in data.get("summary", [])}
    full = summary.get("full")
    if full is None:
        raise ValueError("Ablation summary does not contain the 'full' row")

    datasets = sorted(full.get("datasets", {}).keys())
    rows: list[dict[str, Any]] = []
    for ablation in ABLATION_ORDER:
        if ablation not in summary:
            continue
        row = summary[ablation]
        out: dict[str, Any] = {
            "ablation": ablation,
            "label": ABLATION_LABELS.get(ablation, row.get("label", ablation)),
            "datasets": {},
        }
        gains = []
        drops = []
        for dataset in datasets:
            full_drop = float(full["datasets"][dataset]["mean_drop"])
            drop = float(row["datasets"][dataset]["mean_drop"])
            gain = full_drop - drop
            out["datasets"][dataset] = {
                "mean_drop": drop,
                "full_minus_ablation": gain,
                "records": row["datasets"][dataset].get("records"),
            }
            gains.append(gain)
            drops.append(drop)
        out["mean_drop"] = mean(drops) if drops else None
        out["mean_gain_vs_full"] = mean(gains) if gains else None
        rows.append(out)

    return {
        "status": "passed",
        "definition": "mean_drop is perturbation sensitivity. full_minus_ablation > 0 means the full model is more sensitive than the ablated variant.",
        "datasets": datasets,
        "rows": rows,
    }


def compute_llm_compact(llm_path: Path) -> dict[str, Any]:
    data = _read_json(llm_path)
    weighted_score_num = 0.0
    weighted_score_den = 0
    det_num = 0.0
    det_den = 0
    pair_num = 0.0
    pair_den = 0

    by_variant: list[dict[str, Any]] = []
    for row in data.get("summary", []):
        votes = int(row.get("factor_votes", 0) or 0)
        score = row.get("mean_llm_score")
        det = row.get("deterministic_agreement")
        pair = row.get("pairwise_agreement")
        if score is not None and votes:
            weighted_score_num += float(score) * votes
            weighted_score_den += votes
        if det is not None and votes:
            det_num += float(det) * votes
            det_den += votes
        if pair is not None and votes:
            pair_num += float(pair) * votes
            pair_den += votes
        by_variant.append(
            {
                "dataset": row.get("dataset"),
                "variant": row.get("variant"),
                "mean_llm_score": score,
                "pairwise_agreement": pair,
                "deterministic_agreement": det,
                "factor_votes": votes,
            }
        )

    return {
        "status": "passed",
        "item_count": data.get("item_count"),
        "judgment_count": data.get("judgment_count"),
        "judge_count": data.get("judge_count"),
        "definition": "Mean LLM score is factor preservation judged as covered=1, partial=0.5, absent=0. Pairwise agreement is computed on overlapping factor judgments only.",
        "overall": {
            "mean_llm_score": weighted_score_num / weighted_score_den if weighted_score_den else None,
            "deterministic_agreement": det_num / det_den if det_den else None,
            "pairwise_agreement_overlap": pair_num / pair_den if pair_den else None,
            "factor_votes": weighted_score_den,
            "pairwise_factor_votes": pair_den,
        },
        "by_dataset_variant": by_variant,
        "models": ["google/gemini-2.0-flash-001", "openai/gpt-4o-mini", "meta-llama/llama-3.1-70b-instruct"],
    }


def write_sensitivity_tex(path: Path, sensitivity: dict[str, Any], metrics: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\small",
        r"\caption{Perturbation sensitivity as mean score drop. Larger values indicate that a metric reacts more strongly to the perturbation; unchanged or small drops mark blind spots rather than missing computations.}",
        r"\label{tab:perturbation-sensitivity-drop}",
        r"\begin{tabular}{l" + "r" * len(metrics) + r"}",
        r"\toprule",
        "Perturbation & " + " & ".join(METRIC_LABELS.get(m, m) for m in metrics) + r" \\",
        r"\midrule",
    ]
    for row in sensitivity["by_variant"]:
        cells = [row["label"]]
        for metric in metrics:
            cells.append(_fmt(row[metric]["mean_drop"]))
        lines.append(" & ".join(cells) + r" \\")
    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_ablation_tex(path: Path, ablation: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    datasets = ablation.get("datasets", [])
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\small",
        r"\caption{Ablation sensitivity. Mean drop is the average perturbation response; gain is $\Delta_{full}-\Delta_{ablated}$, so positive values mean that removing the component reduces sensitivity.}",
        r"\label{tab:ablation-gain}",
        r"\begin{tabular}{lrr}",
        r"\toprule",
        r"Variant & Mean drop & Gain vs. full \\",
        r"\midrule",
    ]
    for row in ablation["rows"]:
        lines.append(f"{row['label']} & {_fmt(row['mean_drop'])} & {_fmt(row['mean_gain_vs_full'])} \\")
    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_llm_tex(path: Path, llm: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    overall = llm["overall"]
    batches = f"3 $\\times$ {int(llm.get('judgment_count', 0) / max(int(llm.get('judge_count', 1)), 1))}"
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\small",
        r"\caption{Exploratory LLM reliability probe. Mean score treats covered, partial, and absent factor judgments as 1, 0.5, and 0. Agreement is computed only on overlapping factor judgments.}",
        r"\label{tab:llm-reliability}",
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"Probe & Batches & Judges & Mean score & Agreement \\",
        r"\midrule",
        f"LLM factor judging & {batches} & {llm.get('judge_count', '--')} & {_fmt(overall['mean_llm_score'])} & {_fmt(overall['pairwise_agreement_overlap'])} \\",
        r"\bottomrule",
        r"\end{tabular}",
        r"\end{table}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_markdown_report(path: Path, sensitivity: dict[str, Any], ablation: dict[str, Any], llm: dict[str, Any]) -> None:
    lines = [
        "# LEM-13 recalculated paper aggregates",
        "",
        "This report replaces opaque pilot diagnostics with publication-facing aggregates.",
        "",
        "## Definitions",
        "",
        "- Perturbation sensitivity is `1 - preservation_score`; larger values mean the metric reacts more strongly.",
        "- Ablation gain is `full_drop - ablated_drop`; positive values mean the removed component contributed sensitivity.",
        "- LLM mean score maps `covered/partial/absent` to `1/0.5/0`.",
        "- Pairwise LLM agreement is reported only for overlapping factor judgments.",
        "",
        "## Overall LLM probe",
        "",
        f"- Judgments: {llm.get('judgment_count')}",
        f"- Judges: {llm.get('judge_count')}",
        f"- Mean LLM score: {_fmt(llm['overall']['mean_llm_score'])}",
        f"- Pairwise agreement on overlap: {_fmt(llm['overall']['pairwise_agreement_overlap'])}",
        f"- Deterministic agreement: {_fmt(llm['overall']['deterministic_agreement'])}",
        "",
        "## Recommended paper-table replacements",
        "",
        "- Replace Spearman/Viol diagnostics with `table_perturbation_sensitivity_drop.tex`.",
        "- Replace generic ablation score with `table_ablation_gain.tex`.",
        "- Keep LLM reliability compact with `table_llm_reliability.tex`.",
        "- Remove BC5CDR predicate coverage table from the main text; explain it as a single-relation transfer setting.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Recompute compact paper aggregates.")
    parser.add_argument("--scoring", nargs="+", required=True, type=Path, help="Scoring JSON files.")
    parser.add_argument("--ablation", required=True, type=Path, help="Ablation summary JSON.")
    parser.add_argument("--llm", required=True, type=Path, help="LLM reliability summary JSON.")
    parser.add_argument("--out-dir", type=Path, default=Path("reports"))
    parser.add_argument("--table-dir", type=Path, default=Path("paper/tables"))
    parser.add_argument("--metrics", nargs="+", default=DEFAULT_METRICS)
    args = parser.parse_args(argv)

    rows = load_scoring_rows(args.scoring)
    sensitivity = compute_sensitivity(rows, args.metrics)
    ablation = compute_ablation_gain(args.ablation)
    llm = compute_llm_compact(args.llm)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.table_dir.mkdir(parents=True, exist_ok=True)

    _write_json(args.out_dir / "paper_metric_sensitivity_drops.json", sensitivity)
    _write_json(args.out_dir / "paper_ablation_gain.json", ablation)
    _write_json(args.out_dir / "paper_llm_reliability_compact.json", llm)

    write_sensitivity_tex(args.table_dir / "table_perturbation_sensitivity_drop.tex", sensitivity, args.metrics)
    write_ablation_tex(args.table_dir / "table_ablation_gain.tex", ablation)
    write_llm_tex(args.table_dir / "table_llm_reliability.tex", llm)
    write_markdown_report(args.out_dir / "lem13_recomputed_aggregates_report.md", sensitivity, ablation, llm)

    print(
        json.dumps(
            {
                "status": "passed",
                "rows": len(rows),
                "out": str(args.out_dir),
                "tables": [
                    str(args.table_dir / "table_perturbation_sensitivity_drop.tex"),
                    str(args.table_dir / "table_ablation_gain.tex"),
                    str(args.table_dir / "table_llm_reliability.tex"),
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
