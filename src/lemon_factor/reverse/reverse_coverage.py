"""Reverse LEMON-Factor coverage for reconstructed text-to-KG graphs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from lemon_factor.factors.decomposition import PredicateDecompositionSet
from lemon_factor.reverse.reconstruct_graph import ReconstructedGraphRecord
from lemon_factor.schema.graphtext import Edge, GraphTextExample


class ReverseComponentResult(BaseModel):
    factor: str
    role: str
    weight: float
    covered: bool
    score: float = Field(ge=0.0, le=1.0)
    evidence_type: str = "none"


class ReverseEdgeResult(BaseModel):
    example_id: str
    edge_index: int
    subject: str
    predicate: str
    object: str
    score: float = Field(ge=0.0, le=1.0)
    node_recovery_score: float = Field(ge=0.0, le=1.0)
    edge_recovered: bool
    missing_decomposition: bool = False
    components: list[ReverseComponentResult] = Field(default_factory=list)


class ReverseExampleResult(BaseModel):
    example_id: str
    edge_count: int
    recovered_edge_count: int
    score: float = Field(ge=0.0, le=1.0)
    node_recovery_score: float = Field(ge=0.0, le=1.0)
    edges: list[ReverseEdgeResult] = Field(default_factory=list)


class ReverseCoverageReport(BaseModel):
    examples: int
    edges: int
    recovered_edges: int
    edge_recovery_rate: float
    reverse_lemon_coverage: float
    node_recovery_score: float
    missing_decompositions: int
    metadata: dict[str, Any] = Field(default_factory=dict)


def _safe_avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def _edge_key(edge: Edge) -> tuple[str, str, str]:
    return (edge.subj, edge.pred, edge.obj)


def score_reverse_edge(
    example: GraphTextExample,
    edge: Edge,
    edge_index: int,
    record: ReconstructedGraphRecord,
    decompositions: PredicateDecompositionSet,
) -> ReverseEdgeResult:
    labels = example.node_labels()
    recovered_nodes = record.node_set()
    recovered_edges = record.edge_keys()
    subj_recovered = edge.subj in recovered_nodes
    obj_recovered = edge.obj in recovered_nodes
    edge_recovered = _edge_key(edge) in recovered_edges
    node_score = (float(subj_recovered) + float(obj_recovered)) / 2.0
    decomposition = decompositions.decompositions.get(edge.pred)
    if decomposition is None:
        return ReverseEdgeResult(
            example_id=example.id,
            edge_index=edge_index,
            subject=labels.get(edge.subj, edge.subj),
            predicate=edge.pred,
            object=labels.get(edge.obj, edge.obj),
            score=0.0,
            node_recovery_score=node_score,
            edge_recovered=edge_recovered,
            missing_decomposition=True,
        )

    component_results: list[ReverseComponentResult] = []
    for component in decomposition.components:
        if component.role == "subject_domain":
            covered = subj_recovered
            evidence_type = "subject_node" if covered else "none"
        elif component.role == "object_domain":
            covered = obj_recovered
            evidence_type = "object_node" if covered else "none"
        elif component.role == "predicate_meaning":
            covered = edge_recovered
            evidence_type = "reconstructed_edge" if covered else "none"
        else:
            covered = edge_recovered
            evidence_type = "reconstructed_edge" if covered else "none"
        component_results.append(
            ReverseComponentResult(
                factor=component.factor,
                role=component.role,
                weight=component.weight,
                covered=covered,
                score=1.0 if covered else 0.0,
                evidence_type=evidence_type,
            )
        )
    total_weight = sum(component.weight for component in component_results) or 1.0
    score = sum(component.weight * component.score for component in component_results) / total_weight
    return ReverseEdgeResult(
        example_id=example.id,
        edge_index=edge_index,
        subject=labels.get(edge.subj, edge.subj),
        predicate=edge.pred,
        object=labels.get(edge.obj, edge.obj),
        score=round(score, 6),
        node_recovery_score=round(node_score, 6),
        edge_recovered=edge_recovered,
        components=component_results,
    )


def score_reverse_example(
    example: GraphTextExample,
    record: ReconstructedGraphRecord,
    decompositions: PredicateDecompositionSet,
) -> ReverseExampleResult:
    edge_results = [
        score_reverse_edge(example, edge, idx, record, decompositions)
        for idx, edge in enumerate(example.edges)
    ]
    return ReverseExampleResult(
        example_id=example.id,
        edge_count=len(edge_results),
        recovered_edge_count=sum(1 for edge in edge_results if edge.edge_recovered),
        score=_safe_avg([edge.score for edge in edge_results]),
        node_recovery_score=_safe_avg([edge.node_recovery_score for edge in edge_results]),
        edges=edge_results,
    )


def score_reverse_corpus(
    examples: list[GraphTextExample],
    records: list[ReconstructedGraphRecord],
    decompositions: PredicateDecompositionSet,
) -> tuple[ReverseCoverageReport, list[ReverseExampleResult], list[ReverseEdgeResult]]:
    records_by_id = {record.example_id: record for record in records}
    missing_records = [example.id for example in examples if example.id not in records_by_id]
    if missing_records:
        raise ValueError(f"Missing reconstructed graph records for {len(missing_records)} examples")
    example_results = [
        score_reverse_example(example, records_by_id[example.id], decompositions) for example in examples
    ]
    edge_results = [edge for example in example_results for edge in example.edges]
    edge_count = len(edge_results)
    recovered_edges = sum(1 for edge in edge_results if edge.edge_recovered)
    report = ReverseCoverageReport(
        examples=len(examples),
        edges=edge_count,
        recovered_edges=recovered_edges,
        edge_recovery_rate=round(recovered_edges / edge_count, 6) if edge_count else 0.0,
        reverse_lemon_coverage=_safe_avg([edge.score for edge in edge_results]),
        node_recovery_score=_safe_avg([edge.node_recovery_score for edge in edge_results]),
        missing_decompositions=sum(1 for edge in edge_results if edge.missing_decomposition),
        metadata={"direction": "text_to_kg", "metric": "reverse_lemon"},
    )
    return report, example_results, edge_results


def write_reverse_outputs(
    report: ReverseCoverageReport,
    examples: list[ReverseExampleResult],
    edges: list[ReverseEdgeResult],
    *,
    out: str | Path,
    details: str | Path,
) -> None:
    out_path = Path(out)
    details_path = Path(details)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    details_path.parent.mkdir(parents=True, exist_ok=True)
    payload = report.model_dump(mode="json")
    payload["example_scores"] = [
        {key: value for key, value in example.model_dump(mode="json").items() if key != "edges"}
        for example in examples
    ]
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with details_path.open("w", encoding="utf-8") as stream:
        for edge in edges:
            stream.write(json.dumps(edge.model_dump(mode="json"), ensure_ascii=False) + "\n")
