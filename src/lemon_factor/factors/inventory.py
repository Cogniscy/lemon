"""Build a train-side factor inventory from unified GraphText examples."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from lemon_factor.datasets.unified_io import read_jsonl
from lemon_factor.factors.candidates import candidate_factors_from_predicate
from lemon_factor.schema.graphtext import Edge, GraphTextExample


class PredicateInventoryItem(BaseModel):
    """Aggregated evidence for one graph predicate."""

    predicate: str
    count: int = 0
    categories: dict[str, int] = Field(default_factory=dict)
    candidate_factors: list[str] = Field(default_factory=list)
    examples: list[dict[str, Any]] = Field(default_factory=list)


class NodeLabelInventoryItem(BaseModel):
    """Aggregated evidence for one node label."""

    label: str
    count: int = 0
    categories: dict[str, int] = Field(default_factory=dict)
    examples: list[dict[str, Any]] = Field(default_factory=list)


class FactorInventory(BaseModel):
    """Inventory extracted from an explicit graph/text training split."""

    dataset: str = "webnlg"
    split: str = "train"
    examples: int = 0
    predicates: dict[str, PredicateInventoryItem] = Field(default_factory=dict)
    node_labels: dict[str, NodeLabelInventoryItem] = Field(default_factory=dict)
    categories: dict[str, int] = Field(default_factory=dict)
    category_predicates: dict[str, dict[str, int]] = Field(default_factory=dict)
    candidate_factor_counts: dict[str, int] = Field(default_factory=dict)

    def to_json_file(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def from_json_file(cls, path: str | Path) -> "FactorInventory":
        return cls.model_validate_json(Path(path).read_text(encoding="utf-8"))


def _category(example: GraphTextExample) -> str:
    return str(example.metadata.get("category") or "unknown")


def _node_label_by_id(example: GraphTextExample) -> dict[str, str]:
    return {node.id: node.label for node in example.nodes}


def _edge_example(
    example: GraphTextExample,
    edge: Edge,
    node_labels: dict[str, str],
) -> dict[str, Any]:
    return {
        "example_id": example.id,
        "category": _category(example),
        "subj": node_labels.get(edge.subj, edge.subj),
        "pred": edge.pred,
        "obj": node_labels.get(edge.obj, edge.obj),
        "text": example.text,
    }


def build_inventory(
    examples: list[GraphTextExample],
    *,
    max_contexts_per_item: int = 5,
    dataset: str | None = None,
    split: str | None = None,
) -> FactorInventory:
    """Build a factor inventory from GraphText examples."""

    predicate_counts: Counter[str] = Counter()
    predicate_categories: dict[str, Counter[str]] = defaultdict(Counter)
    predicate_examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    node_counts: Counter[str] = Counter()
    node_categories: dict[str, Counter[str]] = defaultdict(Counter)
    node_examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    category_counts: Counter[str] = Counter()
    category_predicates: dict[str, Counter[str]] = defaultdict(Counter)
    candidate_factor_counts: Counter[str] = Counter()

    for example in examples:
        category = _category(example)
        category_counts[category] += 1
        node_labels = _node_label_by_id(example)

        for node in example.nodes:
            node_counts[node.label] += 1
            node_categories[node.label][category] += 1
            if len(node_examples[node.label]) < max_contexts_per_item:
                node_examples[node.label].append(
                    {"example_id": example.id, "category": category, "text": example.text}
                )

        for edge in example.edges:
            predicate_counts[edge.pred] += 1
            predicate_categories[edge.pred][category] += 1
            category_predicates[category][edge.pred] += 1
            candidates = candidate_factors_from_predicate(edge.pred)
            candidate_factor_counts.update(candidates)
            if len(predicate_examples[edge.pred]) < max_contexts_per_item:
                predicate_examples[edge.pred].append(_edge_example(example, edge, node_labels))

    predicates = {
        predicate: PredicateInventoryItem(
            predicate=predicate,
            count=count,
            categories=dict(predicate_categories[predicate]),
            candidate_factors=candidate_factors_from_predicate(predicate),
            examples=predicate_examples[predicate],
        )
        for predicate, count in sorted(predicate_counts.items())
    }
    node_labels_payload = {
        label: NodeLabelInventoryItem(
            label=label,
            count=count,
            categories=dict(node_categories[label]),
            examples=node_examples[label],
        )
        for label, count in sorted(node_counts.items())
    }

    return FactorInventory(
        dataset=dataset or (examples[0].dataset if examples else "unknown"),
        split=split or (str(examples[0].split.value) if examples else "unknown"),
        examples=len(examples),
        predicates=predicates,
        node_labels=node_labels_payload,
        categories=dict(category_counts),
        category_predicates={category: dict(counts) for category, counts in category_predicates.items()},
        candidate_factor_counts=dict(sorted(candidate_factor_counts.items())),
    )


def build_inventory_from_jsonl(
    path: str | Path,
    *,
    max_contexts_per_item: int = 5,
) -> FactorInventory:
    """Read a GraphText JSONL file and build a factor inventory."""

    return build_inventory(read_jsonl(path), max_contexts_per_item=max_contexts_per_item)


def summarize_inventory(inventory: FactorInventory, *, top_k: int = 20) -> dict[str, Any]:
    """Return compact summary suitable for reports and paper tables."""

    top_predicates = sorted(
        inventory.predicates.values(), key=lambda item: (-item.count, item.predicate)
    )[:top_k]
    top_candidate_factors = sorted(
        inventory.candidate_factor_counts.items(), key=lambda item: (-item[1], item[0])
    )[:top_k]
    return {
        "dataset": inventory.dataset,
        "split": inventory.split,
        "examples": inventory.examples,
        "predicate_count": len(inventory.predicates),
        "node_label_count": len(inventory.node_labels),
        "category_count": len(inventory.categories),
        "candidate_factor_count": len(inventory.candidate_factor_counts),
        "top_predicates": [
            {
                "predicate": item.predicate,
                "count": item.count,
                "categories": item.categories,
                "candidate_factors": item.candidate_factors,
            }
            for item in top_predicates
        ],
        "top_candidate_factors": top_candidate_factors,
        "categories": inventory.categories,
    }
