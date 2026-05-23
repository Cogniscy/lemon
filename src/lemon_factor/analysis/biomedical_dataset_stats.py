"""Biomedical GraphText dataset statistics and paper-table export."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

from lemon_factor.datasets.unified_io import read_jsonl
from lemon_factor.schema.graphtext import GraphTextExample


def summarize_biomedical_examples(examples: list[GraphTextExample]) -> dict[str, Any]:
    if not examples:
        return {
            "examples": 0,
            "nodes_total": 0,
            "edges_total": 0,
            "nodes_avg": 0.0,
            "edges_avg": 0.0,
            "text_chars_avg": 0.0,
            "entity_type_counts": {},
            "predicate_counts": {},
            "normalization_id_coverage": 0.0,
            "document_level_ratio": 0.0,
        }
    entity_types = Counter(node.type or "Unknown" for ex in examples for node in ex.nodes)
    predicates = Counter(edge.pred for ex in examples for edge in ex.edges)
    nodes_total = sum(len(ex.nodes) for ex in examples)
    nodes_with_external_ids = sum(
        1 for ex in examples for node in ex.nodes if node.external_ids
    )
    edges_total = sum(len(ex.edges) for ex in examples)
    document_level_edges = sum(
        1
        for ex in examples
        for edge in ex.edges
        if edge.metadata.get("document_level") is True or ex.metadata.get("document_level") is True
    )
    return {
        "examples": len(examples),
        "nodes_total": nodes_total,
        "edges_total": edges_total,
        "facts_total": sum(len(ex.facts) for ex in examples),
        "nodes_avg": mean(len(ex.nodes) for ex in examples),
        "edges_avg": mean(len(ex.edges) for ex in examples),
        "text_chars_avg": mean(len(ex.text) for ex in examples),
        "entity_type_counts": dict(entity_types.most_common()),
        "predicate_counts": dict(predicates.most_common()),
        "predicate_count": len(predicates),
        "normalization_id_coverage": nodes_with_external_ids / nodes_total if nodes_total else 0.0,
        "document_level_ratio": document_level_edges / edges_total if edges_total else 0.0,
    }


def summarize_path(path: str | Path) -> dict[str, Any]:
    examples = read_jsonl(path)
    stats = summarize_biomedical_examples(examples)
    stats["path"] = str(path)
    stats["dataset"] = examples[0].dataset if examples else "unknown"
    stats["split"] = examples[0].split.value if examples else "unknown"
    return stats


def write_markdown_table(stats_by_path: dict[str, dict[str, Any]], path: str | Path) -> None:
    lines = [
        "| Dataset | Split | Examples | Text chars avg | Entity types | Predicate types | Top predicates | Nodes | Edges | Avg edges | Norm. ID coverage | Document-level ratio |",
        "|---|---|---:|---:|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for stats in stats_by_path.values():
        entity_types = ", ".join(f"{k}:{v}" for k, v in list(stats.get("entity_type_counts", {}).items())[:4])
        predicates = ", ".join(f"{k}:{v}" for k, v in list(stats.get("predicate_counts", {}).items())[:4])
        lines.append(
            "| {dataset} | {split} | {examples} | {text_chars_avg:.1f} | {entity_types} | {predicate_count} | {predicates} | {nodes_total} | {edges_total} | {edges_avg:.2f} | {norm:.3f} | {doc_ratio:.3f} |".format(
                dataset=stats.get("dataset", "unknown"),
                split=stats.get("split", "unknown"),
                examples=stats.get("examples", 0),
                text_chars_avg=float(stats.get("text_chars_avg", 0.0)),
                entity_types=entity_types or "—",
                predicate_count=stats.get("predicate_count", 0),
                predicates=predicates or "—",
                nodes_total=stats.get("nodes_total", 0),
                edges_total=stats.get("edges_total", 0),
                edges_avg=float(stats.get("edges_avg", 0.0)),
                norm=float(stats.get("normalization_id_coverage", 0.0)),
                doc_ratio=float(stats.get("document_level_ratio", 0.0)),
            )
        )
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Biomedical GraphText JSONL files")
    parser.add_argument("--out", default="data/biomedical/reports/biomedical_dataset_stats.json")
    parser.add_argument("--table", default="paper/tables/table_biomedical_dataset_stats.md")
    args = parser.parse_args()

    payload = {str(path): summarize_path(path) for path in args.paths}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_table(payload, args.table)
    print(json.dumps({"out": str(out), "table": args.table}, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
