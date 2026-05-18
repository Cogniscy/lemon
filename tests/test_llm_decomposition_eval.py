from __future__ import annotations

from lemon_factor.factors.decomposition import (
    FactorComponent,
    PredicateDecomposition,
    PredicateDecompositionSet,
)
from lemon_factor.factors.seed_schema import build_default_factor_schema
from lemon_factor.llm.evaluate_decompositions import aggregate_scores, evaluate_records, score_decomposition
from lemon_factor.llm.schema import LLMDecompositionRecord, LLMPredicateDecomposition


def _reference() -> PredicateDecompositionSet:
    return PredicateDecompositionSet(
        factors=build_default_factor_schema(),
        decompositions={
            "birthPlace": PredicateDecomposition(
                predicate="birthPlace",
                components=[
                    FactorComponent(factor="biographical_relation", role="predicate_meaning", weight=0.5),
                    FactorComponent(factor="person", role="subject_domain", weight=0.2),
                    FactorComponent(factor="place", role="object_domain", weight=0.3),
                ],
            )
        },
    )


def _candidate(model: str = "m1") -> LLMDecompositionRecord:
    decomposition = LLMPredicateDecomposition(
        predicate="birthPlace",
        components=[
            {"factor": "biographical_relation", "role": "predicate_meaning", "weight": 0.5},
            {"factor": "person", "role": "subject_domain", "weight": 0.2},
            {"factor": "place", "role": "object_domain", "weight": 0.3},
        ],
        confidence=0.9,
        rationale="ok",
    )
    return LLMDecompositionRecord(model=model, predicate="birthPlace", decomposition=decomposition)


def test_score_decomposition_exact_match():
    score = score_decomposition(_candidate(), _reference())
    assert score["factor_precision"] == 1.0
    assert score["factor_recall"] == 1.0
    assert score["factor_f1"] == 1.0
    assert score["role_accuracy"] == 1.0
    assert score["weight_mae"] == 0.0


def test_evaluate_records_aggregates_by_model():
    result = evaluate_records([_candidate("m1"), _candidate("m2")], _reference())
    assert result["records_total"] == 2
    assert result["records_scored"] == 2
    assert set(result["models"]) == {"m1", "m2"}
    assert result["models"]["m1"]["factor_f1"] == 1.0


def test_aggregate_scores_empty():
    result = aggregate_scores([])
    assert result["models"] == {}
    assert result["items"] == []
