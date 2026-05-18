"""Dataset statistics for unified GraphText files."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

from lemon_factor.datasets.unified_io import read_jsonl
from lemon_factor.schema.graphtext import GraphTextExample


def summarize_examples(examples: list[GraphTextExample]) -> dict[str, Any]:
    """Compute compact statistics for a list of GraphText examples."""

    if not examples:
        return {
            "examples": 0,
            "nodes_total": 0,
            "edges_total": 0,
            "facts_total": 0,
            "nodes_avg": 0.0,
            "edges_avg": 0.0,
            "facts_avg": 0.0,
            "text_chars_avg": 0.0,
            "unique_predicates": 0,
            "predicate_count": 0,
            "top_predicates": [],
            "category_count": 0,
            "categories": {},
            "category_ratios": {},
            "examples_by_edges_count": {},
        }

    predicate_counts = Counter(edge.pred for example in examples for edge in example.edges)
    category_counts = Counter(
        str(example.metadata.get("category"))
        for example in examples
        if example.metadata.get("category") is not None
    )
    edge_count_distribution = Counter(str(len(example.edges)) for example in examples)
    category_ratios = {
        category: count / len(examples) for category, count in sorted(category_counts.items())
    }
    return {
        "examples": len(examples),
        "nodes_total": sum(len(example.nodes) for example in examples),
        "edges_total": sum(len(example.edges) for example in examples),
        "facts_total": sum(len(example.facts) for example in examples),
        "nodes_avg": mean(len(example.nodes) for example in examples),
        "edges_avg": mean(len(example.edges) for example in examples),
        "facts_avg": mean(len(example.facts) for example in examples),
        "text_chars_avg": mean(len(example.text) for example in examples),
        "unique_predicates": len(predicate_counts),
        "predicate_count": len(predicate_counts),
        "top_predicates": predicate_counts.most_common(20),
        "category_count": len(category_counts),
        "categories": dict(category_counts),
        "category_ratios": category_ratios,
        "examples_by_edges_count": dict(sorted(edge_count_distribution.items(), key=lambda item: int(item[0]))),
    }


def summarize_jsonl(path: str | Path) -> dict[str, Any]:
    """Read a GraphText JSONL file and return statistics."""

    return summarize_examples(read_jsonl(path))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="GraphText JSONL files")
    parser.add_argument("--out", default="data/reports/dataset_stats.json", help="Output JSON path")
    args = parser.parse_args()

    payload = {str(path): summarize_jsonl(path) for path in args.paths}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
