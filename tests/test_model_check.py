from __future__ import annotations

import json

from lemon_factor.llm.model_check import (
    ModelCheckResult,
    catalog_by_id,
    check_models,
    supported_parameters,
    supports_structured_outputs,
    write_results,
)


def test_catalog_by_id_indexes_models():
    catalog = [{"id": "a/model"}, {"id": "b/model"}, {"name": "ignored"}]
    indexed = catalog_by_id(catalog)
    assert set(indexed) == {"a/model", "b/model"}


def test_supported_parameters_handles_missing_and_lists():
    assert supported_parameters({}) == ()
    assert supported_parameters({"supported_parameters": ["response_format", "tools"]}) == (
        "response_format",
        "tools",
    )


def test_supports_structured_outputs_from_supported_parameters():
    assert supports_structured_outputs({"supported_parameters": ["response_format"]}) is True
    assert supports_structured_outputs({"supported_parameters": ["tools"]}) is None


def test_supports_structured_outputs_from_capabilities():
    assert supports_structured_outputs({"capabilities": {"structured_outputs": True}}) is True


def test_check_models_marks_unavailable_and_available():
    results = check_models(
        ["available/model", "missing/model"],
        [{"id": "available/model", "supported_parameters": ["response_format"]}],
    )
    by_model = {result.model: result for result in results}
    assert by_model["available/model"].available is True
    assert by_model["available/model"].supports_structured_outputs is True
    assert by_model["missing/model"].available is False
    assert "not present" in by_model["missing/model"].reason


def test_write_results_creates_summary(tmp_path):
    path = tmp_path / "model_check.json"
    write_results(
        [
            ModelCheckResult("a", available=True, supports_structured_outputs=True),
            ModelCheckResult("b", available=False),
        ],
        path,
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["summary"]["total"] == 2
    assert payload["summary"]["available"] == 1
    assert payload["summary"]["unavailable"] == 1
    assert payload["summary"]["structured_explicit"] == 1
