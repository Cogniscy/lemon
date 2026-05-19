from lemon_factor.factors.decomposition import FactorComponent, PredicateDecomposition
from lemon_factor.factors.disagreement import classify_disagreement, max_weight_delta
from lemon_factor.llm.schema import LLMDecompositionRecord, LLMPredicateDecomposition, LLMFactorComponent


def seed(*components):
    return PredicateDecomposition(
        predicate="p",
        components=[FactorComponent(factor=f, role=r, weight=w) for f, r, w in components],
    )


def llm(*components):
    return LLMDecompositionRecord(
        model="m",
        predicate="p",
        decomposition=LLMPredicateDecomposition(
            predicate="p",
            components=[LLMFactorComponent(factor=f, role=r, weight=w) for f, r, w in components],
        ),
    )


def test_disagreement_all_agree():
    s = seed(("person", "subject_domain", 0.5), ("place", "object_domain", 0.5))
    c = llm(("person", "subject_domain", 0.5), ("place", "object_domain", 0.5))
    assert classify_disagreement(s, [c]) == "all_agree"


def test_disagreement_factor_disagreement():
    s = seed(("person", "subject_domain", 0.5), ("place", "object_domain", 0.5))
    c = llm(("person", "subject_domain", 0.5), ("organization", "object_domain", 0.5))
    assert classify_disagreement(s, [c]) == "factor_disagreement"


def test_disagreement_role_disagreement():
    s = seed(("person", "subject_domain", 0.5), ("place", "object_domain", 0.5))
    c = llm(("person", "object_domain", 0.5), ("place", "subject_domain", 0.5))
    assert classify_disagreement(s, [c]) == "role_disagreement"


def test_disagreement_weight_disagreement():
    s = seed(("person", "subject_domain", 0.5), ("place", "object_domain", 0.5))
    c = llm(("person", "subject_domain", 0.8), ("place", "object_domain", 0.2))
    assert round(max_weight_delta(s, [c]), 6) == 0.3
    assert classify_disagreement(s, [c], weight_threshold=0.2) == "weight_disagreement"


def test_disagreement_seed_suspect_when_llms_agree_against_seed():
    s = seed(("person", "subject_domain", 0.5), ("place", "object_domain", 0.5))
    c1 = llm(("organization", "subject_domain", 0.5), ("place", "object_domain", 0.5))
    c2 = llm(("organization", "subject_domain", 0.5), ("place", "object_domain", 0.5))
    assert classify_disagreement(s, [c1, c2]) == "seed_suspect"
