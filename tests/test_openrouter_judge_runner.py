from __future__ import annotations

import json

from lemon_factor.reliability.run_openrouter_judge import (
    build_request_payload,
    extract_json_object,
    parse_judgment_from_response,
    repair_json_text,
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


def test_build_request_payload_contains_stable_json_features() -> None:
    payload = build_request_payload(
        _prompt_payload(),
        model="google/gemini-2.0-flash-001",
        judge_id="judge-a",
        prompt_style="strict",
        temperature=0.0,
        max_tokens=800,
        response_format_mode="json_schema",
        json_healing=True,
        require_parameters=True,
    )
    assert payload["model"] == "google/gemini-2.0-flash-001"
    assert payload["temperature"] == 0.0
    assert payload["stream"] is False
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["plugins"] == [{"id": "response-healing"}]
    assert payload["provider"] == {"require_parameters": True}
    assert payload["messages"][0]["role"] == "system"
    assert "item-1" in payload["messages"][1]["content"]
    assert "judge-a" in payload["messages"][1]["content"]


def test_extract_json_object_handles_fenced_output() -> None:
    parsed = extract_json_object('```json\n{"item_id":"item-1","decisions":[]}\n```')
    assert parsed["item_id"] == "item-1"


def test_extract_json_object_repairs_missing_comma_between_decisions() -> None:
    malformed = '''{
      "item_id": "item-1",
      "judge_id": "x",
      "decisions": [
        {"factor_id": "a", "decision": "covered"}
        {"factor_id": "b", "decision": "absent"}
      ]
    }'''
    repaired = repair_json_text(malformed)
    assert '},{' in repaired.replace("\n", "").replace(" ", "")
    parsed = extract_json_object(malformed)
    assert len(parsed["decisions"]) == 2


def test_parse_judgment_accepts_dict_decisions_and_repairs_judge_id() -> None:
    response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "item_id": "item-1",
                            "judge_id": "model-output-id",
                            "decisions": {
                                "negative_polarity::modifier": {"decision": "absent", "confidence": 0.91, "evidence": None},
                                "chemical::subject_domain": {"decision": "covered", "confidence": 0.88, "evidence": "Drug A"},
                            },
                        }
                    )
                }
            }
        ]
    }
    judgment = parse_judgment_from_response(response, _prompt_payload(), judge_id="openrouter_test", model="google/gemini-2.0-flash-001", prompt_style="strict")
    assert judgment.item_id == "item-1"
    assert judgment.judge_id == "openrouter_test"
    assert [decision.factor_id for decision in judgment.decisions] == ["chemical::subject_domain", "negative_polarity::modifier"]
    assert judgment.decisions[0].decision == "covered"
    assert judgment.decisions[1].decision == "absent"
    assert judgment.metadata["transport"] == "openrouter"
