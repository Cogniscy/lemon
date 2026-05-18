import pytest

from lemon_factor.mine.retrieve import cosine, expand_subgraph, top_k_nodes
from lemon_factor.schema.graphtext import Edge, GraphTextExample, Node


def test_cosine_basic_cases():
    assert cosine([1, 0], [1, 0]) == pytest.approx(1.0)
    assert cosine([1, 0], [0, 1]) == pytest.approx(0.0)
    assert cosine([0, 0], [1, 0]) == pytest.approx(0.0)


def test_top_k_nodes():
    result = top_k_nodes(
        [1, 0],
        {"a": [1, 0], "b": [0, 1], "c": [0.9, 0.1]},
        k=2,
    )
    assert [node for node, _ in result] == ["a", "c"]


def test_expand_subgraph_two_hops():
    example = GraphTextExample(
        id="g1",
        dataset="toy",
        split="dev",
        nodes=[Node(id="a", label="A"), Node(id="b", label="B"), Node(id="c", label="C"), Node(id="d", label="D")],
        edges=[
            Edge(subj="a", pred="r1", obj="b"),
            Edge(subj="b", pred="r2", obj="c"),
            Edge(subj="c", pred="r3", obj="d"),
        ],
    )
    edges = expand_subgraph(example, ["a"], hops=2)
    assert [edge.pred for edge in edges] == ["r1", "r2"]


def test_expand_subgraph_rejects_unknown_seed():
    example = GraphTextExample(
        id="g1",
        dataset="toy",
        split="dev",
        nodes=[Node(id="a", label="A")],
        edges=[],
    )
    with pytest.raises(ValueError, match="Unknown seed"):
        expand_subgraph(example, ["missing"], hops=2)
