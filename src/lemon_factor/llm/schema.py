"""Pydantic schemas for LLM-generated predicate decomposition candidates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from lemon_factor.factors.decomposition import FactorComponent, PredicateDecomposition, SemanticFactor


class LLMFactorComponent(BaseModel):
    """One factor proposed by an LLM for a predicate decomposition."""

    factor: str = Field(min_length=1)
    role: str = Field(min_length=1)
    weight: float = Field(gt=0.0, le=1.0)
    rationale: str | None = None


class LLMPredicateDecomposition(BaseModel):
    """Structured LLM response for one predicate."""

    predicate: str = Field(min_length=1)
    components: list[LLMFactorComponent] = Field(min_length=1)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    rationale: str = ""

    @model_validator(mode="after")
    def check_weight_mass(self) -> "LLMPredicateDecomposition":
        total = sum(component.weight for component in self.components)
        if abs(total - 1.0) > 1e-3:
            raise ValueError(f"LLM component weights must sum to 1.0, got {total}")
        return self


class LLMDecompositionRecord(BaseModel):
    """A model-tagged LLM decomposition suitable for JSONL storage."""

    model: str
    predicate: str
    decomposition: LLMPredicateDecomposition
    raw_response_id: str | None = None
    source: Literal["llm"] = "llm"
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMRawResponseRecord(BaseModel):
    """Audit record for raw LLM responses."""

    model: str
    predicate: str
    raw_response: dict[str, Any] | str
    parsed: bool
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


def decomposition_response_json_schema() -> dict[str, Any]:
    """Return a compact JSON schema for OpenRouter structured outputs."""

    return LLMPredicateDecomposition.model_json_schema()


def _factor_by_id(factors: list[SemanticFactor]) -> dict[str, SemanticFactor]:
    return {factor.id: factor for factor in factors}


def validate_against_factor_schema(
    candidate: LLMPredicateDecomposition,
    factors: list[SemanticFactor],
) -> PredicateDecomposition:
    """Validate an LLM candidate against the controlled factor schema.

    Returns a regular PredicateDecomposition with source='llm_candidate'. This
    makes downstream metric code independent of whether a candidate came from a
    rule or an LLM.
    """

    factors_by_id = _factor_by_id(factors)
    components: list[FactorComponent] = []
    for component in candidate.components:
        if component.factor not in factors_by_id:
            raise ValueError(f"Unknown factor: {component.factor}")
        allowed = {role for role in factors_by_id[component.factor].allowed_roles}
        if component.role not in allowed:
            raise ValueError(
                f"Role {component.role!r} is not allowed for factor {component.factor!r}"
            )
        components.append(
            FactorComponent(
                factor=component.factor,
                role=component.role,  # type: ignore[arg-type]
                weight=component.weight,
                rationale=component.rationale,
            )
        )
    return PredicateDecomposition(
        predicate=candidate.predicate,
        components=components,
        source="llm_candidate",
        confidence=candidate.confidence,
        evidence={"rationale": candidate.rationale},
    )


def read_llm_records(path: str | Path) -> list[LLMDecompositionRecord]:
    records: list[LLMDecompositionRecord] = []
    with Path(path).open("r", encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(LLMDecompositionRecord.model_validate_json(stripped))
            except Exception as exc:  # pragma: no cover - preserves line context
                raise ValueError(f"Invalid LLM record at {path}:{line_no}") from exc
    return records


def write_jsonl(path: str | Path, records: list[BaseModel | dict[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for record in records:
            if isinstance(record, BaseModel):
                payload = record.model_dump(mode="json")
            else:
                payload = record
            stream.write(json.dumps(payload, ensure_ascii=False) + "\n")
