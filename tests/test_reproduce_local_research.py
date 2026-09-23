import json
import runpy
import subprocess
import sys
from pathlib import Path

from lemon_factor.scoring.score_perturbations import score_file

SCRIPT = Path("scripts/reproduce_local_research.py").resolve()


def prepare(root):
    helpers = runpy.run_path("tests/test_scoring_perturbations.py")
    inventory = helpers["_inventory"](root)
    first = helpers["_record"]()
    second = first.model_copy(update={"id": "second"})
    source = root / "input.jsonl"
    source.write_text(first.model_dump_json() + "\n" + second.model_dump_json() + "\n")
    report = score_file(source, inventory, dataset="drugprot", limit=1)
    report["input"] = "input.jsonl"
    report["inventory"] = "inventory.json"
    path = root / "historical.json"
    path.write_text(json.dumps(report))
    return path


def test_replay_with_relative_root_preserves_sample_count(tmp_path):
    prepare(tmp_path)
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", ".", "--reports", "historical.json",
         "--out", "results"], cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    manifest = json.loads((tmp_path / "results/manifest.json").read_text())
    assert manifest["datasets"][0]["records"] == 1
    ablation = json.loads((tmp_path / "results/ablation_summary.json").read_text())
    assert len(ablation["rows"]) == len(ablation["ablation_order"])
    again = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", ".", "--reports", "historical.json",
         "--out", "results"], cwd=tmp_path, capture_output=True, text=True,
    )
    assert again.returncode == 2
    assert json.loads((tmp_path / "results/manifest.json").read_text()) == manifest


def test_replay_rejects_mismatching_historical_scores(tmp_path):
    report_path = prepare(tmp_path)
    report = json.loads(report_path.read_text())
    report["rows"][0]["scores"]["factor_damage_proxy"] = 0.987
    report_path.write_text(json.dumps(report))
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(tmp_path), "--reports", "historical.json",
         "--out", str(tmp_path / "bad")], capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "differ from historical" in result.stderr
    assert not (tmp_path / "bad/manifest.json").exists()
