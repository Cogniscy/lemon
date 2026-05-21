"""Deterministic MINE-style node/edge information retention scoring."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from lemon_factor.mine_nodes_edges.retrieval import (
    expand_reconstructed_subgraph,
    fact_text_for_edge,
    retrieve_top_k_nodes,
)
from lemon_factor.reverse.reconstruct_graph import ReconstructedGraphRecord
from lemon_factor.schema.graphtext import Edge, GraphTextExample


class MineStyleFactScore(BaseModel):
    example_id: str
    edge_index: int
    fact_text: str
    subject_node_hit: bool
    object_node_hit: bool
    node_information: float = Field(ge=0.0, le=1.0)
    edge_information: float = Field(ge=0.0, le=1.0)
    retrieved_edge_hit: bool
    fact_recoverable: bool
    mine_style_score: float = Field(ge=0.0, le=1.0)
    retrieved_nodes: list[str] = Field(default_factory=list)
    retrieved_edges: list[dict[str, Any]] = Field(default_factory=list)


class MineStyleReport(BaseModel):
    examples: int
    facts: int
    node_information: float
    edge_information: float
    retrieved_edge_hit_rate: float
    fact_recoverability: float
    mine_style_score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


def _safe_avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def _edge_key(edge: Edge) -> tuple[str, str, str]:
    return (edge.subj, edge.pred, edge.obj)


def _reconstructed_edge_key(edge: Any) -> tuple[str, str, str]:
    return (edge.subj, edge.pred, edge.obj)


def score_mine_style_fact(
    example: GraphTextExample,
    edge: Edge,
    edge_index: int,
    record: ReconstructedGraphRecord,
    *,
    top_k: int = 2,
    hops: int = 2,
) -> MineStyleFactScore:
    recovered_nodes = record.node_set()
    edge_keys = record.edge_keys()
    fact_text = fact_text_for_edge(example, edge)
    retrieved_nodes_scored = retrieve_top_k_nodes(example, record, fact_text, k=top_k)
    retrieved_node_ids = [node_id for node_id, _score in retrieved_nodes_scored]
    retrieved_edges = expand_reconstructed_subgraph(record, retrieved_node_ids, hops=hops) if retrieved_node_ids else []
    retrieved_edge_keys = {_reconstructed_edge_key(retrieved_edge) for retrieved_edge in retrieved_edges}

    subject_hit = edge.subj in recovered_nodes
    object_hit = edge.obj in recovered_nodes
    node_information = (float(subject_hit) + float(object_hit)) / 2.0
    edge_information = 1.0 if _edge_key(edge) in edge_keys else 0.0
    retrieved_edge_hit = _edge_key(edge) in retrieved_edge_keys
    fact_recoverable = subject_hit and object_hit and retrieved_edge_hit
    mine_score = 0.5 * node_information + 0.5 * edge_information
    return MineStyleFactScore(
        example_id=example.id,
        edge_index=edge_index,
        fact_text=fact_text,
        subject_node_hit=subject_hit,
        object_node_hit=object_hit,
        node_information=round(node_information, 6),
        edge_information=edge_information,
        retrieved_edge_hit=retrieved_edge_hit,
        fact_recoverable=fact_recoverable,
        mine_style_score=round(mine_score, 6),
        retrieved_nodes=retrieved_node_ids,
        retrieved_edges=[edge.model_dump(mode="json") for edge in retrieved_edges],
    )


def score_mine_style_corpus(
    examples: list[GraphTextExample],
    records: list[ReconstructedGraphRecord],
    *,
    top_k: int = 2,
    hops: int = 2,
) -> tuple[MineStyleReport, list[MineStyleFactScore]]:
    records_by_id = {record.example_id: record for record in records}
    scores: list[MineStyleFactScore] = []
    for example in examples:
        if example.id not in records_by_id:
            raise ValueError(f"Missing reconstructed graph for {example.id!r}")
        record = records_by_id[example.id]
        for edge_index, edge in enumerate(example.edges):
            scores.append(score_mine_style_fact(example, edge, edge_index, record, top_k=top_k, hops=hops))
    report = MineStyleReport(
        examples=len(examples),
        facts=len(scores),
        node_information=_safe_avg([score.node_information for score in scores]),
        edge_information=_safe_avg([score.edge_information for score in scores]),
        retrieved_edge_hit_rate=_safe_avg([float(score.retrieved_edge_hit) for score in scores]),
        fact_recoverability=_safe_avg([float(score.fact_recoverable) for score in scores]),
        mine_style_score=_safe_avg([score.mine_style_score for score in scores]),
        metadata={
            "direction": "text_to_kg",
            "metric": "mine_style_nodes_edges",
            "top_k": top_k,
            "hops": hops,
            "llm_judge": False,
        },
    )
    return report, scores


def write_mine_style_outputs(
    report: MineStyleReport,
    scores: list[MineStyleFactScore],
    *,
    out: str | Path,
    scores_path: str | Path,
) -> None:
    out_path = Path(out)
    scores_out = Path(scores_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    scores_out.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with scores_out.open("w", encoding="utf-8") as stream:
        for score in scores:
            stream.write(json.dumps(score.model_dump(mode="json"), ensure_ascii=False) + "\n")
