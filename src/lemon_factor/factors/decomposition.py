"""Role-aware semantic factor schema and predicate decompositions.

This module is intentionally deterministic. LLM-generated decompositions may be
added later as candidate evidence, but the seed schema/decomposition layer must
remain reproducible and testable without network access.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

FactorRole = Literal[
    "subject_domain",
    "object_domain",
    "predicate_meaning",
    "modifier",
    "value_domain",
    "background",
]

FactorLevel = Literal[
    "universal",
    "domain",
    "scientific",
    "abstract_relation",
    "dataset",
]

DecompositionSource = Literal[
    "seed_rule",
    "fallback",
    "expert",
    "llm_candidate",
    "synthetic_adjudication",
    "expansion_rule",
    "fallback_rule",
]

_ALLOWED_ROLE_VALUES = {
    "subject_domain",
    "object_domain",
    "predicate_meaning",
    "modifier",
    "value_domain",
    "background",
}


class SemanticFactor(BaseModel):
    """Controlled semantic direction used by LEMON-Factor."""

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    level: FactorLevel = "universal"
    description: str = ""
    allowed_roles: list[FactorRole] = Field(default_factory=list)
    parents: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_allowed_roles(self) -> "SemanticFactor":
        if not self.allowed_roles:
            raise ValueError("SemanticFactor.allowed_roles must not be empty")
        return self


class FactorComponent(BaseModel):
    """One weighted component of a predicate or term decomposition."""

    factor: str = Field(min_length=1)
    role: FactorRole
    weight: float = Field(gt=0.0, le=1.0)
    rationale: str | None = None


class PredicateDecomposition(BaseModel):
    """Weighted, role-aware decomposition of one graph predicate."""

    predicate: str = Field(min_length=1)
    components: list[FactorComponent] = Field(min_length=1)
    source: DecompositionSource = "seed_rule"
    confidence: float | None = Field(default=0.7, ge=0.0, le=1.0)
    evidence: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_weight_mass(self) -> "PredicateDecomposition":
        total = sum(component.weight for component in self.components)
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"PredicateDecomposition weights must sum to 1.0, got {total}")
        return self

    def component_map(self) -> dict[tuple[str, str], float]:
        return {(component.factor, component.role): component.weight for component in self.components}


class PredicateDecompositionSet(BaseModel):
    """A factor schema plus decompositions that are validated against it."""

    schema_version: str = "seed-v1"
    factors: list[SemanticFactor]
    decompositions: dict[str, PredicateDecomposition]
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_factor_references(self) -> "PredicateDecompositionSet":
        factor_by_id = {factor.id: factor for factor in self.factors}
        if len(factor_by_id) != len(self.factors):
            raise ValueError("Factor ids must be unique")
        for factor in self.factors:
            for parent in factor.parents:
                if parent not in factor_by_id:
                    raise ValueError(f"Factor {factor.id!r} references missing parent {parent!r}")
        for predicate, decomposition in self.decompositions.items():
            if predicate != decomposition.predicate:
                raise ValueError(f"Decomposition key {predicate!r} does not match predicate")
            for component in decomposition.components:
                if component.factor not in factor_by_id:
                    raise ValueError(
                        f"Predicate {predicate!r} references unknown factor {component.factor!r}"
                    )
                allowed = set(factor_by_id[component.factor].allowed_roles)
                if component.role not in allowed:
                    raise ValueError(
                        f"Role {component.role!r} is not allowed for factor {component.factor!r}"
                    )
        return self

    def to_json_file(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def from_json_file(cls, path: str | Path) -> "PredicateDecompositionSet":
        return cls.model_validate_json(Path(path).read_text(encoding="utf-8"))


def write_factor_schema(path: str | Path, factors: list[SemanticFactor]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([factor.model_dump(mode="json") for factor in factors], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def read_factor_schema(path: str | Path) -> list[SemanticFactor]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [SemanticFactor.model_validate(item) for item in raw]
