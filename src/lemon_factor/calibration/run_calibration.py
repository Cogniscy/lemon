"""Run controlled perturbation calibration for graph-text metrics.

The command saves every perturbed dataset and every perturbation manifest under
``--perturbation-dir`` so that changes can be audited independently from the
metric summary.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from lemon_factor.calibration.calibration_stats import (
    KEY_METRICS,
    filter_summary_rows,
    perturbation_quality,
    relation_deletion_sanity,
    summarize_by_metric,
    summarize_calibration_rows,
    summarize_targeted_calibration,
)
from lemon_factor.calibration.perturb_graph import (
    GraphNoiseType,
    count_effective_graph_operations,
    perturb_reconstructed_graph_corpus,
    write_graph_perturbation_artifacts,
)
from lemon_factor.calibration.perturb_text import (
    TextNoiseType,
    count_effective_text_operations,
    expected_direction_for_text_noise,
    perturb_text_corpus,
    write_text_perturbation_artifacts,
)
from lemon_factor.coverage.graphtext_coverage import score_corpus_coverage
from lemon_factor.coverage.run_webnlg_coverage import load_lexical_cues
from lemon_factor.datasets.unified_io import read_jsonl
from lemon_factor.factors.decomposition import PredicateDecompositionSet
from lemon_factor.mine_nodes_edges.scoring import score_mine_style_corpus
from lemon_factor.reverse.reconstruct_graph import (
    read_reconstructed_graphs,
    reconstruct_corpus,
    write_reconstructed_graphs,
)
from lemon_factor.reverse.reverse_coverage import score_reverse_corpus

TEXT_NOISE_TYPES = {
    "swap_object",
    "swap_predicate",
    "delete_relation_phrase",
    "entity_alias",
    "predicate_paraphrase",
    "punctuation_case_noise",
}
GRAPH_NOISE_TYPES = {"drop_edge", "drop_node", "graph_swap_predicate", "hallucinate_edge"}
DEFAULT_NOISE_TYPES = [
    "delete_relation_phrase",
    "swap_object",
    "swap_predicate",
    "entity_alias",
    "predicate_paraphrase",
    "drop_edge",
    "drop_node",
    "graph_swap_predicate",
]


def _slug_level(level: float) -> str:
    return str(level).replace(".", "p")


def _write_jsonl_dicts(path: str | Path, rows: list[dict[str, object]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")


def _score_all(
    examples,
    records,
    *,
    decompositions: PredicateDecompositionSet,
    lexical_cues: dict[str, list[str]],
    top_k: int,
    hops: int,
) -> dict[str, float]:
    forward_report, _forward_examples, _forward_edges = score_corpus_coverage(
        examples,
        decompositions,
        lexical_cues,
    )
    reverse_report, _reverse_examples, _reverse_edges = score_reverse_corpus(
        examples,
        records,
        decompositions,
    )
    mine_report, _mine_scores = score_mine_style_corpus(examples, records, top_k=top_k, hops=hops)
    return {
        "forward_lemon": forward_report.lemon_factor_coverage,
        "exact_label_coverage": forward_report.exact_label_coverage,
        "predicate_cue_coverage": forward_report.predicate_cue_coverage,
        "reverse_lemon": reverse_report.reverse_lemon_coverage,
        "reverse_edge_recovery": reverse_report.edge_recovery_rate,
        "reverse_node_recovery": reverse_report.node_recovery_score,
        "mine_composite_node_edge": mine_report.composite_node_edge_score,
        "mine_fact_recoverability": mine_report.fact_recoverability,
        "mine_node_information": mine_report.node_information,
        "mine_edge_information": mine_report.edge_information,
    }


def _write_summary_table(metric_summary: list[dict[str, object]], path: str | Path) -> None:
    lines = [
        "| Metric | Destructive slope avg | Destructive Spearman avg | Destructive violations | Preserving delta avg | Preserving violations |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in metric_summary:
        lines.append(
            "| {metric} | {slope:.4f} | {rho:.4f} | {dviol} | {pdelta:.4f} | {pviol} |".format(
                metric=row["metric"],
                slope=float(row["destructive_slope_avg"]),
                rho=float(row["destructive_spearman_avg"]),
                dviol=row["destructive_violations"],
                pdelta=float(row["preserving_delta_avg"]),
                pviol=row["preserving_violations"],
            )
        )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_by_noise_table(summary_rows: list[dict[str, object]], path: str | Path) -> None:
    interesting = [row for row in summary_rows if row["metric"] in {"forward_lemon", "reverse_lemon", "mine_composite_node_edge", "mine_fact_recoverability", "exact_label_coverage"}]
    lines = [
        "| Noise | Target | Quality | Expected | Metric | Baseline | Final | Slope | Spearman | Violations |",
        "|---|---|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in interesting:
        lines.append(
            "| {noise} | {target} | {quality} | {exp} | {metric} | {base:.4f} | {final:.4f} | {slope:.4f} | {rho:.4f} | {viol} |".format(
                noise=row["noise_type"],
                target=row.get("noise_target", ""),
                quality=row.get("perturbation_quality", ""),
                exp=row["expected_direction"],
                metric=row["metric"],
                base=float(row["baseline"]),
                final=float(row["final_score"]),
                slope=float(row["sensitivity_slope"]),
                rho=float(row["spearman_noise_score"]),
                viol=row["monotonicity_violations"],
            )
        )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_directional_summary_table(metric_summary: list[dict[str, object]], path: str | Path) -> None:
    lines = [
        "| Metric | Recommended noise target | Destructive slope avg | Destructive Spearman avg | Destructive violations | Preserving delta avg | Preserving violations | Noise types |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in metric_summary:
        lines.append(
            "| {metric} | {target} | {slope:.4f} | {rho:.4f} | {dviol} | {pdelta:.4f} | {pviol} | {n} |".format(
                metric=row["metric"],
                target=row["recommended_noise_target"],
                slope=float(row["destructive_slope_avg"]),
                rho=float(row["destructive_spearman_avg"]),
                dviol=row["destructive_violations"],
                pdelta=float(row["preserving_delta_avg"]),
                pviol=row["preserving_violations"],
                n=row["noise_type_count"],
            )
        )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_side_summary_table(metric_summary: list[dict[str, object]], path: str | Path, *, side_label: str) -> None:
    lines = [
        f"| Metric | {side_label} destructive slope avg | Spearman avg | Violations | Preserving delta avg |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in metric_summary:
        lines.append(
            "| {metric} | {slope:.4f} | {rho:.4f} | {viol} | {pdelta:.4f} |".format(
                metric=row["metric"],
                slope=float(row["destructive_slope_avg"]),
                rho=float(row["destructive_spearman_avg"]),
                viol=row["destructive_violations"],
                pdelta=float(row["preserving_delta_avg"]),
            )
        )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_relation_deletion_table(rows: list[dict[str, object]], path: str | Path) -> None:
    lines = [
        "| Metric | Baseline | Final | Delta | Interpretation |",
        "|---|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {metric} | {base:.4f} | {final:.4f} | {delta:+.4f} | {interp} |".format(
                metric=row["metric"],
                base=float(row["baseline"]),
                final=float(row["final_score"]),
                delta=float(row["delta"]),
                interp=row["interpretation"],
            )
        )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_calibration(args: argparse.Namespace) -> dict[str, Any]:
    examples = read_jsonl(args.jsonl)
    original_records = read_reconstructed_graphs(args.reconstructed)
    decompositions = PredicateDecompositionSet.from_json_file(args.decompositions)
    lexical_cues = load_lexical_cues(args.lexical_cues)
    perturbation_dir = Path(args.perturbation_dir)
    rows: list[dict[str, object]] = []

    for noise_type in args.noise_types:
        for level in args.noise_levels:
            level = float(level)
            level_slug = _slug_level(level)
            seed = int(args.seed) + int(level * 1000) + sum(ord(ch) for ch in noise_type)
            artifact_base = perturbation_dir / noise_type / f"level_{level_slug}"

            if noise_type in TEXT_NOISE_TYPES:
                perturbed_examples, manifest = perturb_text_corpus(
                    examples,
                    noise_type=noise_type,  # type: ignore[arg-type]
                    noise_level=level,
                    lexical_cues=lexical_cues,
                    seed=seed,
                )
                examples_out = artifact_base.with_suffix(".jsonl")
                manifest_out = artifact_base.with_name(artifact_base.name + "_manifest.jsonl")
                write_text_perturbation_artifacts(
                    perturbed_examples,
                    manifest,
                    examples_out=examples_out,
                    manifest_out=manifest_out,
                )
                perturbed_records = reconstruct_corpus(
                    perturbed_examples,
                    lexical_cues=lexical_cues,
                    mode=args.reconstruction_mode,
                )
                reconstructed_out = artifact_base.with_name(artifact_base.name + "_reconstructed.jsonl")
                write_reconstructed_graphs(perturbed_records, reconstructed_out)
                scores = _score_all(
                    perturbed_examples,
                    perturbed_records,
                    decompositions=decompositions,
                    lexical_cues=lexical_cues,
                    top_k=args.top_k,
                    hops=args.hops,
                )
                row = {
                    "noise_type": noise_type,
                    "noise_target": "text",
                    "noise_level": level,
                    "expected_direction": expected_direction_for_text_noise(noise_type),
                    "perturbation_quality": perturbation_quality(noise_type),
                    "changed_operation_count": count_effective_text_operations(manifest),
                    "examples_path": str(examples_out),
                    "manifest_path": str(manifest_out),
                    "reconstructed_path": str(reconstructed_out),
                    **scores,
                }
            elif noise_type in GRAPH_NOISE_TYPES:
                perturbed_records, manifest = perturb_reconstructed_graph_corpus(
                    examples,
                    original_records,
                    noise_type=noise_type,  # type: ignore[arg-type]
                    noise_level=level,
                    seed=seed,
                )
                reconstructed_out = artifact_base.with_name(artifact_base.name + "_reconstructed.jsonl")
                manifest_out = artifact_base.with_name(artifact_base.name + "_manifest.jsonl")
                write_graph_perturbation_artifacts(
                    perturbed_records,
                    manifest,
                    reconstructed_out=reconstructed_out,
                    manifest_out=manifest_out,
                )
                scores = _score_all(
                    examples,
                    perturbed_records,
                    decompositions=decompositions,
                    lexical_cues=lexical_cues,
                    top_k=args.top_k,
                    hops=args.hops,
                )
                row = {
                    "noise_type": noise_type,
                    "noise_target": "reconstructed_graph",
                    "noise_level": level,
                    "expected_direction": "down",
                    "perturbation_quality": perturbation_quality(noise_type),
                    "changed_operation_count": count_effective_graph_operations(manifest),
                    "examples_path": args.jsonl,
                    "manifest_path": str(manifest_out),
                    "reconstructed_path": str(reconstructed_out),
                    **scores,
                }
            else:
                raise ValueError(f"Unsupported noise type: {noise_type}")
            rows.append(row)

    summary_rows = summarize_calibration_rows(rows, metrics=KEY_METRICS)
    metric_summary = summarize_by_metric(summary_rows)
    text_side_summary = summarize_by_metric(filter_summary_rows(summary_rows, noise_target="text"))
    graph_side_summary = summarize_by_metric(filter_summary_rows(summary_rows, noise_target="reconstructed_graph"))
    targeted_summary = summarize_targeted_calibration(summary_rows)
    relation_sanity = relation_deletion_sanity(summary_rows)
    report = {
        "dataset": args.jsonl,
        "examples": len(examples),
        "noise_types": args.noise_types,
        "noise_levels": [float(level) for level in args.noise_levels],
        "perturbation_dir": str(perturbation_dir),
        "rows": rows,
        "summary_by_noise": summary_rows,
        "summary_by_metric": metric_summary,
        "summary_by_metric_text_noise": text_side_summary,
        "summary_by_metric_graph_noise": graph_side_summary,
        "summary_by_metric_targeted": targeted_summary,
        "relation_deletion_sanity": relation_sanity,
        "methodology": {
            "invariance": "meaning-preserving perturbations should keep scores stable",
            "directional_expectation": "meaning-destroying perturbations should reduce scores",
            "artifacts": "all perturbed examples/reconstructed graphs and manifests are saved separately",
        },
    }
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", help="Unified GraphText JSONL")
    parser.add_argument("--reconstructed", required=True, help="Baseline reconstructed graph JSONL")
    parser.add_argument("--decompositions", required=True, help="Predicate decompositions JSON")
    parser.add_argument("--lexical-cues", required=True, help="Expanded lexical cues JSON")
    parser.add_argument("--noise-types", nargs="+", default=DEFAULT_NOISE_TYPES)
    parser.add_argument("--noise-levels", nargs="+", type=float, default=[0.0, 0.1, 0.25, 0.5])
    parser.add_argument("--perturbation-dir", default="data/perturbed/lemon13", help="Directory for perturbed datasets and manifests")
    parser.add_argument("--out", required=True, help="Calibration report JSON")
    parser.add_argument("--details", required=True, help="Row-level calibration JSONL")
    parser.add_argument("--table", required=True, help="Metric-level summary markdown table")
    parser.add_argument("--by-noise-table", default=None, help="Optional noise-by-metric markdown table")
    parser.add_argument("--text-side-table", default=None, help="Optional text-noise calibration markdown table")
    parser.add_argument("--graph-side-table", default=None, help="Optional graph-noise calibration markdown table")
    parser.add_argument("--relation-deletion-table", default=None, help="Optional relation deletion sanity-check markdown table")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--top-k", type=int, default=2)
    parser.add_argument("--hops", type=int, default=2)
    parser.add_argument("--reconstruction-mode", choices=["lexical", "oracle_nodes", "oracle_edges"], default="lexical")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    report = run_calibration(args)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_jsonl_dicts(args.details, report["rows"])
    _write_directional_summary_table(report["summary_by_metric_targeted"], args.table)
    if args.by_noise_table:
        _write_by_noise_table(report["summary_by_noise"], args.by_noise_table)
    if args.text_side_table:
        _write_side_summary_table(report["summary_by_metric_text_noise"], args.text_side_table, side_label="Text-side")
    if args.graph_side_table:
        _write_side_summary_table(report["summary_by_metric_graph_noise"], args.graph_side_table, side_label="Graph-side")
    if args.relation_deletion_table:
        _write_relation_deletion_table(report["relation_deletion_sanity"], args.relation_deletion_table)
    print(json.dumps({"out": args.out, "details": args.details, "table": args.table, "perturbation_dir": args.perturbation_dir}, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
