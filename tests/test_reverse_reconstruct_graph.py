from lemon_factor.reverse.reconstruct_graph import reconstruct_example_graph, summarize_reconstructed_graphs
from lemon_factor.schema.graphtext import Edge, GraphTextExample, Node, Split


def make_example():
    return GraphTextExample(
        id="ex1",
        dataset="toy",
        split=Split.dev,
        text="Alan Bean was born in Wheeler, Texas.",
        nodes=[Node(id="s", label="Alan Bean"), Node(id="o", label="Wheeler, Texas")],
        edges=[Edge(subj="s", pred="birthPlace", obj="o")],
    )


def test_lexical_reconstruction_recovers_nodes_and_cue_edge():
    example = make_example()
    record = reconstruct_example_graph(example, lexical_cues={"birthPlace": ["born in"]})
    assert set(record.nodes) == {"s", "o"}
    assert len(record.edges) == 1
    assert record.edges[0].pred == "birthPlace"


def test_lexical_reconstruction_requires_predicate_cue():
    example = make_example()
    record = reconstruct_example_graph(example, lexical_cues={"birthPlace": ["place of birth"]})
    assert set(record.nodes) == {"s", "o"}
    assert record.edges == []


def test_oracle_edges_is_ceiling():
    example = make_example()
    record = reconstruct_example_graph(example, mode="oracle_edges")
    assert set(record.nodes) == {"s", "o"}
    assert len(record.edges) == 1
    summary = summarize_reconstructed_graphs([example], [record])
    assert summary["node_recovery_rate"] == 1.0
    assert summary["edge_recovery_rate"] == 1.0
