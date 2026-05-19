import json
from pathlib import Path

from lemon_factor.analysis.baseline_comparison import build_comparison_report, main, write_comparison_table


def _examples():
    return [
        {
            "id": "ex1",
            "dataset": "webnlg",
            "split": "dev",
            "nodes": [{"id": "n1", "label": "Alan Bean"}, {"id": "n2", "label": "Wheeler Texas"}],
            "edges": [{"subj": "n1", "pred": "birthPlace", "obj": "n2"}],
            "text": "Alan Bean was born in Wheeler, Texas.",
        }
    ]


def test_build_comparison_report_includes_lemon_and_token_baselines():
    baseline = {
        "examples": 1,
        "edges": 1,
        "exact_label_coverage": 1.0,
        "predicate_cue_coverage": 0.5,
        "lemon_factor_coverage": 0.6,
    }
    expanded = {**baseline, "predicate_cue_coverage": 1.0, "lemon_factor_coverage": 0.9}
    report = build_comparison_report(_examples(), baseline, expanded)
    methods = {row["metric_key"] for row in report["rows"]}
    assert "lemon_factor_coverage" in methods
    assert "token_cosine" in methods
    assert report["lexical_graph_text_baselines"]["token_cosine"] > 0.0


def test_write_comparison_table(tmp_path: Path):
    baseline = {
        "examples": 1,
        "edges": 1,
        "exact_label_coverage": 1.0,
        "predicate_cue_coverage": 0.5,
        "lemon_factor_coverage": 0.6,
    }
    report = build_comparison_report(_examples(), baseline, None)
    out = tmp_path / "table.md"
    write_comparison_table(report, out)
    text = out.read_text(encoding="utf-8")
    assert "LEMON-Factor coverage" in text
    assert "Graph-text token cosine" in text


def test_baseline_comparison_cli_writes_outputs(tmp_path: Path):
    jsonl = tmp_path / "data.jsonl"
    jsonl.write_text("\n".join(json.dumps(item) for item in _examples()) + "\n", encoding="utf-8")
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(
            {
                "examples": 1,
                "edges": 1,
                "exact_label_coverage": 1.0,
                "predicate_cue_coverage": 0.5,
                "lemon_factor_coverage": 0.6,
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "report.json"
    table = tmp_path / "table.md"
    main([str(jsonl), "--baseline-report", str(baseline), "--out", str(out), "--table", str(table)])
    assert out.exists()
    assert table.exists()
