"""MINE-style node/edge information retention scoring.

The deterministic mode scores node and edge hits directly. The LLM-judged mode
keeps the same retrieved subgraph but delegates fact recoverability to a binary
judge, which better matches the MINE idea of checking whether a fact can be
inferred from retrieved nodes and relations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from lemon_factor.mine_nodes_edges.retrieval import (
    expand_reconstructed_subgraph,
    fact_text_for_edge,
    retrieve_top_k_nodes,
)
from lemon_factor.reverse.reconstruct_graph import ReconstructedGraphRecord
from lemon_factor.schema.graphtext import Edge, GraphTextExample

JudgeMode = Literal["deterministic", "offline", "llm"]


class MineStyleFactScore(BaseModel):
    fact_id: str
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
    judge_mode: JudgeMode = "deterministic"
    judge_recoverable: bool | None = None
    judge_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    judge_reason: str | None = None
    judge_evidence_nodes: list[str] = Field(default_factory=list)
    judge_evidence_edges: list[str] = Field(default_factory=list)


class MineStyleReport(BaseModel):
    examples: int
    facts: int
    node_information: float
    edge_information: float
    retrieved_edge_hit_rate: float
    fact_recoverability: float
    mine_style_score: float
    composite_node_edge_score: float
    deterministic_fact_recoverability: float | None = None
    llm_fact_recoverability: float | None = None
    deterministic_node_information_on_subset: float | None = None
    deterministic_edge_information_on_subset: float | None = None
    deterministic_fact_recoverability_on_subset: float | None = None
    judged_facts: int = 0
    requested_judgments: int | None = None
    valid_judgments: int | None = None
    failed_judgments: int | None = None
    judge_parse_success_rate: float | None = None
    parse_success_rate: float | None = None
    retry_attempts: int = 0
    retry_successes: int = 0
    judge_changed_count: int | None = None
    judge_agreement_with_deterministic: float | None = None
    deterministic_score_on_subset: float | None = None
    mean_judge_confidence: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


def _safe_avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def _safe_optional_avg(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 6) if values else None


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
        fact_id=f"{example.id}::edge-{edge_index}",
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
    report = build_mine_style_report(scores, examples=len(examples), top_k=top_k, hops=hops, judge_mode="deterministic")
    return report, scores


def apply_fact_judgments(
    scores: list[MineStyleFactScore],
    judgments: dict[str, Any],
    *,
    judge_mode: JudgeMode,
) -> list[MineStyleFactScore]:
    """Return scores with LLM/offline judgment fields applied.

    Only facts present in ``judgments`` are returned. This prevents silent mixing
    of LLM-judged and deterministic facts when --limit is used.
    """

    judged_scores: list[MineStyleFactScore] = []
    for score in scores:
        judgment = judgments.get(score.fact_id)
        if judgment is None:
            continue
        updated = score.model_copy(deep=True)
        updated.judge_mode = judge_mode
        updated.judge_recoverable = bool(judgment.recoverable)
        updated.judge_confidence = judgment.confidence
        updated.judge_reason = judgment.reason
        updated.judge_evidence_nodes = list(judgment.evidence_nodes)
        updated.judge_evidence_edges = list(judgment.evidence_edges)
        updated.fact_recoverable = bool(judgment.recoverable)
        updated.mine_style_score = 1.0 if judgment.recoverable else 0.0
        judged_scores.append(updated)
    return judged_scores


def build_mine_style_report(
    scores: list[MineStyleFactScore],
    *,
    examples: int,
    top_k: int,
    hops: int,
    judge_mode: JudgeMode,
    parse_success_rate: float | None = None,
    models: list[str] | None = None,
    requested_judgments: int | None = None,
    failed_judgments: int | None = None,
    retry_attempts: int = 0,
    retry_successes: int = 0,
    deterministic_scores: list[MineStyleFactScore] | None = None,
) -> MineStyleReport:
    confidence_values = [score.judge_confidence for score in scores if score.judge_confidence is not None]
    judged_facts = sum(1 for score in scores if score.judge_recoverable is not None)
    valid_judgments = judged_facts if judge_mode != "deterministic" else None
    failed = failed_judgments
    if requested_judgments is not None and valid_judgments is not None and failed is None:
        failed = max(requested_judgments - valid_judgments, 0)

    deterministic_subset_score: float | None = None
    deterministic_node_subset: float | None = None
    deterministic_edge_subset: float | None = None
    deterministic_fact_subset: float | None = None
    judge_changed_count: int | None = None
    judge_agreement: float | None = None
    if deterministic_scores is not None and scores:
        deterministic_by_id = {score.fact_id: score for score in deterministic_scores}
        deterministic_values = [deterministic_by_id[score.fact_id].mine_style_score for score in scores if score.fact_id in deterministic_by_id]
        deterministic_subset_score = _safe_optional_avg([float(value) for value in deterministic_values])
        deterministic_node_subset = _safe_optional_avg([
            float(deterministic_by_id[score.fact_id].node_information) for score in scores if score.fact_id in deterministic_by_id
        ])
        deterministic_edge_subset = _safe_optional_avg([
            float(deterministic_by_id[score.fact_id].edge_information) for score in scores if score.fact_id in deterministic_by_id
        ])
        deterministic_fact_subset = _safe_optional_avg([
            float(deterministic_by_id[score.fact_id].fact_recoverable) for score in scores if score.fact_id in deterministic_by_id
        ])
        if judge_mode != "deterministic":
            comparable = [score for score in scores if score.fact_id in deterministic_by_id and score.judge_recoverable is not None]
            judge_changed_count = sum(
                1 for score in comparable if deterministic_by_id[score.fact_id].fact_recoverable != bool(score.judge_recoverable)
            )
            judge_agreement = round(
                (len(comparable) - judge_changed_count) / len(comparable), 6
            ) if comparable else None

    node_information = _safe_avg([score.node_information for score in scores])
    edge_information = _safe_avg([score.edge_information for score in scores])
    fact_recoverability = _safe_avg([float(score.fact_recoverable) for score in scores])
    mine_style_score = _safe_avg([score.mine_style_score for score in scores])
    composite_node_edge_score = round(0.5 * node_information + 0.5 * edge_information, 6)
    deterministic_fact_recoverability = fact_recoverability if judge_mode == "deterministic" else deterministic_fact_subset
    llm_fact_recoverability = fact_recoverability if judge_mode == "llm" else None

    return MineStyleReport(
        examples=examples,
        facts=len(scores),
        node_information=node_information,
        edge_information=edge_information,
        retrieved_edge_hit_rate=_safe_avg([float(score.retrieved_edge_hit) for score in scores]),
        fact_recoverability=fact_recoverability,
        mine_style_score=mine_style_score,
        composite_node_edge_score=composite_node_edge_score,
        deterministic_fact_recoverability=deterministic_fact_recoverability,
        llm_fact_recoverability=llm_fact_recoverability,
        deterministic_node_information_on_subset=deterministic_node_subset,
        deterministic_edge_information_on_subset=deterministic_edge_subset,
        deterministic_fact_recoverability_on_subset=deterministic_fact_subset,
        judged_facts=judged_facts,
        requested_judgments=requested_judgments,
        valid_judgments=valid_judgments,
        failed_judgments=failed,
        judge_parse_success_rate=parse_success_rate,
        parse_success_rate=parse_success_rate,
        retry_attempts=retry_attempts,
        retry_successes=retry_successes,
        judge_changed_count=judge_changed_count,
        judge_agreement_with_deterministic=judge_agreement,
        deterministic_score_on_subset=deterministic_subset_score,
        mean_judge_confidence=_safe_optional_avg([float(value) for value in confidence_values]),
        metadata={
            "direction": "text_to_kg",
            "metric": "mine_style_nodes_edges",
            "top_k": top_k,
            "hops": hops,
            "judge_mode": judge_mode,
            "llm_judge": judge_mode == "llm",
            "score_semantics": "binary_fact_recoverability" if judge_mode == "llm" else "composite_node_edge_score",
            "adapts": "KGGen Measure of Information in Nodes and Edges (MINE)",
            "models": models or [],
        },
    )


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
