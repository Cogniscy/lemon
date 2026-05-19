"""Disagreement diagnostics for seed, LLM, and adjudicated decompositions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

from lemon_factor.factors.decomposition import PredicateDecomposition
from lemon_factor.llm.schema import LLMDecompositionRecord

DisagreementType = Literal[
    "all_agree",
    "factor_disagreement",
    "role_disagreement",
    "weight_disagreement",
    "seed_suspect",
    "schema_gap",
    "no_llm_candidates",
]


def factor_set(decomposition: PredicateDecomposition | LLMDecompositionRecord) -> set[str]:
    if isinstance(decomposition, LLMDecompositionRecord):
        return {component.factor for component in decomposition.decomposition.components}
    return {component.factor for component in decomposition.components}


def factor_role_set(decomposition: PredicateDecomposition | LLMDecompositionRecord) -> set[tuple[str, str]]:
    if isinstance(decomposition, LLMDecompositionRecord):
        return {(component.factor, component.role) for component in decomposition.decomposition.components}
    return {(component.factor, component.role) for component in decomposition.components}


def weights_by_factor(decomposition: PredicateDecomposition | LLMDecompositionRecord) -> dict[str, float]:
    if isinstance(decomposition, LLMDecompositionRecord):
        return {component.factor: component.weight for component in decomposition.decomposition.components}
    return {component.factor: component.weight for component in decomposition.components}


def _all_same(values: Iterable[object]) -> bool:
    values = list(values)
    return all(value == values[0] for value in values[1:]) if values else True


def max_weight_delta(
    seed: PredicateDecomposition,
    candidates: list[LLMDecompositionRecord],
) -> float:
    """Return max absolute factor-weight difference across seed and LLM candidates."""

    if not candidates:
        return 0.0
    seed_weights = weights_by_factor(seed)
    deltas: list[float] = []
    for candidate in candidates:
        candidate_weights = weights_by_factor(candidate)
        factors = set(seed_weights) | set(candidate_weights)
        deltas.extend(abs(seed_weights.get(f, 0.0) - candidate_weights.get(f, 0.0)) for f in factors)
    return max(deltas) if deltas else 0.0


def classify_disagreement(
    seed: PredicateDecomposition,
    candidates: list[LLMDecompositionRecord],
    *,
    weight_threshold: float = 0.2,
) -> DisagreementType:
    """Classify disagreement between one seed decomposition and LLM candidates.

    The labels are intentionally coarse because they are used for triage before
    human or strong-LLM adjudication.
    """

    if not candidates:
        return "no_llm_candidates"

    seed_factors = factor_set(seed)
    candidate_factor_sets = [factor_set(candidate) for candidate in candidates]
    if (
        len(candidate_factor_sets) >= 2
        and all(factors != seed_factors for factors in candidate_factor_sets)
        and _all_same(candidate_factor_sets)
    ):
        return "seed_suspect"
    if any(factors != seed_factors for factors in candidate_factor_sets):
        return "factor_disagreement"

    seed_roles = factor_role_set(seed)
    candidate_role_sets = [factor_role_set(candidate) for candidate in candidates]
    if any(roles != seed_roles for roles in candidate_role_sets):
        return "role_disagreement"

    if max_weight_delta(seed, candidates) > weight_threshold:
        return "weight_disagreement"
    return "all_agree"
