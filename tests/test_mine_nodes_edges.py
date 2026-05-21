from lemon_factor.mine_nodes_edges.retrieval import expand_reconstructed_subgraph, retrieve_top_k_nodes
from lemon_factor.mine_nodes_edges.scoring import score_mine_style_corpus, score_mine_style_fact
from lemon_factor.reverse.reconstruct_graph import reconstruct_example_graph
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


def test_retrieve_top_k_nodes_from_reconstructed_graph():
    example = make_example()
    record = reconstruct_example_graph(example, lexical_cues={"birthPlace": ["born in"]})
    retrieved = retrieve_top_k_nodes(example, record, "Alan Bean birthPlace Wheeler Texas", k=2)
    assert len(retrieved) == 2
    assert {node_id for node_id, _ in retrieved} == {"s", "o"}


def test_expand_reconstructed_subgraph_returns_edge():
    example = make_example()
    record = reconstruct_example_graph(example, lexical_cues={"birthPlace": ["born in"]})
    edges = expand_reconstructed_subgraph(record, ["s"], hops=1)
    assert len(edges) == 1
    assert edges[0].pred == "birthPlace"


def test_mine_style_fact_score_recovers_fact():
    example = make_example()
    record = reconstruct_example_graph(example, lexical_cues={"birthPlace": ["born in"]})
    score = score_mine_style_fact(example, example.edges[0], 0, record, top_k=2, hops=1)
    assert score.node_information == 1.0
    assert score.edge_information == 1.0
    assert score.fact_recoverable is True
    assert score.mine_style_score == 1.0


def test_mine_style_corpus_report():
    example = make_example()
    record = reconstruct_example_graph(example, lexical_cues={"birthPlace": ["born in"]})
    report, scores = score_mine_style_corpus([example], [record], top_k=2, hops=1)
    assert report.facts == 1
    assert report.node_information == 1.0
    assert report.edge_information == 1.0
    assert report.mine_style_score == 1.0
    assert scores[0].fact_recoverable is True
