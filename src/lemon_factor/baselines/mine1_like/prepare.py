"""Prepare MINE-1-compatible fact-recovery items from LEMON perturbations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .core import apply_controlled_perturbation, edge_to_labeled, fact_for_edge, node_label_map, norm_text, read_jsonl, target_edge_index, write_jsonl


def make_item(record: dict[str, Any]) -> dict[str, Any] | None:
    edge_index = target_edge_index(record)
    if edge_index is None:
        return None
    raw_edges = record.get("edges", []) or []
    if edge_index >= len(raw_edges):
        return None
    labels = node_label_map(record)
    ref_edge = edge_to_labeled(raw_edges[edge_index], labels)
    fact = fact_for_edge(record, edge_index)
    fact_text = norm_text(fact.get("text")) if fact else ref_edge.as_text()
    candidate_edges = apply_controlled_perturbation(record)
    return {
        "id": f"{record.get('id')}::mine1::{edge_index}",
        "source_record_id": record.get("id"),
        "original_id": record.get("original_id"),
        "dataset": record.get("dataset"),
        "variant": record.get("variant"),
        "fact_id": fact.get("id") if fact else f"edge_{edge_index}",
        "fact": fact_text,
        "reference_edge": ref_edge.__dict__,
        "candidate_graph": {
            "nodes": sorted({node for edge in candidate_edges for node in (edge.subject, edge.object)}),
            "edges": [edge.__dict__ for edge in candidate_edges],
        },
        "metadata": {
            "edge_index": edge_index,
            "expected_damage": record.get("expected_damage", {}),
            "target_factor_groups": record.get("target_factor_groups", []),
            "mine_variant": "local_lexical_retrieval_two_hop",
        },
    }


def prepare(inputs: list[str], out: str, limit: int | None = None, per_dataset: int | None = None) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    by_dataset: dict[str, int] = {}
    for path in inputs:
        for record in read_jsonl(path):
            item = make_item(record)
            if item is None:
                continue
            dataset = str(item.get("dataset"))
            if per_dataset is not None and by_dataset.get(dataset, 0) >= per_dataset:
                continue
            items.append(item)
            by_dataset[dataset] = by_dataset.get(dataset, 0) + 1
            if limit is not None and len(items) >= limit:
                break
        if limit is not None and len(items) >= limit:
            break
    write_jsonl(out, items)
    return {"status": "passed", "out": out, "items": len(items), "by_dataset": by_dataset}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--per-dataset", type=int, default=None)
    args = parser.parse_args()
    report = prepare(args.inputs, args.out, limit=args.limit, per_dataset=args.per_dataset)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
