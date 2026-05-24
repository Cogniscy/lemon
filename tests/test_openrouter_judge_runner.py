from __future__ import annotations

import json

from lemon_factor.reliability.run_openrouter_judge import (
    build_request_payload,
    extract_json_object,
    parse_judgment_from_response,
    response_format,
)


def _prompt_payload() -> dict:
    return {
        "item_id": "item-1",
        "dataset": "drugprot",
        "variant": "polarity_flip",
        "source_edge": {"subject": "Drug A", "predicate": "chemical_inhibits_gene_or_protein", "object": "Protein B"},
        "original_text": "Drug A inhibits Protein B.",
        "perturbed_text": "Drug A activates Protein B.",
        "factors": [
            {"id": "chemical::subject_domain", "label": "Chemical", "role": "subject_domain", "group": "participant_roles", "weight": 0.2},
            {"id": "negative_polarity::modifier", "label": "Negative polarity", "role": "modifier", "group": "polarity", "weight": 0.2},
        ],
    }


def test_response_format_modes() -> None:
    assert response_format("none") is None
    assert response_format("json_object") == {"type": "json_object"}
    schema = response_format("json_schema")
    assert schema is not None
    assert schema["type"] == "json_schema"
    assert schema["json_schema"]["schema"]["properties"]["decisions"]["type"] == "array"


def test_build_request_payload_contains_openrouter_chat_fields() -> None:
    payload = build_request_payload(
        _prompt_payload(),
        model="openrouter/auto",
        prompt_style="strict",
        temperature=0.0,
        max_tokens=800,
        response_format_mode="json_object",
    )
    assert payload["model"] == "openrouter/auto"
    assert payload["temperature"] == 0.0
    assert payload["response_format"] == {"type": "json_object"}
    assert payload["messages"][0]["role"] == "system"
    assert "item-1" in payload["messages"][1]["content"]


def test_extract_json_object_handles_fenced_output() -> None:
    parsed = extract_json_object('```json\n{"item_id":"item-1","decisions":[]}\n```')
    assert parsed["item_id"] == "item-1"


def test_parse_judgment_repairs_judge_id_and_preserves_factor_order() -> None:
    response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "item_id": "item-1",
                            "judge_id": "model-output-id",
                            "decisions": [
                                {"factor_id": "negative_polarity::modifier", "decision": "absent", "confidence": 0.91, "evidence": None},
                                {"factor_id": "chemical::subject_domain", "decision": "covered", "confidence": 0.88, "evidence": "Drug A"},
                            ],
                        }
                    )
                }
            }
        ]
    }
    judgment = parse_judgment_from_response(response, _prompt_payload(), judge_id="openrouter_test", model="openrouter/auto", prompt_style="strict")
    assert judgment.item_id == "item-1"
    assert judgment.judge_id == "openrouter_test"
    assert [decision.factor_id for decision in judgment.decisions] == ["chemical::subject_domain", "negative_polarity::modifier"]
    assert judgment.decisions[0].decision == "covered"
    assert judgment.decisions[1].decision == "absent"
    assert judgment.metadata["transport"] == "openrouter"
