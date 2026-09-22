import pytest
import json
from pathlib import Path


@pytest.mark.artifacts("reports/layer_profile_values.json")
def test_layer_profile_values_are_documented_and_bounded():
    path = Path("reports/layer_profile_values.json")
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["status"] == "draft_source_for_radar"
    assert "not absolute accuracy" in data["note"]
    axes = {row["axis"] for row in data["layers"]}
    required = {
        "entity/domain sensitivity",
        "predicate-cue sensitivity",
        "role/argument sensitivity",
        "polarity sensitivity",
        "relation-blur sensitivity",
        "role ablation gain",
        "determinism",
    }
    assert required <= axes
    for row in data["layers"]:
        assert 0.0 <= row["value"] <= 1.0
        assert row["source_report"].startswith("reports/") or row["source_report"].startswith("paper/")
        assert row["safe_interpretation"]


def test_layer_profile_table_source_is_retained_but_not_required_in_paper():
    results = Path("paper/sections/06_results.tex").read_text(encoding="utf-8")
    assert "entity/domain support" in results
    assert "table_layer_profile" not in results
    table = Path("paper/tables/table_layer_profile.tex").read_text(encoding="utf-8")
    for term in ["Entity/domain", "Predicate cue", "Role/arg.", "Polarity"]:
        assert term in table
