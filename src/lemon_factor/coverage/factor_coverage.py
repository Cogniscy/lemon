"""Weighted factor coverage for one graph edge and text."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from lemon_factor.coverage.text_evidence import (
    any_cue_in_text,
    factor_to_cues,
    label_in_text,
    normalize_text,
    token_overlap_score,
)
from lemon_factor.factors.decomposition import FactorComponent, PredicateDecomposition
from lemon_factor.schema.graphtext import Edge


class ComponentCoverageResult(BaseModel):
    factor: str
    role: str
    weight: float
    covered: bool
    score: float = Field(ge=0.0, le=1.0)
    evidence_type: str = "none"
    evidence: str | None = None


class PredicateCoverageResult(BaseModel):
    predicate: str
    score: float = Field(ge=0.0, le=1.0)
    exact_label_score: float = Field(ge=0.0, le=1.0)
    predicate_cue_score: float = Field(ge=0.0, le=1.0)
    components: list[ComponentCoverageResult]
    missing_decomposition: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


def predicate_cues_for(predicate: str, lexical_cues: dict[str, list[str]] | None = None) -> list[str]:
    lexical_cues = lexical_cues or {}
    cues = list(lexical_cues.get(predicate, []))
    # Predicate identifiers themselves are weak but useful fallback cues.
    normalized_predicate = normalize_text(predicate)
    if normalized_predicate:
        cues.append(normalized_predicate)
    return cues


def predicate_cue_score(predicate: str, text: str, lexical_cues: dict[str, list[str]] | None = None) -> float:
    return 1.0 if any_cue_in_text(predicate_cues_for(predicate, lexical_cues), text) else 0.0


def exact_label_score(edge: Edge, node_labels: dict[str, str], text: str) -> float:
    subj_label = node_labels.get(edge.subj, edge.subj)
    obj_label = node_labels.get(edge.obj, edge.obj)
    return (token_overlap_score(subj_label, text) + token_overlap_score(obj_label, text)) / 2.0


def _score_domain_component(
    component: FactorComponent,
    edge: Edge,
    node_labels: dict[str, str],
    text: str,
) -> ComponentCoverageResult:
    label = node_labels.get(edge.subj if component.role == "subject_domain" else edge.obj, "")
    overlap = token_overlap_score(label, text)
    covered = label_in_text(label, text)
    return ComponentCoverageResult(
        factor=component.factor,
        role=component.role,
        weight=component.weight,
        covered=covered,
        score=overlap if covered else 0.0,
        evidence_type="node_label" if covered else "none",
        evidence=label if covered else None,
    )


def score_factor_component(
    component: FactorComponent,
    text: str,
    edge: Edge,
    node_labels: dict[str, str],
    lexical_cues: dict[str, list[str]] | None = None,
) -> ComponentCoverageResult:
    """Score whether one semantic factor component is supported by text."""

    lexical_cues = lexical_cues or {}
    if component.role in {"subject_domain", "object_domain"}:
        return _score_domain_component(component, edge, node_labels, text)

    predicate_cues = predicate_cues_for(edge.pred, lexical_cues)
    factor_cues = list(lexical_cues.get(component.factor, [])) + factor_to_cues(component.factor)
    if component.role == "predicate_meaning" and any_cue_in_text(predicate_cues, text):
        return ComponentCoverageResult(
            factor=component.factor,
            role=component.role,
            weight=component.weight,
            covered=True,
            score=1.0,
            evidence_type="predicate_cue",
            evidence=edge.pred,
        )
    if any_cue_in_text(factor_cues, text):
        return ComponentCoverageResult(
            factor=component.factor,
            role=component.role,
            weight=component.weight,
            covered=True,
            score=1.0,
            evidence_type="factor_cue",
            evidence=component.factor,
        )
    return ComponentCoverageResult(
        factor=component.factor,
        role=component.role,
        weight=component.weight,
        covered=False,
        score=0.0,
    )


def score_predicate_decomposition(
    decomposition: PredicateDecomposition,
    text: str,
    edge: Edge,
    node_labels: dict[str, str],
    lexical_cues: dict[str, list[str]] | None = None,
) -> PredicateCoverageResult:
    """Compute weighted coverage for one predicate decomposition."""

    components = [
        score_factor_component(component, text, edge, node_labels, lexical_cues)
        for component in decomposition.components
    ]
    total_weight = sum(component.weight for component in components) or 1.0
    score = sum(component.weight * component.score for component in components) / total_weight
    return PredicateCoverageResult(
        predicate=edge.pred,
        score=round(score, 6),
        exact_label_score=round(exact_label_score(edge, node_labels, text), 6),
        predicate_cue_score=predicate_cue_score(edge.pred, text, lexical_cues),
        components=components,
        missing_decomposition=False,
    )


def missing_decomposition_result(edge: Edge, text: str, node_labels: dict[str, str]) -> PredicateCoverageResult:
    return PredicateCoverageResult(
        predicate=edge.pred,
        score=0.0,
        exact_label_score=round(exact_label_score(edge, node_labels, text), 6),
        predicate_cue_score=0.0,
        components=[],
        missing_decomposition=True,
    )
