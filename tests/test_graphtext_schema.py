import pytest
from pydantic import ValidationError

from lemon_factor.schema.graphtext import Edge, Fact, GraphTextExample, Node


def test_graphtext_validates_edge_refs():
    example = GraphTextExample(
        id="ex1",
        dataset="toy",
        split="train",
        text="Alan Bean was born in Wheeler.",
        nodes=[Node(id="n1", label="Alan Bean"), Node(id="n2", label="Wheeler")],
        edges=[Edge(subj="n1", pred="birthPlace", obj="n2")],
        facts=[Fact(id="f1", text="Alan Bean was born in Wheeler.", edge_refs=[0])],
    )
    assert example.node_labels() == {"n1": "Alan Bean", "n2": "Wheeler"}


def test_graphtext_rejects_missing_edge_node():
    with pytest.raises(ValidationError, match="not defined in nodes"):
        GraphTextExample(
            id="ex1",
            dataset="toy",
            split="train",
            nodes=[Node(id="n1", label="Alan Bean")],
            edges=[Edge(subj="n1", pred="birthPlace", obj="missing")],
        )


def test_graphtext_rejects_missing_fact_edge_ref():
    with pytest.raises(ValidationError, match="references missing edge index"):
        GraphTextExample(
            id="ex1",
            dataset="toy",
            split="train",
            nodes=[Node(id="n1", label="A"), Node(id="n2", label="B")],
            edges=[Edge(subj="n1", pred="rel", obj="n2")],
            facts=[Fact(id="f1", text="A relates to B", edge_refs=[2])],
        )
