import pytest

from lemon_factor.factors.decomposition import FactorComponent
from lemon_factor.factors.seed_schema import build_default_factor_schema
from lemon_factor.llm.adjudication_schema import (
    LLMAdjudicationDecision,
    validate_adjudication_against_schema,
)


def test_adjudication_decision_validates_against_schema():
    decision = LLMAdjudicationDecision(
        predicate="birthPlace",
        status="modified",
        components=[
            FactorComponent(factor="biographical_relation", role="predicate_meaning", weight=0.4),
            FactorComponent(factor="person", role="subject_domain", weight=0.2),
            FactorComponent(factor="place", role="object_domain", weight=0.4),
        ],
        confidence=0.8,
        selected_sources=["seed", "llm:meta"],
        rationale="Preserves person-place biography relation.",
    )
    decomposition = validate_adjudication_against_schema(decision, build_default_factor_schema())
    assert decomposition.source == "synthetic_adjudication"
    assert decomposition.evidence["adjudication_status"] == "modified"


def test_adjudication_rejects_unknown_factor():
    decision = LLMAdjudicationDecision(
        predicate="x",
        status="modified",
        components=[FactorComponent(factor="not_in_schema", role="subject_domain", weight=1.0)],
    )
    with pytest.raises(ValueError, match="Unknown factor"):
        validate_adjudication_against_schema(decision, build_default_factor_schema())


def test_adjudication_missing_confidence_stays_none():
    decision = LLMAdjudicationDecision(
        predicate="birthPlace",
        status="modified",
        components=[
            FactorComponent(factor="biographical_relation", role="predicate_meaning", weight=0.4),
            FactorComponent(factor="person", role="subject_domain", weight=0.2),
            FactorComponent(factor="place", role="object_domain", weight=0.4),
        ],
        rationale="Valid decomposition without explicit confidence.",
    )
    decomposition = validate_adjudication_against_schema(decision, build_default_factor_schema())
    assert decomposition.confidence is None
    assert decomposition.evidence["confidence_missing"] is True


def test_adjudication_rejects_confidence_out_of_range():
    with pytest.raises(Exception):
        LLMAdjudicationDecision(
            predicate="birthPlace",
            status="modified",
            components=[
                FactorComponent(factor="biographical_relation", role="predicate_meaning", weight=0.4),
                FactorComponent(factor="person", role="subject_domain", weight=0.2),
                FactorComponent(factor="place", role="object_domain", weight=0.4),
            ],
            confidence=1.5,
        )
