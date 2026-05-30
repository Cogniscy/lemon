"""Build the LEMON-Factor diagnostic radar chart.

The chart is intentionally a diagnostic profile over controlled perturbation
variants, not an absolute accuracy leaderboard. Values are mean score drops
under controlled semantic damage, so larger values mean stronger sensitivity to
that perturbation.
"""

from __future__ import annotations

import argparse
import json
from math import pi
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
PERTURBATION_REPORT = ROOT / "reports" / "paper_metric_sensitivity_drops.json"
LAYER_PROFILE = ROOT / "reports" / "layer_profile_values.json"
OUT_JSON = ROOT / "reports" / "radar_diagnostic_profile_values.json"
OUT_PDF = ROOT / "paper" / "figures" / "figure_radar_diagnostic_profile.pdf"
OUT_PNG = ROOT / "paper" / "figures" / "figure_radar_diagnostic_profile.png"

AXES = [
    ("Node deletion", "node_deletion"),
    ("Edge deletion", "edge_deletion"),
    ("Argument swap", "argument_swap"),
    ("Polarity flip", "polarity_flip"),
    ("Relation blur", "relation_blur"),
]

METHODS = [
    ("LEMON-Factor", "lemon_full"),
    ("Entity recall", "entity_recall"),
    ("Triple match", "triple_match"),
]

METHOD_STYLES = {
    "LEMON-Factor": {"color": "#1f77b4", "linestyle": "-", "linewidth": 2.3},
    "Entity recall": {"color": "#7f7f7f", "linestyle": "--", "linewidth": 1.8},
    "Triple match": {"color": "#d62728", "linestyle": ":", "linewidth": 2.1},
}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_values() -> dict[str, Any]:
    perturbation = _read_json(PERTURBATION_REPORT)
    layer_profile = _read_json(LAYER_PROFILE)
    by_variant = {row["variant"]: row for row in perturbation["by_variant"]}

    axis_rows: list[dict[str, Any]] = []
    methods: dict[str, dict[str, float]] = {name: {} for name, _ in METHODS}

    for axis_label, variant in AXES:
        row = by_variant[variant]
        axis_record = {
            "axis": axis_label,
            "variant": variant,
            "source_report": "reports/paper_metric_sensitivity_drops.json",
            "normalization_rule": perturbation["definition"],
            "values": {},
        }
        for method_name, metric_key in METHODS:
            value = float(row[metric_key]["mean_drop"])
            rounded = round(value, 4)
            methods[method_name][axis_label] = rounded
            axis_record["values"][method_name] = {
                "value": rounded,
                "metric_key": metric_key,
                "n": row[metric_key].get("n"),
            }
        axis_rows.append(axis_record)

    output = {
        "status": "passed",
        "figure": {
            "pdf": "paper/figures/figure_radar_diagnostic_profile.pdf",
            "png": "paper/figures/figure_radar_diagnostic_profile.png",
        },
        "note": (
            "Radar values are mean drops under controlled perturbations, not "
            "absolute accuracy scores. Larger values mean stronger sensitivity "
            "to that controlled semantic damage. The profile is diagnostic, not "
            "a global metric leaderboard."
        ),
        "axes": [label for label, _ in AXES],
        "methods": methods,
        "axis_records": axis_rows,
        "source_files": [
            "reports/paper_metric_sensitivity_drops.json",
            "reports/layer_profile_values.json",
        ],
        "source_context": {
            "layer_profile_status": layer_profile.get("status"),
            "layer_profile_note": layer_profile.get("note"),
        },
        "safe_interpretation": (
            "LEMON-Factor provides a relation-factor diagnostic profile. It is "
            "not always the harshest scalar response, but unlike entity-only or "
            "triple-style scores it is tied to factor traces that identify roles, "
            "polarity, direction, and evidence when those dimensions are encoded."
        ),
        "do_not_claim": [
            "Do not interpret radar values as absolute accuracy.",
            "Do not claim empirical superiority over embeddings from this figure.",
            "Do not claim universal polarity handling; it depends on the factor inventory.",
            "Do not present the profile as a leaderboard across all metrics.",
        ],
    }
    return output


def plot(values: dict[str, Any], out_pdf: Path = OUT_PDF, out_png: Path = OUT_PNG) -> None:
    axes = values["axes"]
    n_axes = len(axes)
    angles = [idx / float(n_axes) * 2 * pi for idx in range(n_axes)]
    closed_angles = angles + angles[:1]

    fig = plt.figure(figsize=(4.3, 3.2), dpi=220)
    ax = plt.subplot(111, polar=True)
    ax.set_theta_offset(pi / 2)
    ax.set_theta_direction(-1)

    ax.set_xticks(angles)
    ax.set_xticklabels(axes, fontsize=7)
    ax.set_ylim(0, 0.75)
    ax.set_yticks([0.25, 0.50, 0.75])
    ax.set_yticklabels(["0.25", "0.50", "0.75"], fontsize=6)
    ax.grid(True, linewidth=0.6, alpha=0.55)

    for method_name, axis_values in values["methods"].items():
        series = [axis_values[axis] for axis in axes]
        closed_series = series + series[:1]
        style = METHOD_STYLES.get(method_name, {})
        ax.plot(closed_angles, closed_series, label=method_name, **style)
        if method_name == "LEMON-Factor":
            ax.fill(closed_angles, closed_series, alpha=0.08, color=style.get("color", "#1f77b4"))

    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.22), ncol=3, fontsize=6, frameon=False)
    fig.tight_layout(pad=0.45)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_pdf, bbox_inches="tight")
    fig.savefig(out_png, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the LEMON-Factor diagnostic radar profile.")
    parser.add_argument("--json", type=Path, default=OUT_JSON, help="Output JSON path.")
    parser.add_argument("--pdf", type=Path, default=OUT_PDF, help="Output PDF figure path.")
    parser.add_argument("--png", type=Path, default=OUT_PNG, help="Output PNG figure path.")
    args = parser.parse_args()

    values = build_values()
    _write_json(args.json, values)
    plot(values, args.pdf, args.png)
    print(f"Wrote {args.json}")
    print(f"Wrote {args.pdf}")
    print(f"Wrote {args.png}")


if __name__ == "__main__":
    main()
