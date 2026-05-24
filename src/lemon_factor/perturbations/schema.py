"""Schema objects for controlled graph-text perturbations.

The perturbation layer is deliberately lightweight: it keeps the original graph
and changes only the text while recording which semantic factor groups should be
affected. Later scoring modules can read the JSONL as ordinary GraphText records
because the original graph fields are preserved.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

PerturbationVariant = Literal[
    "node_deletion",
    "edge_deletion",
    "argument_swap",
    "polarity_flip",
    "relation_blur",
]


class PerturbationOperation(BaseModel):
    """One deterministic text edit attempted by a perturbation operator."""

    edge_index: int | None = None
    operation: str = Field(min_length=1)
    target: str | None = None
    replacement: str | None = None
    changed: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExpectedDamage(BaseModel):
    """Expected semantic damage profile for a perturbed example."""

    direction: Literal["down", "stable"] = "down"
    severity: Literal["low", "medium", "high"] = "medium"
    rationale: str = Field(min_length=1)


class PerturbedGraphTextRecord(BaseModel):
    """Serializable JSONL record used by the LEM-04 perturbation builder."""

    id: str = Field(min_length=1)
    original_id: str = Field(min_length=1)
    dataset: str = Field(min_length=1)
    split: str = Field(min_length=1)
    variant: PerturbationVariant
    text: str
    original_text: str
    language: str | None = None
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)
    facts: list[dict[str, Any]] = Field(default_factory=list)
    expected_damage: ExpectedDamage
    target_factor_groups: list[str] = Field(min_length=1)
    operations: list[PerturbationOperation] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_text_is_not_empty(self) -> "PerturbedGraphTextRecord":
        if not self.text.strip():
            raise ValueError("Perturbed text must not be empty")
        return self
