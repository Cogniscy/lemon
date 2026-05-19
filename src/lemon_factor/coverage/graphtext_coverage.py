"""Example-level and corpus-level LEMON-Factor graph-text coverage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from lemon_factor.coverage.factor_coverage import (
    PredicateCoverageResult,
    missing_decomposition_result,
    score_predicate_decomposition,
)
from lemon_factor.factors.decomposition import PredicateDecompositionSet
from lemon_factor.schema.graphtext import Edge, GraphTextExample


class EdgeCoverageResult(BaseModel):
    example_id: str
    edge_index: int
    subject: str
    predicate: str
    object: str
    score: float = Field(ge=0.0, le=1.0)
    exact_label_score: float = Field(ge=0.0, le=1.0)
    predicate_cue_score: float = Field(ge=0.0, le=1.0)
    missing_decomposition: bool = False
    components: list[dict[str, Any]] = Field(default_factory=list)


class ExampleCoverageResult(BaseModel):
    example_id: str
    dataset: str
    split: str
    category: str | None = None
    edge_count: int
    scored_edge_count: int
    missing_decomposition_count: int
    score: float = Field(ge=0.0, le=1.0)
    exact_label_score: float = Field(ge=0.0, le=1.0)
    predicate_cue_score: float = Field(ge=0.0, le=1.0)
    edges: list[EdgeCoverageResult] = Field(default_factory=list)


class CorpusCoverageReport(BaseModel):
    examples: int
    edges: int
    scored_edges: int
    missing_decompositions: int
    missing_decomposition_rate: float
    lemon_factor_coverage: float
    exact_label_coverage: float
    predicate_cue_coverage: float
    low_coverage_edge_count: int
    metadata: dict[str, Any] = Field(default_factory=dict)


def _edge_result(
    example: GraphTextExample,
    edge: Edge,
    edge_index: int,
    predicate_result: PredicateCoverageResult,
) -> EdgeCoverageResult:
    labels = example.node_labels()
    return EdgeCoverageResult(
        example_id=example.id,
        edge_index=edge_index,
        subject=labels.get(edge.subj, edge.subj),
        predicate=edge.pred,
        object=labels.get(edge.obj, edge.obj),
        score=predicate_result.score,
        exact_label_score=predicate_result.exact_label_score,
        predicate_cue_score=predicate_result.predicate_cue_score,
        missing_decomposition=predicate_result.missing_decomposition,
        components=[component.model_dump(mode="json") for component in predicate_result.components],
    )


def score_edge_coverage(
    example: GraphTextExample,
    edge: Edge,
    edge_index: int,
    decompositions: PredicateDecompositionSet,
    lexical_cues: dict[str, list[str]] | None = None,
) -> EdgeCoverageResult:
    decomposition = decompositions.decompositions.get(edge.pred)
    if decomposition is None:
        result = missing_decomposition_result(edge, example.text, example.node_labels())
    else:
        result = score_predicate_decomposition(
            decomposition,
            example.text,
            edge,
            example.node_labels(),
            lexical_cues,
        )
    return _edge_result(example, edge, edge_index, result)


def _safe_avg(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 6)


def score_example_coverage(
    example: GraphTextExample,
    decompositions: PredicateDecompositionSet,
    lexical_cues: dict[str, list[str]] | None = None,
) -> ExampleCoverageResult:
    edge_results = [
        score_edge_coverage(example, edge, idx, decompositions, lexical_cues)
        for idx, edge in enumerate(example.edges)
    ]
    missing = sum(1 for result in edge_results if result.missing_decomposition)
    return ExampleCoverageResult(
        example_id=example.id,
        dataset=example.dataset,
        split=str(example.split.value if hasattr(example.split, "value") else example.split),
        category=example.metadata.get("category"),
        edge_count=len(example.edges),
        scored_edge_count=len(edge_results) - missing,
        missing_decomposition_count=missing,
        score=_safe_avg([result.score for result in edge_results]),
        exact_label_score=_safe_avg([result.exact_label_score for result in edge_results]),
        predicate_cue_score=_safe_avg([result.predicate_cue_score for result in edge_results]),
        edges=edge_results,
    )


def score_corpus_coverage(
    examples: list[GraphTextExample],
    decompositions: PredicateDecompositionSet,
    lexical_cues: dict[str, list[str]] | None = None,
    *,
    low_coverage_threshold: float = 0.5,
) -> tuple[CorpusCoverageReport, list[ExampleCoverageResult], list[EdgeCoverageResult]]:
    example_results = [score_example_coverage(example, decompositions, lexical_cues) for example in examples]
    edge_results = [edge for example in example_results for edge in example.edges]
    edge_count = len(edge_results)
    missing = sum(1 for edge in edge_results if edge.missing_decomposition)
    report = CorpusCoverageReport(
        examples=len(examples),
        edges=edge_count,
        scored_edges=edge_count - missing,
        missing_decompositions=missing,
        missing_decomposition_rate=round(missing / edge_count, 6) if edge_count else 0.0,
        lemon_factor_coverage=_safe_avg([edge.score for edge in edge_results]),
        exact_label_coverage=_safe_avg([edge.exact_label_score for edge in edge_results]),
        predicate_cue_coverage=_safe_avg([edge.predicate_cue_score for edge in edge_results]),
        low_coverage_edge_count=sum(1 for edge in edge_results if edge.score < low_coverage_threshold),
        metadata={"low_coverage_threshold": low_coverage_threshold},
    )
    return report, example_results, edge_results


def write_coverage_outputs(
    report: CorpusCoverageReport,
    examples: list[ExampleCoverageResult],
    edges: list[EdgeCoverageResult],
    *,
    out: str | Path,
    details: str | Path,
) -> None:
    out = Path(out)
    details = Path(details)
    out.parent.mkdir(parents=True, exist_ok=True)
    details.parent.mkdir(parents=True, exist_ok=True)
    payload = report.model_dump(mode="json")
    payload["example_scores"] = [
        {
            key: value
            for key, value in example.model_dump(mode="json").items()
            if key != "edges"
        }
        for example in examples
    ]
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with details.open("w", encoding="utf-8") as stream:
        for edge in edges:
            stream.write(json.dumps(edge.model_dump(mode="json"), ensure_ascii=False) + "\n")
