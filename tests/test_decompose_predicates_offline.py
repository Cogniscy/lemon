from __future__ import annotations

import json

from lemon_factor.factors.inventory import FactorInventory, PredicateInventoryItem
from lemon_factor.factors.seed_schema import build_default_factor_schema
from lemon_factor.factors.decomposition import write_factor_schema
from lemon_factor.llm.decompose_predicates import build_prompt_payloads, read_model_config, read_offline_fixture


def test_read_model_config(tmp_path):
    path = tmp_path / "models.yaml"
    path.write_text("models:\n  - model/a\n  - model/b\n", encoding="utf-8")
    assert read_model_config(path) == ["model/a", "model/b"]


def test_build_prompt_payloads(tmp_path):
    schema_path = tmp_path / "schema.json"
    write_factor_schema(schema_path, build_default_factor_schema())
    inventory = FactorInventory(
        predicates={
            "birthPlace": PredicateInventoryItem(
                predicate="birthPlace",
                count=10,
                categories={"Astronaut": 10},
                candidate_factors=["birth", "place"],
                examples=[],
            )
        }
    )
    records = build_prompt_payloads(inventory, schema_path, models=["model/a", "model/b"], limit=1)
    assert len(records) == 2
    assert records[0]["predicate"] == "birthPlace"
    assert "response_format" in records[0]["payload"]


def test_read_offline_fixture_validates_candidates(tmp_path):
    schema_path = tmp_path / "schema.json"
    write_factor_schema(schema_path, build_default_factor_schema())
    fixture_path = tmp_path / "fixture.jsonl"
    content = {
        "predicate": "birthPlace",
        "components": [
            {"factor": "biographical_relation", "role": "predicate_meaning", "weight": 0.5},
            {"factor": "person", "role": "subject_domain", "weight": 0.2},
            {"factor": "place", "role": "object_domain", "weight": 0.3},
        ],
        "confidence": 0.9,
        "rationale": "ok",
    }
    fixture_path.write_text(
        json.dumps({"model": "fixture/model", "predicate": "birthPlace", "content": json.dumps(content)}) + "\n",
        encoding="utf-8",
    )
    candidates, raw = read_offline_fixture(fixture_path, factors_path=schema_path)
    assert len(candidates) == 1
    assert len(raw) == 1
    assert raw[0].parsed is True
    assert candidates[0].model == "fixture/model"
