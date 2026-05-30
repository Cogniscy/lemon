"""Core utilities for a MINE-1-compatible retention baseline.

MINE-1 evaluates whether reference facts are recoverable from an extracted
knowledge graph.  A fact is used as a query, relevant graph nodes are retrieved,
a two-hop neighborhood is induced, and a binary judge decides whether the fact
follows from that subgraph.  The MINE-1 score is the mean of those binary
recoverability decisions.

This module implements the same evaluation shape for controlled LEMON
perturbation records.  It intentionally remains a *compatible local baseline*,
not a vendored copy of the KGGen implementation.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Any, Iterable

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


@dataclass(frozen=True)
class GraphEdge:
    subject: str
    predicate: str
    object: str

    def as_text(self) -> str:
        return f"{self.subject} {self.predicate} {self.object}"


def norm_text(value: Any) -> str:
    return " ".join(str(value or "").replace("_", " ").split())


def tokenize(value: Any) -> set[str]:
    return {tok.lower() for tok in _TOKEN_RE.findall(norm_text(value)) if tok}


def lexical_overlap(a: Any, b: Any) -> float:
    ta = tokenize(a)
    tb = tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def node_label_map(record: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for node in record.get("nodes", []) or []:
        node_id = str(node.get("id", ""))
        if node_id:
            mapping[node_id] = norm_text(node.get("label", node_id)) or node_id
    return mapping


def edge_to_labeled(edge: dict[str, Any], labels: dict[str, str]) -> GraphEdge:
    subj_id = str(edge.get("subj", edge.get("subject", "")))
    obj_id = str(edge.get("obj", edge.get("object", "")))
    return GraphEdge(
        subject=labels.get(subj_id, norm_text(edge.get("subject", subj_id)) or subj_id),
        predicate=norm_text(edge.get("pred", edge.get("predicate", ""))),
        object=labels.get(obj_id, norm_text(edge.get("object", obj_id)) or obj_id),
    )


def labeled_edges(record: dict[str, Any]) -> list[GraphEdge]:
    labels = node_label_map(record)
    return [edge_to_labeled(edge, labels) for edge in record.get("edges", []) or []]


def fact_for_edge(record: dict[str, Any], edge_index: int | None = None) -> dict[str, Any] | None:
    facts = record.get("facts", []) or []
    if edge_index is not None:
        for fact in facts:
            if edge_index in (fact.get("edge_refs") or []):
                return fact
    return facts[0] if facts else None


def operation_edge_indices(record: dict[str, Any]) -> list[int]:
    indices: list[int] = []
    for op in record.get("operations", []) or []:
        if isinstance(op.get("edge_index"), int):
            indices.append(int(op["edge_index"]))
    return indices


def target_edge_index(record: dict[str, Any]) -> int | None:
    indices = operation_edge_indices(record)
    if indices:
        return indices[0]
    return 0 if record.get("edges") else None


def apply_controlled_perturbation(record: dict[str, Any]) -> list[GraphEdge]:
    """Build a graph-side analogue of a controlled perturbation record.

    LEMON perturbation files primarily modify text.  For a MINE-like graph
    recoverability check, we create the graph-side analogue of the same damage:
    edge deletion removes an edge, node deletion removes incident edges,
    argument swap reverses one edge, polarity flip marks the predicate as
    negated, and relation blur replaces the predicate by a generic relation.
    """

    edges = labeled_edges(record)
    if not edges:
        return []

    variant = str(record.get("variant", ""))
    operations = record.get("operations", []) or []
    if not operations:
        return edges

    mutable = list(edges)
    remove_indices: set[int] = set()

    for op in operations:
        edge_index = op.get("edge_index")
        if not isinstance(edge_index, int) or edge_index < 0 or edge_index >= len(mutable):
            continue
        edge = mutable[edge_index]
        target = norm_text(op.get("target"))

        if variant == "edge_deletion":
            remove_indices.add(edge_index)
        elif variant == "node_deletion":
            if target:
                for i, candidate in enumerate(mutable):
                    if norm_text(candidate.subject).lower() == target.lower() or norm_text(candidate.object).lower() == target.lower():
                        remove_indices.add(i)
            else:
                remove_indices.add(edge_index)
        elif variant == "argument_swap":
            mutable[edge_index] = GraphEdge(subject=edge.object, predicate=edge.predicate, object=edge.subject)
        elif variant == "polarity_flip":
            mutable[edge_index] = GraphEdge(subject=edge.subject, predicate=f"NEGATED_{edge.predicate}", object=edge.object)
        elif variant == "relation_blur":
            mutable[edge_index] = GraphEdge(subject=edge.subject, predicate="related_to", object=edge.object)

    return [edge for i, edge in enumerate(mutable) if i not in remove_indices]


def graph_nodes(edges: Iterable[GraphEdge]) -> list[str]:
    seen: dict[str, None] = {}
    for edge in edges:
        seen.setdefault(edge.subject, None)
        seen.setdefault(edge.object, None)
    return list(seen.keys())


def retrieve_nodes(fact: str, nodes: list[str], top_k: int = 3) -> list[str]:
    scored = [(lexical_overlap(fact, node), node) for node in nodes]
    scored.sort(key=lambda pair: (-pair[0], pair[1].lower()))
    return [node for score, node in scored[: max(1, top_k)] if score > 0]


def expand_subgraph(edges: list[GraphEdge], seed_nodes: Iterable[str], hops: int = 2) -> tuple[list[str], list[GraphEdge]]:
    seed = {norm_text(node) for node in seed_nodes if norm_text(node)}
    if not seed:
        return [], []
    adjacency: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        s = norm_text(edge.subject)
        o = norm_text(edge.object)
        adjacency[s].add(o)
        adjacency[o].add(s)

    visited = set(seed)
    queue: deque[tuple[str, int]] = deque((node, 0) for node in seed)
    while queue:
        node, dist = queue.popleft()
        if dist >= hops:
            continue
        for nxt in adjacency.get(node, set()):
            if nxt not in visited:
                visited.add(nxt)
                queue.append((nxt, dist + 1))

    sub_edges = [edge for edge in edges if norm_text(edge.subject) in visited and norm_text(edge.object) in visited]
    return sorted(visited), sub_edges


def fact_components(item: dict[str, Any]) -> tuple[str, str, str]:
    edge = item.get("reference_edge") or item.get("source_edge") or {}
    return (
        norm_text(edge.get("subject", "")),
        norm_text(edge.get("predicate", "")),
        norm_text(edge.get("object", "")),
    )


def lexical_binary_judge(item: dict[str, Any], subgraph_edges: list[GraphEdge]) -> tuple[bool, dict[str, Any]]:
    subj, pred, obj = fact_components(item)
    subgraph_text = " ".join(edge.as_text() for edge in subgraph_edges)
    sub_tokens = tokenize(subgraph_text)
    subj_ok = bool(tokenize(subj) & sub_tokens)
    obj_ok = bool(tokenize(obj) & sub_tokens)

    pred_tokens = tokenize(pred)
    pred_ok = bool(pred_tokens & sub_tokens) if pred_tokens else True

    negated_candidate = any(edge.predicate.startswith("NEGATED_") for edge in subgraph_edges)
    generic_only = bool(subgraph_edges) and all(edge.predicate == "related_to" for edge in subgraph_edges)
    recoverable = subj_ok and obj_ok and pred_ok and not negated_candidate and not generic_only
    diagnostics = {
        "subject_found": subj_ok,
        "object_found": obj_ok,
        "predicate_found": pred_ok,
        "negated_candidate": negated_candidate,
        "generic_only": generic_only,
    }
    return recoverable, diagnostics


def retrieval_context(item: dict[str, Any], *, top_k: int = 3, hops: int = 2) -> dict[str, Any]:
    edges = [GraphEdge(**edge) for edge in item.get("candidate_graph", {}).get("edges", [])]
    fact = norm_text(item.get("fact", ""))
    nodes = graph_nodes(edges)
    retrieved = retrieve_nodes(fact, nodes, top_k=top_k)
    sub_nodes, sub_edges = expand_subgraph(edges, retrieved, hops=hops)
    return {
        "item_id": item.get("id"),
        "dataset": item.get("dataset"),
        "variant": item.get("variant"),
        "fact": fact,
        "reference_edge": item.get("reference_edge", {}),
        "retrieved_nodes": retrieved,
        "subgraph_nodes": sub_nodes,
        "subgraph_edges": [edge.__dict__ for edge in sub_edges],
        "top_k": top_k,
        "hops": hops,
    }


def score_item(item: dict[str, Any], *, top_k: int = 3, hops: int = 2) -> dict[str, Any]:
    context = retrieval_context(item, top_k=top_k, hops=hops)
    sub_edges = [GraphEdge(**edge) for edge in context.get("subgraph_edges", [])]
    recoverable, diagnostics = lexical_binary_judge(item, sub_edges)
    return {
        **context,
        "recoverable": bool(recoverable),
        "score": 1.0 if recoverable else 0.0,
        "judge_mode": "lexical",
        "diagnostics": diagnostics,
    }


def score_item_with_judgment(item: dict[str, Any], judgment: dict[str, Any], *, top_k: int = 3, hops: int = 2) -> dict[str, Any]:
    context = retrieval_context(item, top_k=top_k, hops=hops)
    recoverable = bool(judgment.get("recoverable"))
    return {
        **context,
        "recoverable": recoverable,
        "score": 1.0 if recoverable else 0.0,
        "judge_mode": str(judgment.get("judge_id") or judgment.get("model") or "llm_saved"),
        "confidence": judgment.get("confidence"),
        "rationale": judgment.get("rationale") or judgment.get("evidence"),
        "raw_judgment": judgment,
    }


def parse_recoverability_judgment(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize saved MINE-like LLM judgments.

    Accepted shapes:
    * {"item_id": ..., "recoverable": true, ...}
    * {"id": ..., "content": "{...json...}"} from OpenRouter-style raw logs
    * {"item_id": ..., "judgment": {"recoverable": ...}}
    """
    if "judgment" in row and isinstance(row["judgment"], dict):
        merged = {**row["judgment"]}
        merged.setdefault("item_id", row.get("item_id") or row.get("id"))
        return parse_recoverability_judgment(merged)

    if "content" in row and isinstance(row["content"], str):
        content = row["content"].strip()
        if content.startswith("```"):
            content = content.strip("`")
            if content.startswith("json"):
                content = content[4:].strip()
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Could not parse judgment content for {row.get('item_id') or row.get('id')}") from exc
        parsed.setdefault("item_id", row.get("item_id") or row.get("id"))
        parsed.setdefault("judge_id", row.get("judge_id"))
        parsed.setdefault("model", row.get("model"))
        return parse_recoverability_judgment(parsed)

    item_id = row.get("item_id") or row.get("id")
    if not item_id:
        raise ValueError("Judgment is missing item_id")
    if "recoverable" not in row:
        raise ValueError(f"Judgment for {item_id} is missing recoverable")
    value = row.get("recoverable")
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "yes", "1", "recoverable"}:
            value = True
        elif lowered in {"false", "no", "0", "not_recoverable", "unrecoverable"}:
            value = False
        else:
            raise ValueError(f"Invalid recoverable value for {item_id}: {value!r}")
    return {**row, "item_id": item_id, "recoverable": bool(value)}


def mine1_score(decisions: Iterable[bool | int | float]) -> float:
    values = [1.0 if bool(value) else 0.0 for value in decisions]
    if not values:
        return 0.0
    return sum(values) / len(values)


def summarize_scores(scores: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in scores:
        groups[(str(row.get("dataset")), str(row.get("variant")))].append(row)
    by_group = []
    for (dataset, variant), rows in sorted(groups.items()):
        by_group.append(
            {
                "dataset": dataset,
                "variant": variant,
                "items": len(rows),
                "mine1_like_score": round(mine1_score(row.get("recoverable", False) for row in rows), 4),
            }
        )
    return {
        "items": len(scores),
        "mine1_like_score": round(mine1_score(row.get("recoverable", False) for row in scores), 4),
        "by_dataset_variant": by_group,
    }


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    with Path(path).open(encoding="utf8") as fh:
        for line_no, line in enumerate(fh, start=1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSONL at {path}:{line_no}") from exc
    return rows


def write_jsonl(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def harmonic_mean(a: float, b: float) -> float:
    if a <= 0 or b <= 0:
        return 0.0
    return 2 * a * b / (a + b)
