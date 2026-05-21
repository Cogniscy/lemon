"""MINE-style deterministic retrieval over reconstructed nodes and edges.

KGGen's MINE benchmark evaluates information in nodes and edges of extracted
knowledge graphs. This module provides a lightweight WebNLG adaptation: gold
triples are treated as facts, reconstructed graphs are treated as extracted KGs,
and retrieval is performed by lexical node/fact overlap.
"""

from __future__ import annotations

from collections import deque

from lemon_factor.coverage.text_evidence import text_tokens, token_overlap_score
from lemon_factor.reverse.reconstruct_graph import ReconstructedEdge, ReconstructedGraphRecord
from lemon_factor.schema.graphtext import Edge, GraphTextExample


def fact_text_for_edge(example: GraphTextExample, edge: Edge) -> str:
    labels = example.node_labels()
    return f"{labels.get(edge.subj, edge.subj)} {edge.pred} {labels.get(edge.obj, edge.obj)}"


def retrieve_top_k_nodes(
    example: GraphTextExample,
    record: ReconstructedGraphRecord,
    fact_text: str,
    *,
    k: int = 2,
) -> list[tuple[str, float]]:
    if k <= 0:
        raise ValueError("k must be positive")
    recovered_nodes = record.node_set()
    labels = example.node_labels()
    scored = [
        (node_id, token_overlap_score(labels.get(node_id, node_id), fact_text))
        for node_id in recovered_nodes
    ]
    # Deterministic tie-breaker keeps runs stable.
    scored.sort(key=lambda item: (-item[1], item[0]))
    return scored[:k]


def expand_reconstructed_subgraph(
    record: ReconstructedGraphRecord,
    seed_node_ids: list[str],
    *,
    hops: int = 2,
) -> list[ReconstructedEdge]:
    if hops < 0:
        raise ValueError("hops must be non-negative")
    recovered_nodes = record.node_set()
    for seed in seed_node_ids:
        if seed not in recovered_nodes:
            raise ValueError(f"Unknown reconstructed seed node {seed!r}")

    adjacency: dict[str, list[tuple[str, int]]] = {node_id: [] for node_id in recovered_nodes}
    for idx, edge in enumerate(record.edges):
        adjacency.setdefault(edge.subj, []).append((edge.obj, idx))
        adjacency.setdefault(edge.obj, []).append((edge.subj, idx))

    seen_nodes = set(seed_node_ids)
    seen_edges: set[int] = set()
    queue: deque[tuple[str, int]] = deque((seed, 0) for seed in seed_node_ids)
    while queue:
        node_id, depth = queue.popleft()
        if depth >= hops:
            continue
        for neighbor, edge_idx in adjacency.get(node_id, []):
            seen_edges.add(edge_idx)
            if neighbor not in seen_nodes:
                seen_nodes.add(neighbor)
                queue.append((neighbor, depth + 1))
    return [record.edges[idx] for idx in sorted(seen_edges)]


def lexical_fact_node_overlap(fact_text: str, node_label: str) -> float:
    fact_tokens = set(text_tokens(fact_text))
    node_tokens = set(text_tokens(node_label))
    if not node_tokens:
        return 0.0
    return len(fact_tokens & node_tokens) / len(node_tokens)
