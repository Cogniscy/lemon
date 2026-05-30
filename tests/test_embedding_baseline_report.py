import json
import subprocess
import sys
from pathlib import Path


def test_embedding_baseline_report_is_materialized_and_bounded():
    report_path = Path("reports/embedding_baseline_perturbation.json")
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "passed"
    assert report["backend"] in {"char_ngram_vector_cosine", "sentence_transformer_cosine"}
    assert "not be read as a complete comparison" in report["safe_interpretation"]
    assert report["n_pairs"] > 0
    assert {row["variant"] for row in report["by_variant"]} == {
        "node_deletion",
        "edge_deletion",
        "argument_swap",
        "polarity_flip",
        "relation_blur",
    }
    for row in report["by_variant"]:
        assert row["n"] > 0
        assert 0.0 <= row["mean_cosine"] <= 1.0
        assert 0.0 <= row["mean_drop"] <= 1.0
        assert 0.0 <= row["std_drop"] <= 1.0


def test_embedding_baseline_script_runs_on_small_sample(tmp_path):
    out_json = tmp_path / "embedding.json"
    out_md = tmp_path / "embedding.md"
    subprocess.run(
        [
            sys.executable,
            "scripts/run_embedding_baseline.py",
            "--limit-per-variant",
            "1",
            "--json",
            str(out_json),
            "--md",
            str(out_md),
        ],
        check=True,
    )
    report = json.loads(out_json.read_text(encoding="utf-8"))
    assert report["status"] == "passed"
    assert report["backend"] == "char_ngram_vector_cosine"
    assert out_md.exists()
    assert len(report["by_variant"]) == 5


def test_reproducibility_docs_mention_embedding_baseline():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "python scripts/run_embedding_baseline.py" in readme
    assert "reports/embedding_baseline_perturbation.json" in readme

    audit = Path("docs/CLAIMS_AND_METRICS_AUDIT.md").read_text(encoding="utf-8")
    assert "Vector-space perturbation baseline" in audit
    assert "not a dense sentence embedding" in audit
