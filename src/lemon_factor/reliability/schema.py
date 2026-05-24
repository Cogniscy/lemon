"""Schema objects for LLM reliability probes.

The reliability layer is deliberately separate from deterministic LEMON
scoring. It stores probe items, JSON-only judge outputs, and summary records so
that LLM-as-judge experiments can be run and audited without changing the main
metric implementation.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

FactorDecision = Literal["covered", "partial", "absent"]


class ProbeFactor(BaseModel):
    """One factor shown to an external judge."""

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    role: str = Field(min_length=1)
    group: str = Field(min_length=1)
    weight: float = Field(ge=0.0, le=1.0)
    description: str = ""


class ProbeEdge(BaseModel):
    """Source edge used in a probe item."""

    subject: str = Field(min_length=1)
    predicate: str = Field(min_length=1)
    object: str = Field(min_length=1)


class LLMProbeItem(BaseModel):
    """One controlled item prepared for LLM judging."""

    id: str = Field(min_length=1)
    dataset: str = Field(min_length=1)
    variant: str = Field(min_length=1)
    source_edge: ProbeEdge
    original_text: str = Field(min_length=1)
    perturbed_text: str = Field(min_length=1)
    factors: list[ProbeFactor] = Field(min_length=1)
    expected_damage: dict[str, Any] = Field(default_factory=dict)
    target_factor_groups: list[str] = Field(default_factory=list)
    deterministic_scores: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FactorJudgment(BaseModel):
    """One judge decision for a factor."""

    factor_id: str = Field(min_length=1)
    decision: FactorDecision
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence: str | None = None


class LLMProbeJudgment(BaseModel):
    """JSON output expected from one LLM judge for one probe item."""

    item_id: str = Field(min_length=1)
    judge_id: str = Field(min_length=1)
    decisions: list[FactorJudgment] = Field(min_length=1)
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_unique_factor_decisions(self) -> "LLMProbeJudgment":
        ids = [decision.factor_id for decision in self.decisions]
        if len(ids) != len(set(ids)):
            raise ValueError("Judgment has duplicate factor decisions")
        return self


class LLMReliabilitySummary(BaseModel):
    """Serializable summary of a reliability probe."""

    status: Literal["passed", "no_judgments", "partial"]
    item_count: int
    judgment_count: int
    judge_count: int
    summary: list[dict[str, Any]] = Field(default_factory=list)
    deterministic_agreement: list[dict[str, Any]] = Field(default_factory=list)
    examples: list[dict[str, Any]] = Field(default_factory=list)
