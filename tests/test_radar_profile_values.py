import json
import subprocess
import sys
from pathlib import Path


def test_radar_profile_generator_outputs_documented_values(tmp_path):
    out_json = tmp_path / "radar.json"
    out_pdf = tmp_path / "radar.pdf"
    out_png = tmp_path / "radar.png"
    subprocess.run(
        [
            sys.executable,
            "scripts/make_radar_profile.py",
            "--json",
            str(out_json),
            "--pdf",
            str(out_pdf),
            "--png",
            str(out_png),
        ],
        check=True,
    )
    assert out_json.exists()
    assert out_pdf.exists() and out_pdf.stat().st_size > 1000
    assert out_png.exists() and out_png.stat().st_size > 1000

    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["status"] == "passed"
    assert "not absolute accuracy" in data["note"]
    assert "reports/paper_metric_sensitivity_drops.json" in data["source_files"]
    assert "reports/layer_profile_values.json" in data["source_files"]
    assert data["axes"] == [
        "Node deletion",
        "Edge deletion",
        "Argument swap",
        "Polarity flip",
        "Relation blur",
    ]
    assert set(data["methods"]) == {"LEMON-Factor", "Entity recall", "Triple match"}
    for method_values in data["methods"].values():
        assert set(method_values) == set(data["axes"])
        for value in method_values.values():
            assert 0.0 <= value <= 1.0
    for record in data["axis_records"]:
        assert record["source_report"] == "reports/paper_metric_sensitivity_drops.json"
        assert record["normalization_rule"]
        for cell in record["values"].values():
            assert 0.0 <= cell["value"] <= 1.0
            assert cell["n"] > 0


def test_radar_profile_figure_is_included_in_paper():
    results = Path("paper/sections/06_results.tex").read_text(encoding="utf-8")
    assert "figure_radar_diagnostic_profile.pdf" in results
    assert "fig:radar-diagnostic-profile" in results
    assert "not be read as an absolute accuracy comparison" in results

    report = json.loads(Path("reports/radar_diagnostic_profile_values.json").read_text(encoding="utf-8"))
    assert report["figure"]["pdf"] == "paper/figures/figure_radar_diagnostic_profile.pdf"
    assert Path(report["figure"]["pdf"]).exists()
    assert Path(report["figure"]["png"]).exists()
