from lemon_factor.coverage.graphtext_coverage import score_corpus_coverage, score_example_coverage
from lemon_factor.factors.decomposition import (
    FactorComponent,
    PredicateDecomposition,
    PredicateDecompositionSet,
    SemanticFactor,
)
from lemon_factor.schema.graphtext import Edge, GraphTextExample, Node, Split


def factor(fid, roles):
    return SemanticFactor(id=fid, label=fid.replace("_", " "), allowed_roles=roles)


def decomposition_set():
    factors = [
        factor("biographical_relation", ["predicate_meaning"]),
        factor("person", ["subject_domain"]),
        factor("place", ["object_domain"]),
    ]
    decomposition = PredicateDecomposition(
        predicate="birthPlace",
        components=[
            FactorComponent(factor="biographical_relation", role="predicate_meaning", weight=0.45),
            FactorComponent(factor="person", role="subject_domain", weight=0.2),
            FactorComponent(factor="place", role="object_domain", weight=0.35),
        ],
    )
    return PredicateDecompositionSet(factors=factors, decompositions={"birthPlace": decomposition})


def example(pred="birthPlace"):
    return GraphTextExample(
        id="ex1",
        dataset="webnlg",
        split=Split.dev,
        text="Alan Bean was born in Wheeler, Texas.",
        nodes=[Node(id="n1", label="Alan Bean"), Node(id="n2", label="Wheeler Texas")],
        edges=[Edge(subj="n1", pred=pred, obj="n2")],
        metadata={"category": "Astronaut"},
    )


def test_score_example_coverage_scores_one_edge():
    result = score_example_coverage(example(), decomposition_set(), {"birthPlace": ["born in"]})
    assert result.edge_count == 1
    assert result.missing_decomposition_count == 0
    assert result.score > 0.9
    assert result.edges[0].components


def test_score_example_coverage_counts_missing_decomposition():
    result = score_example_coverage(example("unknownPredicate"), decomposition_set(), {})
    assert result.missing_decomposition_count == 1
    assert result.score == 0.0
    assert result.edges[0].missing_decomposition


def test_score_corpus_coverage_aggregates_missing_rate():
    report, examples, edges = score_corpus_coverage(
        [example(), example("unknownPredicate")],
        decomposition_set(),
        {"birthPlace": ["born in"]},
    )
    assert report.examples == 2
    assert report.edges == 2
    assert report.missing_decomposition_rate == 0.5
    assert len(examples) == 2
    assert len(edges) == 2
