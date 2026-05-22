"""Deterministic reconstructed-graph perturbations for calibration."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from lemon_factor.reverse.reconstruct_graph import (
    ReconstructedEdge,
    ReconstructedGraphRecord,
    write_reconstructed_graphs,
)
from lemon_factor.schema.graphtext import GraphTextExample

GraphNoiseType = Literal["drop_edge", "drop_node", "graph_swap_predicate", "hallucinate_edge"]

GRAPH_NOISE_EXPECTED_DIRECTION: dict[str, Literal["down", "stable"]] = {
    "drop_edge": "down",
    "drop_node": "down",
    "graph_swap_predicate": "down",
    "hallucinate_edge": "down",
}


class GraphPerturbationOperation(BaseModel):
    example_id: str
    operation: str
    target: str | None = None
    replacement: str | None = None
    changed: bool = False
    metadata: dict[str, object] = Field(default_factory=dict)


class GraphPerturbationRecord(BaseModel):
    example_id: str
    noise_type: str
    noise_level: float = Field(ge=0.0, le=1.0)
    expected_direction: Literal["down", "stable"] = "down"
    original_node_count: int
    perturbed_node_count: int
    original_edge_count: int
    perturbed_edge_count: int
    operations: list[GraphPerturbationOperation] = Field(default_factory=list)


def _edge_id(edge: ReconstructedEdge) -> str:
    return f"{edge.subj}|{edge.pred}|{edge.obj}|{edge.gold_edge_index}"


def _predicate_pool(examples: list[GraphTextExample]) -> list[str]:
    predicates = sorted({edge.pred for example in examples for edge in example.edges})
    return predicates or ["relatedTo"]


def _operation(example_id: str, operation: str, target: str | None, replacement: str | None, changed: bool, **metadata: object) -> GraphPerturbationOperation:
    return GraphPerturbationOperation(
        example_id=example_id,
        operation=operation,
        target=target,
        replacement=replacement,
        changed=changed,
        metadata=metadata,
    )


def perturb_reconstructed_graph(
    record: ReconstructedGraphRecord,
    *,
    noise_type: GraphNoiseType,
    noise_level: float,
    predicates: list[str] | None = None,
    rng: random.Random | None = None,
) -> tuple[ReconstructedGraphRecord, GraphPerturbationRecord]:
    predicates = predicates or ["relatedTo"]
    rng = rng or random.Random(0)
    perturbed = record.model_copy(deep=True)
    operations: list[GraphPerturbationOperation] = []

    if noise_level <= 0.0:
        pass
    elif noise_type == "drop_edge":
        kept_edges: list[ReconstructedEdge] = []
        for edge in perturbed.edges:
            drop = rng.random() < noise_level
            operations.append(_operation(record.example_id, "drop_edge", _edge_id(edge), None, drop))
            if not drop:
                kept_edges.append(edge)
        perturbed.edges = kept_edges
    elif noise_type == "drop_node":
        kept_nodes: list[str] = []
        dropped_nodes: set[str] = set()
        for node in perturbed.nodes:
            drop = rng.random() < noise_level
            operations.append(_operation(record.example_id, "drop_node", node, None, drop))
            if drop:
                dropped_nodes.add(node)
            else:
                kept_nodes.append(node)
        perturbed.nodes = kept_nodes
        before_edges = len(perturbed.edges)
        perturbed.edges = [edge for edge in perturbed.edges if edge.subj not in dropped_nodes and edge.obj not in dropped_nodes]
        if dropped_nodes and len(perturbed.edges) != before_edges:
            operations.append(
                _operation(
                    record.example_id,
                    "remove_incident_edges",
                    ",".join(sorted(dropped_nodes)),
                    None,
                    True,
                    removed_edges=before_edges - len(perturbed.edges),
                )
            )
    elif noise_type == "graph_swap_predicate":
        for idx, edge in enumerate(perturbed.edges):
            if rng.random() >= noise_level:
                continue
            candidates = [predicate for predicate in predicates if predicate != edge.pred]
            if not candidates:
                continue
            old_pred = edge.pred
            new_pred = rng.choice(candidates)
            perturbed.edges[idx] = edge.model_copy(update={"pred": new_pred, "confidence": min(edge.confidence, 0.25)})
            operations.append(_operation(record.example_id, "graph_swap_predicate", old_pred, new_pred, True, edge_id=_edge_id(edge)))
    elif noise_type == "hallucinate_edge":
        # Add up to ceil(level * current_edges) extra wrong edges. Hallucinated
        # edges affect precision-style analysis and are recorded separately.
        if len(perturbed.nodes) >= 2:
            add_count = max(1, round(noise_level * max(1, len(perturbed.edges))))
            for idx in range(add_count):
                subj, obj = rng.sample(perturbed.nodes, 2)
                pred = rng.choice(predicates)
                new_edge = ReconstructedEdge(
                    subj=subj,
                    pred=pred,
                    obj=obj,
                    gold_edge_index=-1,
                    confidence=0.1,
                    evidence={"calibration": "hallucinated_edge"},
                )
                perturbed.edges.append(new_edge)
                operations.append(_operation(record.example_id, "hallucinate_edge", None, _edge_id(new_edge), True, index=idx))
    else:  # pragma: no cover - guarded by CLI choices
        raise ValueError(f"Unsupported graph noise type: {noise_type}")

    perturbed.metadata = dict(perturbed.metadata)
    perturbed.metadata["calibration_noise"] = {
        "noise_type": noise_type,
        "noise_level": noise_level,
        "expected_direction": GRAPH_NOISE_EXPECTED_DIRECTION.get(noise_type, "down"),
    }
    manifest = GraphPerturbationRecord(
        example_id=record.example_id,
        noise_type=noise_type,
        noise_level=noise_level,
        expected_direction=GRAPH_NOISE_EXPECTED_DIRECTION.get(noise_type, "down"),
        original_node_count=len(record.nodes),
        perturbed_node_count=len(perturbed.nodes),
        original_edge_count=len(record.edges),
        perturbed_edge_count=len(perturbed.edges),
        operations=operations,
    )
    return perturbed, manifest


def perturb_reconstructed_graph_corpus(
    examples: list[GraphTextExample],
    records: list[ReconstructedGraphRecord],
    *,
    noise_type: GraphNoiseType,
    noise_level: float,
    seed: int = 42,
) -> tuple[list[ReconstructedGraphRecord], list[GraphPerturbationRecord]]:
    rng = random.Random(seed)
    predicates = _predicate_pool(examples)
    perturbed: list[ReconstructedGraphRecord] = []
    manifests: list[GraphPerturbationRecord] = []
    for record in records:
        item, manifest = perturb_reconstructed_graph(
            record,
            noise_type=noise_type,
            noise_level=noise_level,
            predicates=predicates,
            rng=rng,
        )
        perturbed.append(item)
        manifests.append(manifest)
    return perturbed, manifests


def write_graph_perturbation_artifacts(
    records: list[ReconstructedGraphRecord],
    manifests: list[GraphPerturbationRecord],
    *,
    reconstructed_out: str | Path,
    manifest_out: str | Path,
) -> None:
    write_reconstructed_graphs(records, reconstructed_out)
    manifest_path = Path(manifest_out)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as stream:
        for manifest in manifests:
            stream.write(json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False) + "\n")


def count_effective_graph_operations(records: list[GraphPerturbationRecord]) -> int:
    return sum(1 for record in records for operation in record.operations if operation.changed)
