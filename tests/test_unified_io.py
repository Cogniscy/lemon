from lemon_factor.datasets.unified_io import read_jsonl, write_jsonl
from lemon_factor.schema.graphtext import Edge, GraphTextExample, Node


def test_jsonl_round_trip(tmp_path):
    example = GraphTextExample(
        id="ex1",
        dataset="toy",
        split="dev",
        nodes=[Node(id="a", label="A"), Node(id="b", label="B")],
        edges=[Edge(subj="a", pred="rel", obj="b")],
    )
    path = tmp_path / "examples.jsonl"
    write_jsonl(path, [example])
    loaded = read_jsonl(path)
    assert len(loaded) == 1
    assert loaded[0].id == "ex1"
    assert loaded[0].edges[0].pred == "rel"
