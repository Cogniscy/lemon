from lemon_factor.coverage.factor_coverage import (
    exact_label_score,
    predicate_cue_score,
    score_predicate_decomposition,
)
from lemon_factor.factors.decomposition import FactorComponent, PredicateDecomposition
from lemon_factor.schema.graphtext import Edge


def birth_place_decomposition():
    return PredicateDecomposition(
        predicate="birthPlace",
        components=[
            FactorComponent(factor="biographical_relation", role="predicate_meaning", weight=0.45),
            FactorComponent(factor="person", role="subject_domain", weight=0.2),
            FactorComponent(factor="place", role="object_domain", weight=0.35),
        ],
    )


def test_predicate_cue_score_finds_born_in():
    cues = {"birthPlace": ["born in", "place of birth"]}
    assert predicate_cue_score("birthPlace", "Alan Bean was born in Texas.", cues) == 1.0


def test_exact_label_score_averages_subject_and_object_overlap():
    edge = Edge(subj="n1", pred="birthPlace", obj="n2")
    labels = {"n1": "Alan Bean", "n2": "Wheeler Texas"}
    assert exact_label_score(edge, labels, "Alan Bean was born in Wheeler.") == 0.75


def test_score_predicate_decomposition_weighted_components():
    edge = Edge(subj="n1", pred="birthPlace", obj="n2")
    labels = {"n1": "Alan Bean", "n2": "Wheeler Texas"}
    result = score_predicate_decomposition(
        birth_place_decomposition(),
        "Alan Bean was born in Wheeler, Texas.",
        edge,
        labels,
        {"birthPlace": ["born in"]},
    )
    assert result.score > 0.9
    assert [component.covered for component in result.components] == [True, True, True]


def test_score_predicate_decomposition_can_explain_missing_predicate_meaning():
    edge = Edge(subj="n1", pred="birthPlace", obj="n2")
    labels = {"n1": "Alan Bean", "n2": "Wheeler Texas"}
    result = score_predicate_decomposition(
        birth_place_decomposition(),
        "Alan Bean visited Wheeler, Texas.",
        edge,
        labels,
        {"birthPlace": ["born in"]},
    )
    missing = [component for component in result.components if not component.covered]
    assert any(component.factor == "biographical_relation" for component in missing)
    assert result.score < 1.0
