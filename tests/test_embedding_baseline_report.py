import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


def load_script():
    name = "lemon_embedding_script"
    spec = importlib.util.spec_from_file_location(name, "scripts/run_embedding_baseline.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.artifacts("reports/embedding_baseline_perturbation.json")
def test_historical_embedding_report():
    report = json.loads(Path("reports/embedding_baseline_perturbation.json").read_text())
    assert report["n_pairs"] > 0
    for row in report["by_variant"]:
        assert 0 <= row["mean_cosine"] <= 1
        assert 0 <= row["mean_drop"] <= 1


def test_embedding_script_runs_without_datasets(tmp_path):
    source = tmp_path / "pairs.jsonl"
    module = load_script()
    source.write_text("\n".join(json.dumps({
        "id": variant, "dataset": "synthetic", "variant": variant,
        "original_text": "Alex was born in Cedar Bay.", "text": "Alex visited Cedar Bay.",
    }) for variant in module.VARIANT_LABELS), encoding="utf-8")
    report_path = tmp_path / "result.json"
    result = subprocess.run([
        sys.executable, "scripts/run_embedding_baseline.py", "--backend", "hashed-char",
        "--json", str(report_path), "--md", str(tmp_path / "result.md"), str(source),
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    report = json.loads(report_path.read_text())
    assert report["backend"] == "hashed_char_cosine"
    assert report["n_pairs"] == 5
    import hashlib
    assert list(report["input_sha256"].values()) == [hashlib.sha256(source.read_bytes()).hexdigest()]
    assert report["backend_params"]["fit_scope"] == "none"


def test_legacy_backend_requires_explicit_choice():
    result = subprocess.run([
        sys.executable, "scripts/run_embedding_baseline.py", "--backend", "hash-char",
    ], capture_output=True, text=True)
    assert result.returncode != 0
    assert "choose hashed-char or tfidf-char" in result.stderr


def test_hashed_backend_is_deterministic_and_does_not_import_sklearn(monkeypatch):
    import builtins
    module = load_script()
    original = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name.startswith("sklearn"):
            raise AssertionError("Hashed backend must not import sklearn")
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", guarded)
    pairs = [module.Pair("x", "demo", "node_deletion", "same text", "same text")]
    first = module.hashed_char_cosines(pairs)
    assert first == module.hashed_char_cosines(pairs)
    assert first[0] == pytest.approx(1)


def test_tfidf_missing_dependency_has_no_fallback(monkeypatch):
    import builtins
    module = load_script()
    original = builtins.__import__
    def guarded(name, *args, **kwargs):
        if name.startswith("sklearn"):
            raise ImportError("unavailable")
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", guarded)
    with pytest.raises(RuntimeError, match="requires scikit-learn"):
        module.tfidf_char_cosines([])
