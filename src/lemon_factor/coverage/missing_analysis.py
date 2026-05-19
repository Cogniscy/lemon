"""Analyze predicates that are missing factor decompositions in coverage details."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from lemon_factor.datasets.unified_io import read_jsonl
from lemon_factor.schema.graphtext import GraphTextExample


class MissingPredicateItem(BaseModel):
    """Aggregated evidence for one predicate without a decomposition."""

    predicate: str
    count: int
    categories: dict[str, int] = Field(default_factory=dict)
    examples: list[dict[str, Any]] = Field(default_factory=list)


class MissingPredicateReport(BaseModel):
    """Report used to drive decomposition/cue expansion."""

    total_missing_edges: int
    predicate_count: int
    predicates: dict[str, MissingPredicateItem]
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_json_file(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def from_json_file(cls, path: str | Path) -> "MissingPredicateReport":
        return cls.model_validate_json(Path(path).read_text(encoding="utf-8"))


def read_details_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _example_index(examples: list[GraphTextExample]) -> dict[str, GraphTextExample]:
    return {example.id: example for example in examples}


def _edge_category(example: GraphTextExample | None) -> str:
    if example is None:
        return "unknown"
    return str(example.metadata.get("category") or "unknown")


def _edge_text(example: GraphTextExample | None) -> str | None:
    return example.text if example is not None else None


def build_missing_predicate_report(
    details_rows: list[dict[str, Any]],
    *,
    examples: list[GraphTextExample] | None = None,
    max_examples_per_predicate: int = 5,
) -> MissingPredicateReport:
    """Aggregate missing-decomposition edges by predicate."""

    examples_by_id = _example_index(examples or [])
    counts: Counter[str] = Counter()
    categories: dict[str, Counter[str]] = defaultdict(Counter)
    examples_by_predicate: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in details_rows:
        if not row.get("missing_decomposition"):
            continue
        predicate = str(row.get("predicate") or "")
        if not predicate:
            continue
        counts[predicate] += 1
        example = examples_by_id.get(str(row.get("example_id")))
        category = _edge_category(example)
        categories[predicate][category] += 1
        if len(examples_by_predicate[predicate]) < max_examples_per_predicate:
            payload = {
                "example_id": row.get("example_id"),
                "edge_index": row.get("edge_index"),
                "category": category,
                "subj": row.get("subject"),
                "pred": predicate,
                "obj": row.get("object"),
            }
            text = _edge_text(example)
            if text is not None:
                payload["text"] = text
            examples_by_predicate[predicate].append(payload)

    items = {
        predicate: MissingPredicateItem(
            predicate=predicate,
            count=count,
            categories=dict(categories[predicate]),
            examples=examples_by_predicate[predicate],
        )
        for predicate, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    }
    return MissingPredicateReport(
        total_missing_edges=sum(counts.values()),
        predicate_count=len(items),
        predicates=items,
        metadata={"max_examples_per_predicate": max_examples_per_predicate},
    )


def write_missing_predicates_table(report: MissingPredicateReport, path: str | Path, *, top_k: int = 20) -> None:
    lines = [
        "| Predicate | Missing edges | Categories | Example |",
        "|---|---:|---|---|",
    ]
    for item in list(report.predicates.values())[:top_k]:
        categories = ", ".join(f"{key}:{value}" for key, value in sorted(item.categories.items())) or "—"
        example = item.examples[0] if item.examples else {}
        edge = "—"
        if example:
            edge = f"{example.get('subj')} — {item.predicate} → {example.get('obj')}"
        lines.append(f"| `{item.predicate}` | {item.count} | {categories} | {edge} |")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("details", help="Edge-level coverage details JSONL")
    parser.add_argument("--examples", default=None, help="Optional GraphText JSONL for categories/text evidence")
    parser.add_argument("--out", required=True, help="Missing-predicate JSON report")
    parser.add_argument("--table", required=True, help="Markdown table with top missing predicates")
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--max-examples-per-predicate", type=int, default=5)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    examples = read_jsonl(args.examples) if args.examples else None
    report = build_missing_predicate_report(
        read_details_jsonl(args.details),
        examples=examples,
        max_examples_per_predicate=args.max_examples_per_predicate,
    )
    report.to_json_file(args.out)
    write_missing_predicates_table(report, args.table, top_k=args.top_k)
    print(json.dumps({"out": args.out, "table": args.table}, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
