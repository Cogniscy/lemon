from lemon_factor.factors.decomposition import (
    FactorComponent,
    PredicateDecomposition,
    PredicateDecompositionSet,
    SemanticFactor,
)
from lemon_factor.reverse.reconstruct_graph import reconstruct_example_graph
from lemon_factor.reverse.reverse_coverage import score_reverse_corpus, score_reverse_edge
from lemon_factor.schema.graphtext import Edge, GraphTextExample, Node, Split


def make_schema():
    factors = [
        SemanticFactor(id="person", label="Person", allowed_roles=["subject_domain"]),
        SemanticFactor(id="place", label="Place", allowed_roles=["object_domain"]),
        SemanticFactor(
            id="biographical_relation",
            label="Biographical relation",
            level="abstract_relation",
            allowed_roles=["predicate_meaning"],
        ),
    ]
    decomp = PredicateDecomposition(
        predicate="birthPlace",
        components=[
            FactorComponent(factor="biographical_relation", role="predicate_meaning", weight=0.5),
            FactorComponent(factor="person", role="subject_domain", weight=0.25),
            FactorComponent(factor="place", role="object_domain", weight=0.25),
        ],
    )
    return PredicateDecompositionSet(factors=factors, decompositions={"birthPlace": decomp})


def make_example():
    return GraphTextExample(
        id="ex1",
        dataset="toy",
        split=Split.dev,
        text="Alan Bean was born in Wheeler, Texas.",
        nodes=[Node(id="s", label="Alan Bean"), Node(id="o", label="Wheeler, Texas")],
        edges=[Edge(subj="s", pred="birthPlace", obj="o")],
    )


def test_reverse_edge_scores_weighted_components():
    example = make_example()
    record = reconstruct_example_graph(example, lexical_cues={"birthPlace": ["born in"]})
    result = score_reverse_edge(example, example.edges[0], 0, record, make_schema())
    assert result.score == 1.0
    assert result.edge_recovered is True
    assert {component.role for component in result.components} == {
        "predicate_meaning",
        "subject_domain",
        "object_domain",
    }


def test_reverse_corpus_reports_edge_recovery():
    example = make_example()
    record = reconstruct_example_graph(example, lexical_cues={"birthPlace": ["born in"]})
    report, examples, edges = score_reverse_corpus([example], [record], make_schema())
    assert report.reverse_lemon_coverage == 1.0
    assert report.edge_recovery_rate == 1.0
    assert examples[0].score == 1.0
    assert edges[0].score == 1.0
