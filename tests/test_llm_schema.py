from __future__ import annotations

import pytest

from lemon_factor.factors.seed_schema import build_default_factor_schema
from lemon_factor.llm.schema import LLMPredicateDecomposition, validate_against_factor_schema


def test_llm_decomposition_validates_against_seed_schema():
    candidate = LLMPredicateDecomposition(
        predicate="birthPlace",
        components=[
            {"factor": "biographical_relation", "role": "predicate_meaning", "weight": 0.5},
            {"factor": "person", "role": "subject_domain", "weight": 0.2},
            {"factor": "place", "role": "object_domain", "weight": 0.3},
        ],
        confidence=0.8,
        rationale="birthPlace links a person to a place of birth",
    )
    decomposition = validate_against_factor_schema(candidate, build_default_factor_schema())
    assert decomposition.source == "llm_candidate"
    assert decomposition.predicate == "birthPlace"


def test_llm_decomposition_rejects_unknown_factor():
    candidate = LLMPredicateDecomposition(
        predicate="birthPlace",
        components=[
            {"factor": "made_up_factor", "role": "predicate_meaning", "weight": 1.0},
        ],
        confidence=0.1,
        rationale="bad",
    )
    with pytest.raises(ValueError, match="Unknown factor"):
        validate_against_factor_schema(candidate, build_default_factor_schema())


def test_llm_decomposition_rejects_bad_weight_sum():
    with pytest.raises(ValueError, match="weights must sum"):
        LLMPredicateDecomposition(
            predicate="x",
            components=[
                {"factor": "entity_relation", "role": "predicate_meaning", "weight": 0.6},
            ],
            confidence=0.1,
            rationale="bad",
        )
