from __future__ import annotations

from lemon_factor.analysis.dataset_stats import summarize_examples
from lemon_factor.datasets.convert_webnlg import convert_records


def test_stats_include_category_distribution_and_edge_counts() -> None:
    examples = convert_records(
        [
            {"gem_id": "a", "input": ["A | p | B"], "target": "A p B.", "category": "X"},
            {
                "gem_id": "b",
                "input": ["C | p | D", "C | q | E"],
                "target": "C p D and q E.",
                "category": "Y",
            },
            {"gem_id": "c", "input": ["F | q | G"], "target": "F q G.", "category": "Y"},
        ],
        split="train",
    )
    stats = summarize_examples(examples)
    assert stats["category_count"] == 2
    assert stats["categories"] == {"X": 1, "Y": 2}
    assert stats["category_ratios"] == {"X": 1 / 3, "Y": 2 / 3}
    assert stats["examples_by_edges_count"] == {"1": 2, "2": 1}
    assert stats["predicate_count"] == 2
