from lemon_factor.factors.inventory import PredicateInventoryItem
from lemon_factor.factors.seed_builder import build_seed_decomposition_set, decompose_predicate
from lemon_factor.factors.inventory import FactorInventory


def item(predicate: str, *, categories=None, candidates=None, count=10):
    return PredicateInventoryItem(
        predicate=predicate,
        count=count,
        categories=categories or {},
        candidate_factors=candidates or [],
        examples=[{"subj": "s", "pred": predicate, "obj": "o", "text": "text"}],
    )


def component_factors(decomposition):
    return {component.factor for component in decomposition.components}


def test_birthplace_decomposition_contains_biographical_person_place():
    d = decompose_predicate(
        item(
            "birthPlace",
            categories={"Astronaut": 8, "Artist": 4},
            candidates=["birth", "place"],
        )
    )
    assert component_factors(d) == {"biographical_relation", "person", "place"}
    assert d.confidence >= 0.8


def test_is_part_of_decomposition_contains_part_whole_relation():
    d = decompose_predicate(
        item("isPartOf", categories={"City": 12}, candidates=["is", "part", "of"])
    )
    assert "part_whole_relation" in component_factors(d)
    assert d.source == "seed_rule"


def test_orbital_period_decomposition_contains_astronomical_and_time():
    d = decompose_predicate(
        item(
            "orbitalPeriod",
            categories={"CelestialBody": 8},
            candidates=["orbital", "period"],
        )
    )
    assert "astronomical_relation" in component_factors(d)
    assert "time" in component_factors(d)


def test_unknown_predicate_gets_generic_fallback():
    d = decompose_predicate(item("unknownThing", categories={"Food": 1}, candidates=["unknown", "thing"]))
    assert "entity_relation" in component_factors(d)
    assert d.source == "fallback"
    assert d.confidence < 0.5


def test_decomposition_weights_sum_to_one():
    d = decompose_predicate(item("country", categories={"City": 3}, candidates=["country"]))
    assert sum(component.weight for component in d.components) == 1.0


def test_build_seed_decomposition_set_uses_top_k():
    inventory = FactorInventory(
        examples=2,
        predicates={
            "birthPlace": item("birthPlace", categories={"Astronaut": 5}, candidates=["birth", "place"], count=5),
            "country": item("country", categories={"City": 3}, candidates=["country"], count=3),
            "leader": item("leader", categories={"City": 2}, candidates=["leader"], count=2),
        },
    )
    decomposition_set = build_seed_decomposition_set(inventory, top_k=2)
    assert set(decomposition_set.decompositions) == {"birthPlace", "country"}
