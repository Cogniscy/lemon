import json
import subprocess
import sys
from pathlib import Path

import pytest

VARIANTS = ["node_deletion", "edge_deletion", "argument_swap", "polarity_flip", "relation_blur"]


def test_radar_generator_supports_legacy_input_with_honest_labels(tmp_path):
    pytest.importorskip("matplotlib", reason="Plot generation requires .[plots]")
    metrics = ["lemon_full", "mine_style", "triple_match", "entity_recall"]
    inputs = {
        "perturbation": {"metrics": metrics, "by_dataset": [], "by_dataset_variant": [],
            "by_variant": [{"variant": variant, **{key: {"mean_drop": 0.4, "n": 2}
                for key in metrics}} for variant in VARIANTS]},
        "embedding": {"backend": "char_ngram_vector_cosine", "backend_note": "Legacy ambiguous backend",
            "by_variant": [{"variant": variant, "mean_drop": 0.2, "n": 2} for variant in VARIANTS]},
        "layer-profile": {"status": "fixture"},
    }
    command = [sys.executable, "scripts/make_radar_profile.py"]
    for name, data in inputs.items():
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(data))
        command += ["--" + name, str(path)]
    command += ["--json", str(tmp_path / "output.json"), "--pdf", str(tmp_path / "output.pdf"),
                "--png", str(tmp_path / "output.png")]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    report = json.loads((tmp_path / "output.json").read_text())
    assert set(report["methods"]) == {"Damage proxy", "MINE-style", "Triple match", "Entity recall", "Vector cosine"}
    assert report["source_context"]["vector_algorithm"] == "unknown"
    assert len(report["axis_records"]) == 5
    assert all(value == 0.4 for value in report["methods"]["Damage proxy"].values())
    for suffix in ("pdf", "png"):
        assert (tmp_path / f"output.{suffix}").stat().st_size > 1000


@pytest.mark.artifacts("reports/radar_diagnostic_profile_values.json")
def test_historical_radar_is_retained():
    report = json.loads(Path("reports/radar_diagnostic_profile_values.json").read_text())
    assert "methods" in report
    assert set(report["methods"]) >= {"MINE-style", "Entity recall", "Vector cosine"}
    for values in report["methods"].values():
        assert all(0 <= value <= 1 for value in values.values())
