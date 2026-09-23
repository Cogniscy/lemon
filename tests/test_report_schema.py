import copy
import pytest
from lemon_factor.scoring.report_schema import normalize_scoring_report, normalize_sensitivity_report


def legacy():
    return {
        "input": "input.jsonl", "inventory": "inventory.json", "metrics": ["lemon_full"],
        "rows": [{"scores": {"lemon_full": 0.4}}],
        "summary": [{"metrics": {"lemon_full": 0.4}}],
    }


def test_legacy_migration_is_lossless_and_non_mutating():
    report = legacy()
    before = copy.deepcopy(report)
    result = normalize_scoring_report(report)
    assert report == before
    assert result["rows"][0]["scores"] == {"factor_damage_proxy": 0.4}
    assert result["summary"][0]["metrics"] == {"factor_damage_proxy": 0.4}
    assert normalize_scoring_report(result) == result


def test_conflicting_keys_and_unknown_reports_rejected():
    report = legacy()
    report["rows"][0]["scores"]["factor_damage_proxy"] = 0.9
    with pytest.raises(ValueError, match="Conflicting"):
        normalize_scoring_report(report)
    with pytest.raises(ValueError, match="Expected"):
        normalize_scoring_report({"lemon_full": 0.4})
    report = legacy()
    report["schema_version"] = "future"
    with pytest.raises(ValueError, match="Unsupported"):
        normalize_scoring_report(report)


def test_sensitivity_preserves_nested_statistics():
    report = {
        "metrics": ["lemon_full"], "by_variant": [{"variant": "x", "lemon_full": {"n": 5, "mean_drop": 0.6}}],
        "by_dataset": [], "by_dataset_variant": [],
    }
    result = normalize_sensitivity_report(report)
    assert result["by_variant"][0]["factor_damage_proxy"] == {"n": 5, "mean_drop": 0.6}
    assert normalize_sensitivity_report(result) == result
