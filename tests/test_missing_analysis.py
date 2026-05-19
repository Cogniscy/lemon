from lemon_factor.coverage.missing_analysis import build_missing_predicate_report
from lemon_factor.schema.graphtext import Edge, GraphTextExample, Node, Split


def _example():
    return GraphTextExample(
        id="ex1",
        dataset="webnlg",
        split=Split.dev,
        text="Alice wrote the book.",
        nodes=[Node(id="s", label="Alice"), Node(id="o", label="Book")],
        edges=[Edge(subj="s", pred="author", obj="o")],
        metadata={"category": "WrittenWork"},
    )


def test_missing_predicate_report_aggregates_missing_edges_with_context():
    rows = [
        {
            "example_id": "ex1",
            "edge_index": 0,
            "subject": "Alice",
            "predicate": "author",
            "object": "Book",
            "missing_decomposition": True,
        },
        {
            "example_id": "ex1",
            "edge_index": 1,
            "subject": "Alice",
            "predicate": "genre",
            "object": "Novel",
            "missing_decomposition": False,
        },
    ]
    report = build_missing_predicate_report(rows, examples=[_example()])
    assert report.total_missing_edges == 1
    assert report.predicate_count == 1
    assert report.predicates["author"].categories == {"WrittenWork": 1}
    assert report.predicates["author"].examples[0]["text"] == "Alice wrote the book."
