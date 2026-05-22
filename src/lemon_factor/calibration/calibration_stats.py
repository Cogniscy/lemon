"""Calibration statistics for controlled perturbation experiments."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

KEY_METRICS = [
    "forward_lemon",
    "exact_label_coverage",
    "predicate_cue_coverage",
    "reverse_lemon",
    "mine_composite_node_edge",
    "mine_fact_recoverability",
    "mine_node_information",
    "mine_edge_information",
]


TEXT_SIDE_NOISES = {
    "delete_relation_phrase",
    "swap_object",
    "swap_predicate",
    "entity_alias",
    "predicate_paraphrase",
    "punctuation_case_noise",
}
GRAPH_SIDE_NOISES = {"drop_edge", "drop_node", "graph_swap_predicate", "hallucinate_edge"}

PERTURBATION_QUALITY = {
    "delete_relation_phrase": "clean",
    "swap_object": "clean",
    "swap_predicate": "clean",
    "drop_edge": "clean",
    "drop_node": "clean",
    "graph_swap_predicate": "clean",
    "hallucinate_edge": "precision_only",
    "entity_alias": "weak_template",
    "predicate_paraphrase": "weak_template",
    "punctuation_case_noise": "clean",
}

FORWARD_TEXT_METRICS = {"forward_lemon", "exact_label_coverage", "predicate_cue_coverage"}
REVERSE_GRAPH_METRICS = {
    "reverse_lemon",
    "mine_composite_node_edge",
    "mine_fact_recoverability",
    "mine_node_information",
    "mine_edge_information",
}


def noise_target_side(noise_type: str) -> str:
    if noise_type in TEXT_SIDE_NOISES:
        return "text"
    if noise_type in GRAPH_SIDE_NOISES:
        return "reconstructed_graph"
    return "unknown"


def perturbation_quality(noise_type: str) -> str:
    return PERTURBATION_QUALITY.get(noise_type, "unknown")


def _safe_avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def _linear_slope(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2 or len(set(xs)) < 2:
        return 0.0
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    denom = sum((x - x_mean) ** 2 for x in xs)
    if denom == 0:
        return 0.0
    return round(sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denom, 6)


def _ranks(values: list[float]) -> list[float]:
    order = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and order[j + 1][1] == order[i][1]:
            j += 1
        rank = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[order[k][0]] = rank
        i = j + 1
    return ranks


def spearman(xs: list[float], ys: list[float]) -> float:
    if len(xs) < 2 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return 0.0
    rx = _ranks(xs)
    ry = _ranks(ys)
    x_mean = sum(rx) / len(rx)
    y_mean = sum(ry) / len(ry)
    num = sum((x - x_mean) * (y - y_mean) for x, y in zip(rx, ry))
    x_den = sum((x - x_mean) ** 2 for x in rx) ** 0.5
    y_den = sum((y - y_mean) ** 2 for y in ry) ** 0.5
    if x_den == 0 or y_den == 0:
        return 0.0
    return round(num / (x_den * y_den), 6)


def _monotonicity_violations(level_scores: list[tuple[float, float]], expected_direction: str, *, eps: float = 1e-6) -> int:
    ordered = sorted(level_scores)
    violations = 0
    for (_prev_level, prev_score), (_level, score) in zip(ordered, ordered[1:]):
        if expected_direction == "down" and score > prev_score + eps:
            violations += 1
        elif expected_direction == "stable" and abs(score - prev_score) > 0.15:
            violations += 1
    return violations


def summarize_calibration_rows(rows: Iterable[dict[str, object]], *, metrics: list[str] | None = None) -> list[dict[str, object]]:
    metrics = metrics or KEY_METRICS
    grouped: dict[tuple[str, str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        noise_type = str(row["noise_type"])
        target = str(row.get("noise_target", noise_target_side(noise_type)))
        quality = str(row.get("perturbation_quality", perturbation_quality(noise_type)))
        grouped[(noise_type, str(row["expected_direction"]), target, quality)].append(row)

    summary: list[dict[str, object]] = []
    for (noise_type, expected_direction, noise_target, quality), items in sorted(grouped.items()):
        baseline_items = [item for item in items if float(item["noise_level"]) == 0.0]
        for metric in metrics:
            metric_items = [item for item in items if item.get(metric) is not None]
            if not metric_items:
                continue
            xs = [float(item["noise_level"]) for item in metric_items]
            ys = [float(item[metric]) for item in metric_items]
            baseline = float(baseline_items[0][metric]) if baseline_items and baseline_items[0].get(metric) is not None else ys[0]
            max_delta = max(abs(score - baseline) for score in ys) if ys else 0.0
            level_scores = list(zip(xs, ys))
            summary.append(
                {
                    "noise_type": noise_type,
                    "noise_target": noise_target,
                    "perturbation_quality": quality,
                    "expected_direction": expected_direction,
                    "metric": metric,
                    "baseline": round(baseline, 6),
                    "min_score": round(min(ys), 6),
                    "max_score": round(max(ys), 6),
                    "final_score": round(ys[-1], 6),
                    "max_abs_delta_from_baseline": round(max_delta, 6),
                    "sensitivity_slope": _linear_slope(xs, ys),
                    "spearman_noise_score": spearman(xs, ys),
                    "monotonicity_violations": _monotonicity_violations(level_scores, expected_direction),
                }
            )
    return summary


def summarize_by_metric(summary_rows: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in summary_rows:
        grouped[str(row["metric"])].append(row)
    out: list[dict[str, object]] = []
    for metric, rows in sorted(grouped.items()):
        destructive = [row for row in rows if row["expected_direction"] == "down"]
        preserving = [row for row in rows if row["expected_direction"] == "stable"]
        out.append(
            {
                "metric": metric,
                "destructive_slope_avg": _safe_avg([float(row["sensitivity_slope"]) for row in destructive]),
                "destructive_spearman_avg": _safe_avg([float(row["spearman_noise_score"]) for row in destructive]),
                "destructive_violations": sum(int(row["monotonicity_violations"]) for row in destructive),
                "preserving_delta_avg": _safe_avg([float(row["max_abs_delta_from_baseline"]) for row in preserving]),
                "preserving_violations": sum(int(row["monotonicity_violations"]) for row in preserving),
            }
        )
    return out


def filter_summary_rows(
    summary_rows: Iterable[dict[str, object]],
    *,
    noise_target: str | None = None,
    expected_direction: str | None = None,
    include_qualities: set[str] | None = None,
) -> list[dict[str, object]]:
    rows = list(summary_rows)
    if noise_target is not None:
        rows = [row for row in rows if row.get("noise_target") == noise_target]
    if expected_direction is not None:
        rows = [row for row in rows if row.get("expected_direction") == expected_direction]
    if include_qualities is not None:
        rows = [row for row in rows if row.get("perturbation_quality") in include_qualities]
    return rows


def summarize_targeted_calibration(summary_rows: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    rows = list(summary_rows)
    out: list[dict[str, object]] = []
    for metric in KEY_METRICS:
        if metric in FORWARD_TEXT_METRICS:
            target = "text"
            target_rows = [row for row in rows if row.get("metric") == metric and row.get("noise_target") == "text"]
        elif metric in REVERSE_GRAPH_METRICS:
            target = "reconstructed_graph"
            target_rows = [row for row in rows if row.get("metric") == metric and row.get("noise_target") == "reconstructed_graph"]
        else:
            target = "all"
            target_rows = [row for row in rows if row.get("metric") == metric]
        destructive = [row for row in target_rows if row.get("expected_direction") == "down"]
        preserving = [row for row in target_rows if row.get("expected_direction") == "stable"]
        out.append(
            {
                "metric": metric,
                "recommended_noise_target": target,
                "destructive_slope_avg": _safe_avg([float(row["sensitivity_slope"]) for row in destructive]),
                "destructive_spearman_avg": _safe_avg([float(row["spearman_noise_score"]) for row in destructive]),
                "destructive_violations": sum(int(row["monotonicity_violations"]) for row in destructive),
                "preserving_delta_avg": _safe_avg([float(row["max_abs_delta_from_baseline"]) for row in preserving]),
                "preserving_violations": sum(int(row["monotonicity_violations"]) for row in preserving),
                "noise_type_count": len({str(row["noise_type"]) for row in target_rows}),
            }
        )
    return out


def relation_deletion_sanity(summary_rows: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    wanted = {"forward_lemon", "exact_label_coverage", "predicate_cue_coverage", "mine_fact_recoverability"}
    rows = [row for row in summary_rows if row.get("noise_type") == "delete_relation_phrase" and row.get("metric") in wanted]
    out = []
    for row in sorted(rows, key=lambda item: str(item["metric"])):
        baseline = float(row["baseline"])
        final = float(row["final_score"])
        out.append(
            {
                "metric": row["metric"],
                "baseline": round(baseline, 6),
                "final_score": round(final, 6),
                "delta": round(final - baseline, 6),
                "interpretation": "relation-sensitive" if row["metric"] != "exact_label_coverage" else "surface-control",
            }
        )
    return out
