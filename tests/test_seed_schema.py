from pathlib import Path

import pytest

from lemon_factor.factors.decomposition import (
    FactorComponent,
    PredicateDecomposition,
    PredicateDecompositionSet,
    read_factor_schema,
    write_factor_schema,
)
from lemon_factor.factors.seed_schema import build_default_factor_schema


def test_default_factor_schema_contains_required_factors():
    factors = build_default_factor_schema()
    ids = {factor.id for factor in factors}
    assert "biographical_relation" in ids
    assert "location_relation" in ids
    assert "part_whole_relation" in ids
    assert "person" in ids
    assert "place" in ids


def test_default_factor_schema_ids_are_unique():
    factors = build_default_factor_schema()
    ids = [factor.id for factor in factors]
    assert len(ids) == len(set(ids))


def test_default_factor_schema_roundtrip(tmp_path: Path):
    path = tmp_path / "factor_schema_seed.json"
    factors = build_default_factor_schema()
    write_factor_schema(path, factors)
    loaded = read_factor_schema(path)
    assert [factor.id for factor in loaded] == [factor.id for factor in factors]


def test_decomposition_set_rejects_unknown_factor():
    factors = build_default_factor_schema()
    decomposition = PredicateDecomposition(
        predicate="badPredicate",
        components=[
            FactorComponent(factor="missing", role="predicate_meaning", weight=1.0),
        ],
    )
    with pytest.raises(ValueError, match="unknown factor"):
        PredicateDecompositionSet(factors=factors, decompositions={"badPredicate": decomposition})


def test_decomposition_set_rejects_disallowed_role():
    factors = build_default_factor_schema()
    decomposition = PredicateDecomposition(
        predicate="badPredicate",
        components=[
            FactorComponent(factor="biographical_relation", role="subject_domain", weight=1.0),
        ],
    )
    with pytest.raises(ValueError, match="not allowed"):
        PredicateDecompositionSet(factors=factors, decompositions={"badPredicate": decomposition})


def test_predicate_decomposition_requires_weights_sum_to_one():
    with pytest.raises(ValueError, match="weights must sum"):
        PredicateDecomposition(
            predicate="badPredicate",
            components=[
                FactorComponent(factor="entity_relation", role="predicate_meaning", weight=0.5),
                FactorComponent(factor="entity", role="subject_domain", weight=0.25),
            ],
        )
