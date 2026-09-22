"""Build the LEMON-Factor diagnostic profile figure.

The figure is intentionally a compact matrix over controlled perturbation
variants, not an absolute accuracy leaderboard. Values are mean score drops
under controlled semantic damage, so larger values mean stronger scalar
sensitivity to that perturbation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lemon_factor.scoring.report_schema import normalize_sensitivity_report

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parents[1]
PERTURBATION_REPORT = ROOT / "reports" / "paper_metric_sensitivity_drops.json"
EMBEDDING_REPORT = ROOT / "reports" / "embedding_baseline_perturbation.json"
LAYER_PROFILE = ROOT / "reports" / "layer_profile_values.json"
OUT_JSON = ROOT / "artifacts" / "radar_diagnostic_profile_values.json"
OUT_PDF = ROOT / "artifacts" / "figure_radar_diagnostic_profile.pdf"
OUT_PNG = ROOT / "artifacts" / "figure_radar_diagnostic_profile.png"

AXES = [
    ("Node deletion", "node_deletion"),
    ("Edge deletion", "edge_deletion"),
    ("Argument swap", "argument_swap"),
    ("Polarity flip", "polarity_flip"),
    ("Relation blur", "relation_blur"),
]
PLOT_AXIS_LABELS = ["Node\ndeletion", "Edge\ndeletion", "Argument\nswap", "Polarity\nflip", "Relation\nblur"]

METHODS = [
    ("Damage proxy", "factor_damage_proxy", "reports/paper_metric_sensitivity_drops.json"),
    ("MINE-style", "mine_style", "reports/paper_metric_sensitivity_drops.json"),
    ("Triple match", "triple_match", "reports/paper_metric_sensitivity_drops.json"),
    ("Entity recall", "entity_recall", "reports/paper_metric_sensitivity_drops.json"),
    ("Vector cosine", "vector_cosine", "reports/embedding_baseline_perturbation.json"),
]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_values(perturbation_path=PERTURBATION_REPORT, embedding_path=EMBEDDING_REPORT, layer_path=LAYER_PROFILE) -> dict[str, Any]:
    perturbation = normalize_sensitivity_report(_read_json(perturbation_path))
    embedding = _read_json(embedding_path)
    layer_profile = _read_json(layer_path)
    by_variant = {row["variant"]: row for row in perturbation["by_variant"]}
    vector_by_variant = {row["variant"]: row for row in embedding["by_variant"]}

    def source_name(path):
        path = Path(path).resolve()
        return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
    sources = {
        "reports/paper_metric_sensitivity_drops.json": source_name(perturbation_path),
        "reports/embedding_baseline_perturbation.json": source_name(embedding_path),
        "reports/layer_profile_values.json": source_name(layer_path),
    }
    axis_rows: list[dict[str, Any]] = []
    methods: dict[str, dict[str, float]] = {name: {} for name, _, _ in METHODS}

    for axis_label, variant in AXES:
        row = by_variant[variant]
        vector_row = vector_by_variant[variant]
        axis_record = {
            "axis": axis_label,
            "variant": variant,
            "normalization_rule": "mean_drop under a controlled perturbation; larger means stronger response to induced damage",
            "values": {},
        }
        for method_name, metric_key, source_report in METHODS:
            if metric_key == "vector_cosine":
                value = float(vector_row["mean_drop"])
                n_value = vector_row.get("n")
                backend = embedding.get("backend")
            else:
                value = float(row[metric_key]["mean_drop"])
                n_value = row[metric_key].get("n")
                backend = None
            rounded = round(value, 4)
            methods[method_name][axis_label] = rounded
            cell = {
                "value": rounded,
                "metric_key": metric_key,
                "source_report": sources[source_report],
                "n": n_value,
            }
            if backend:
                cell["backend"] = backend
            axis_record["values"][method_name] = cell
        axis_rows.append(axis_record)

    return {
        "status": "passed",
        "figure": {
            "pdf": "paper/figures/figure_radar_diagnostic_profile.pdf",
            "png": "paper/figures/figure_radar_diagnostic_profile.png",
            "style": "annotated_matrix",
        },
        "note": (
            "Figure values are mean drops under controlled perturbations, not "
            "absolute accuracy scores. Larger values mean stronger scalar "
            "sensitivity to that controlled semantic damage. The profile is "
            "diagnostic, not a global metric leaderboard."
        ),
        "axes": [label for label, _ in AXES],
        "methods": methods,
        "axis_records": axis_rows,
        "source_files": list(sources.values()),
        "source_context": {
            "layer_profile_status": layer_profile.get("status"),
            "layer_profile_note": layer_profile.get("note"),
            "vector_backend": embedding.get("backend"),
            "vector_algorithm": "unknown" if embedding.get("backend") == "char_ngram_vector_cosine" else embedding.get("backend"),
            "vector_backend_note": embedding.get("backend_note"),
            "vector_definition": embedding.get("definition"),
        },
        "safe_interpretation": (
            "MINE-style and triple-match are harsher scalar detectors under "
            "controlled perturbations. The damage proxy is less harsh in aggregate, "
            "but the proxy response is prescribed by intended damage metadata for "
            "roles, polarity, direction, and evidence when those dimensions are encoded."
        ),
        "do_not_claim": [
            "Do not interpret the figure as absolute accuracy.",
            "Do not claim empirical superiority over embeddings from this figure.",
            "Do not describe Vector cosine as a dense embedding unless the dense backend was run and materialized.",
            "Do not claim universal polarity handling; it depends on the factor inventory.",
            "Do not present the profile as a leaderboard across all metrics.",
        ],
    }


def plot(values: dict[str, Any], out_pdf: Path = OUT_PDF, out_png: Path = OUT_PNG) -> None:
    axis_names = values["axes"]
    method_names = list(values["methods"].keys())
    matrix = np.array([[values["methods"][method][axis] for axis in axis_names] for method in method_names])

    cmap = LinearSegmentedColormap.from_list(
        "lemon_profile",
        ["#f7fbff", "#deebf7", "#9ecae1", "#3182bd", "#08519c"],
    )

    fig, ax = plt.subplots(figsize=(5.65, 2.9), dpi=220)
    im = ax.imshow(matrix, cmap=cmap, vmin=0.0, vmax=0.75, aspect="auto")

    ax.set_xticks(np.arange(len(axis_names)))
    ax.set_xticklabels(PLOT_AXIS_LABELS, fontsize=7)
    ax.set_yticks(np.arange(len(method_names)))
    ax.set_yticklabels(method_names, fontsize=7)
    ax.tick_params(top=False, bottom=True, left=True, right=False, length=0)

    for idx, label in enumerate(ax.get_yticklabels()):
        method_name = method_names[idx]
        label.set_color("black")
        if method_name == "LEMON-Factor":
            label.set_fontweight("bold")

    ax.set_xticks(np.arange(-0.5, len(axis_names), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(method_names), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.2)
    ax.tick_params(which="minor", bottom=False, left=False)

    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            value = matrix[i, j]
            text_color = "white" if value >= 0.42 else ("#08306b" if value >= 0.16 else "#222222")
            weight = "bold" if method_names[i] == "LEMON-Factor" else "normal"
            ax.text(j, i, f"{value:.3f}", ha="center", va="center", fontsize=6.4, color=text_color, fontweight=weight)

    lemon_idx = method_names.index("Damage proxy")
    ax.add_patch(plt.Rectangle((-0.5, lemon_idx - 0.5), len(axis_names), 1, fill=False, edgecolor="#0b4f8a", linewidth=1.6))

    cbar = fig.colorbar(im, ax=ax, fraction=0.05, pad=0.02)
    cbar.ax.tick_params(labelsize=6)
    cbar.set_label("Mean score drop", fontsize=7)

    fig.text(
        0.125,
        0.02,
        "Higher values indicate stronger scalar sensitivity to induced damage; they do not by themselves indicate a better metric.",
        fontsize=6.1,
    )
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_pdf, bbox_inches="tight")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the LEMON-Factor diagnostic profile figure.")
    parser.add_argument("--json", type=Path, default=OUT_JSON, help="Output JSON path.")
    parser.add_argument("--pdf", type=Path, default=OUT_PDF, help="Output PDF figure path.")
    parser.add_argument("--png", type=Path, default=OUT_PNG, help="Output PNG figure path.")
    parser.add_argument("--perturbation", type=Path, default=PERTURBATION_REPORT)
    parser.add_argument("--embedding", type=Path, default=EMBEDDING_REPORT)
    parser.add_argument("--layer-profile", type=Path, default=LAYER_PROFILE)
    args = parser.parse_args()

    values = build_values(args.perturbation, args.embedding, args.layer_profile)
    values["figure"]["pdf"] = str(args.pdf)
    values["figure"]["png"] = str(args.png)
    _write_json(args.json, values)
    plot(values, args.pdf, args.png)
    print(f"Wrote {args.json}")
    print(f"Wrote {args.pdf}")
    print(f"Wrote {args.png}")


if __name__ == "__main__":
    main()
