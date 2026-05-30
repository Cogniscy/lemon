"""Exact triple-retention baseline for controlled perturbation records."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .mine1_like.core import apply_controlled_perturbation, edge_to_labeled, harmonic_mean, node_label_map, read_jsonl, target_edge_index, tokenize


def norm_triple(edge: Any) -> tuple[str, str, str]:
    return (
        " ".join(sorted(tokenize(edge.subject))),
        " ".join(sorted(tokenize(edge.predicate))),
        " ".join(sorted(tokenize(edge.object))),
    )


def score_record(record: dict[str, Any]) -> dict[str, Any] | None:
    edge_index = target_edge_index(record)
    if edge_index is None:
        return None
    raw_edges = record.get("edges", []) or []
    if edge_index >= len(raw_edges):
        return None
    labels = node_label_map(record)
    reference = edge_to_labeled(raw_edges[edge_index], labels)
    candidates = apply_controlled_perturbation(record)
    ref = norm_triple(reference)
    cand = {norm_triple(edge) for edge in candidates}
    tp = 1 if ref in cand else 0
    precision = tp / max(1, len(cand))
    recall = float(tp)
    return {
        "id": record.get("id"),
        "dataset": record.get("dataset"),
        "variant": record.get("variant"),
        "precision": precision,
        "recall": recall,
        "f1": harmonic_mean(precision, recall),
        "exact_recovered": bool(tp),
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(str(row.get("dataset")), str(row.get("variant")))].append(row)
    by_group = []
    for (dataset, variant), members in sorted(groups.items()):
        by_group.append(
            {
                "dataset": dataset,
                "variant": variant,
                "items": len(members),
                "triple_f1": round(sum(row["f1"] for row in members) / len(members), 4),
                "exact_recovery": round(sum(1 for row in members if row["exact_recovered"]) / len(members), 4),
            }
        )
    return {
        "status": "passed",
        "items": len(rows),
        "triple_f1": round(sum(row["f1"] for row in rows) / max(1, len(rows)), 4),
        "exact_recovery": round(sum(1 for row in rows if row["exact_recovered"]) / max(1, len(rows)), 4),
        "by_dataset_variant": by_group,
    }


def run(inputs: list[str], out: str, scores_out: str | None = None, limit: int | None = None, per_dataset: int | None = None) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    by_dataset: dict[str, int] = defaultdict(int)
    for path in inputs:
        for record in read_jsonl(path):
            dataset = str(record.get("dataset", ""))
            if per_dataset is not None and by_dataset[dataset] >= per_dataset:
                continue
            row = score_record(record)
            if row is not None:
                rows.append(row)
                by_dataset[str(row.get("dataset", ""))] += 1
            if limit is not None and len(rows) >= limit:
                break
        if limit is not None and len(rows) >= limit:
            break
    report = summarize(rows)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")
    if scores_out:
        Path(scores_out).parent.mkdir(parents=True, exist_ok=True)
        with Path(scores_out).open("w", encoding="utf8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--scores-out", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--per-dataset", type=int, default=None)
    args = parser.parse_args()
    report = run(args.inputs, args.out, scores_out=args.scores_out, limit=args.limit, per_dataset=args.per_dataset)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
