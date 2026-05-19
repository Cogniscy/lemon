"""Schemas for strong-LLM synthetic adjudication."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from lemon_factor.factors.decomposition import FactorComponent, PredicateDecomposition, SemanticFactor

AdjudicationStatus = Literal[
    "accepted_seed",
    "accepted_llm",
    "modified",
    "rejected_unclear",
    "needs_schema_change",
]


class LLMAdjudicationDecision(BaseModel):
    """Structured strong-LLM decision for one predicate decomposition."""

    predicate: str = Field(min_length=1)
    status: AdjudicationStatus
    components: list[FactorComponent] = Field(min_length=1)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    selected_sources: list[str] = Field(default_factory=list)
    rationale: str = ""

    @model_validator(mode="after")
    def check_weight_mass(self) -> "LLMAdjudicationDecision":
        total = sum(component.weight for component in self.components)
        if abs(total - 1.0) > 1e-3:
            raise ValueError(f"Adjudication component weights must sum to 1.0, got {total}")
        return self


def adjudication_response_json_schema() -> dict:
    return LLMAdjudicationDecision.model_json_schema()


def validate_adjudication_against_schema(
    decision: LLMAdjudicationDecision,
    factors: list[SemanticFactor],
    *,
    evidence: dict | None = None,
) -> PredicateDecomposition:
    factors_by_id = {factor.id: factor for factor in factors}
    for component in decision.components:
        if component.factor not in factors_by_id:
            raise ValueError(f"Unknown factor: {component.factor}")
        allowed = set(factors_by_id[component.factor].allowed_roles)
        if component.role not in allowed:
            raise ValueError(
                f"Role {component.role!r} is not allowed for factor {component.factor!r}"
            )
    return PredicateDecomposition(
        predicate=decision.predicate,
        components=decision.components,
        source="synthetic_adjudication",
        confidence=decision.confidence,
        evidence={
            "adjudication_status": decision.status,
            "confidence_missing": decision.confidence is None,
            "selected_sources": decision.selected_sources,
            "rationale": decision.rationale,
            **(evidence or {}),
        },
    )
