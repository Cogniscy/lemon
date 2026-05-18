"""Pydantic models for factorized semantic decompositions."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

FactorKind = Literal[
    "entity_type",
    "event_type",
    "property",
    "domain",
    "role",
    "quantity",
    "unit",
    "evidence",
    "relation",
]

FactorRole = Literal[
    "type",
    "part",
    "function",
    "cause",
    "effect",
    "measure",
    "domain",
    "agent",
    "object",
    "subject_domain",
    "object_domain",
    "predicate_meaning",
    "source_entity",
    "target_entity",
    "background",
]


class SemanticFactor(BaseModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    kind: FactorKind
    level: Literal["universal", "scientific", "biomedical", "dataset"] = "universal"
    is_atomic: bool = False
    description: str | None = None


class FactorComponent(BaseModel):
    factor: str = Field(min_length=1)
    role: FactorRole = "type"
    weight: float = Field(ge=0.0, le=1.0)
    depth: int = Field(default=0, ge=0)
    evidence: str | None = None


class FactorDecomposition(BaseModel):
    term: str = Field(min_length=1)
    components: list[FactorComponent] = Field(min_length=1)
    source: Literal["seed", "train", "expert", "auto"] = "seed"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_weight_mass(self) -> "FactorDecomposition":
        total = sum(c.weight for c in self.components)
        if total <= 0:
            raise ValueError("Factor decomposition must have positive total weight")
        return self

    def normalized_weights(self) -> dict[tuple[str, str], float]:
        total = sum(c.weight for c in self.components)
        return {(c.factor, c.role): c.weight / total for c in self.components}
