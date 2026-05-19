from lemon_factor.coverage.missing_analysis import MissingPredicateItem, MissingPredicateReport
from lemon_factor.factors.decomposition import PredicateDecompositionSet
from lemon_factor.factors.expand_decompositions import expand_decomposition_set
from lemon_factor.factors.seed_builder import build_seed_decomposition_set
from lemon_factor.factors.inventory import FactorInventory


def _base_set() -> PredicateDecompositionSet:
    inventory = FactorInventory(
        predicates={},
        examples=0,
    )
    return build_seed_decomposition_set(inventory, top_k=0)


def test_expand_decomposition_set_adds_missing_predicate():
    missing = MissingPredicateReport(
        total_missing_edges=2,
        predicate_count=1,
        predicates={
            "author": MissingPredicateItem(
                predicate="author",
                count=2,
                categories={"WrittenWork": 2},
                examples=[],
            )
        },
    )
    expanded = expand_decomposition_set(_base_set(), missing)
    assert "author" in expanded.decompositions
    assert expanded.decompositions["author"].source in {"expansion_rule", "fallback_rule"}
    assert expanded.metadata["added_predicate_count"] == 1


def test_expand_decomposition_set_does_not_overwrite_existing():
    missing = MissingPredicateReport(
        total_missing_edges=1,
        predicate_count=1,
        predicates={"birthPlace": MissingPredicateItem(predicate="birthPlace", count=1)},
    )
    inv = FactorInventory(
        predicates={
            "birthPlace": {
                "predicate": "birthPlace",
                "count": 1,
                "categories": {"Astronaut": 1},
                "candidate_factors": ["birth", "place"],
                "examples": [],
            }
        }
    )
    base = build_seed_decomposition_set(inv, top_k=1)
    expanded = expand_decomposition_set(base, missing)
    assert expanded.metadata["added_predicate_count"] == 0
    assert expanded.decompositions["birthPlace"].source == "seed_rule"
