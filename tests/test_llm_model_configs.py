from __future__ import annotations

from pathlib import Path

from lemon_factor.llm.decompose_predicates import read_model_config


ROOT = Path(__file__).resolve().parents[1]


def test_default_llm_model_config_is_small_for_debugging():
    models = read_model_config(ROOT / "configs" / "llm_models.yaml")
    assert models == ["meta-llama/llama-3.1-70b-instruct"]


def test_full_llm_model_config_keeps_multiple_models_for_final_results():
    models = read_model_config(ROOT / "configs" / "llm_models_full.yaml")
    assert len(models) >= 3


def test_sanity_llm_model_config_has_two_validated_models():
    models = read_model_config(ROOT / "configs" / "llm_models_sanity.yaml")
    assert models == [
        "meta-llama/llama-3.1-70b-instruct",
        "anthropic/claude-3.5-haiku",
    ]
