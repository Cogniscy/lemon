"""MINE-compatible retrieval primitives.

This module does not implement an LLM judge. It implements deterministic graph
retrieval pieces that are easy to test: top-k retrieval over supplied vectors
and 2-hop graph expansion from retrieved nodes.
"""

from __future__ import annotations

from collections import deque
from math import sqrt
from typing import Mapping, Sequence

from lemon_factor.schema.graphtext import Edge, GraphTextExample

Vector = Sequence[float]


def cosine(left: Vector, right: Vector) -> float:
    if len(left) != len(right):
        raise ValueError("Vectors must have equal length")
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = sqrt(sum(a * a for a in left))
    right_norm = sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def top_k_nodes(
    fact_embedding: Vector,
    node_embeddings: Mapping[str, Vector],
    *,
    k: int,
) -> list[tuple[str, float]]:
    if k <= 0:
        raise ValueError("k must be positive")
    scored = [
        (node_id, cosine(fact_embedding, embedding))
        for node_id, embedding in node_embeddings.items()
    ]
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]


def expand_subgraph(
    example: GraphTextExample,
    seed_node_ids: Sequence[str],
    *,
    hops: int = 2,
) -> list[Edge]:
    """Return edges reachable within `hops` undirected graph steps."""

    if hops < 0:
        raise ValueError("hops must be non-negative")
    known_nodes = {node.id for node in example.nodes}
    for seed in seed_node_ids:
        if seed not in known_nodes:
            raise ValueError(f"Unknown seed node {seed!r}")

    adjacency: dict[str, list[tuple[str, int]]] = {node.id: [] for node in example.nodes}
    for idx, edge in enumerate(example.edges):
        adjacency[edge.subj].append((edge.obj, idx))
        adjacency[edge.obj].append((edge.subj, idx))

    seen_nodes = set(seed_node_ids)
    seen_edges: set[int] = set()
    queue: deque[tuple[str, int]] = deque((seed, 0) for seed in seed_node_ids)

    while queue:
        node_id, depth = queue.popleft()
        if depth >= hops:
            continue
        for neighbor, edge_idx in adjacency[node_id]:
            seen_edges.add(edge_idx)
            if neighbor not in seen_nodes:
                seen_nodes.add(neighbor)
                queue.append((neighbor, depth + 1))

    return [example.edges[idx] for idx in sorted(seen_edges)]
