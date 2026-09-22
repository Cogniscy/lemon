import json
from pathlib import Path

from lemon_factor.analysis.recompute_paper_aggregates import (
    compute_ablation_gain,
    compute_llm_compact,
    compute_sensitivity,
)


def test_compute_sensitivity_uses_drop_direction() -> None:
    rows = [
        {"dataset": "d", "variant": "node_deletion", "scores": {"entity_recall": 0.25, "factor_damage_proxy": 0.75}},
        {"dataset": "d", "variant": "node_deletion", "scores": {"entity_recall": 0.75, "factor_damage_proxy": 0.25}},
    ]
    out = compute_sensitivity(rows, ["entity_recall", "factor_damage_proxy"])
    node = out["by_variant"][0]
    assert node["variant"] == "node_deletion"
    assert round(node["entity_recall"]["mean_drop"], 3) == 0.5
    assert round(node["factor_damage_proxy"]["mean_drop"], 3) == 0.5


def test_compute_ablation_gain(tmp_path: Path) -> None:
    path = tmp_path / "ablation.json"
    path.write_text(json.dumps({
        "summary": [
            {"ablation": "full", "datasets": {"d": {"mean_drop": 0.4, "records": 2}}},
            {"ablation": "minus_roles", "datasets": {"d": {"mean_drop": 0.1, "records": 2}}},
        ]
    }), encoding="utf-8")
    out = compute_ablation_gain(path)
    minus = [r for r in out["rows"] if r["ablation"] == "minus_roles"][0]
    assert round(minus["mean_gain_vs_full"], 3) == 0.3


def test_compute_llm_compact(tmp_path: Path) -> None:
    path = tmp_path / "llm.json"
    path.write_text(json.dumps({
        "item_count": 10,
        "judgment_count": 6,
        "judge_count": 3,
        "summary": [
            {"dataset": "d", "variant": "v", "mean_llm_score": 0.5, "pairwise_agreement": 0.25, "deterministic_agreement": 0.75, "factor_votes": 4},
            {"dataset": "d", "variant": "w", "mean_llm_score": 1.0, "pairwise_agreement": None, "deterministic_agreement": 0.5, "factor_votes": 2},
        ],
    }), encoding="utf-8")
    out = compute_llm_compact(path)
    assert round(out["overall"]["mean_llm_score"], 3) == 0.667
    assert round(out["overall"]["pairwise_agreement_overlap"], 3) == 0.25
