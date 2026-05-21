"""Deterministic text-to-graph reconstruction baselines for reverse LEMON.

This module deliberately does not claim to be a full KG extractor. It builds
small reconstructed graphs from WebNLG text using entity-label and predicate-cue
evidence so that reverse graph/text metrics can be tested reproducibly.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from lemon_factor.coverage.factor_coverage import predicate_cue_score
from lemon_factor.coverage.text_evidence import label_in_text, token_overlap_score
from lemon_factor.datasets.unified_io import read_jsonl
from lemon_factor.schema.graphtext import GraphTextExample

ReconstructionMode = Literal["lexical", "oracle_nodes", "oracle_edges"]


class ReconstructedEdge(BaseModel):
    subj: str
    pred: str
    obj: str
    gold_edge_index: int
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: dict[str, object] = Field(default_factory=dict)


class ReconstructedGraphRecord(BaseModel):
    example_id: str
    mode: ReconstructionMode
    nodes: list[str] = Field(default_factory=list)
    edges: list[ReconstructedEdge] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)

    def node_set(self) -> set[str]:
        return set(self.nodes)

    def edge_keys(self) -> set[tuple[str, str, str]]:
        return {(edge.subj, edge.pred, edge.obj) for edge in self.edges}


def load_lexical_cues(path: str | Path | None) -> dict[str, list[str]]:
    if path is None:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def reconstruct_example_graph(
    example: GraphTextExample,
    *,
    lexical_cues: dict[str, list[str]] | None = None,
    mode: ReconstructionMode = "lexical",
) -> ReconstructedGraphRecord:
    """Build a deterministic reconstructed graph from text evidence.

    Modes:
    - lexical: recover nodes only when labels are mentioned; recover edges only
      when both endpoints are recovered and a predicate cue is present.
    - oracle_nodes: recover all gold nodes; recover edges by predicate cues.
    - oracle_edges: recover all gold nodes and edges. This is a ceiling mode.
    """

    lexical_cues = lexical_cues or {}
    labels = example.node_labels()

    if mode == "oracle_edges":
        nodes = [node.id for node in example.nodes]
    elif mode == "oracle_nodes":
        nodes = [node.id for node in example.nodes]
    else:
        nodes = [node.id for node in example.nodes if label_in_text(node.label, example.text)]

    recovered_nodes = set(nodes)
    reconstructed_edges: list[ReconstructedEdge] = []
    for edge_index, edge in enumerate(example.edges):
        subj_score = token_overlap_score(labels.get(edge.subj, edge.subj), example.text)
        obj_score = token_overlap_score(labels.get(edge.obj, edge.obj), example.text)
        pred_score = predicate_cue_score(edge.pred, example.text, lexical_cues)
        if mode == "oracle_edges":
            keep_edge = True
        else:
            keep_edge = edge.subj in recovered_nodes and edge.obj in recovered_nodes and pred_score > 0.0
        if keep_edge:
            confidence = round((subj_score + obj_score + pred_score) / 3.0, 6)
            if mode == "oracle_edges":
                confidence = 1.0
            reconstructed_edges.append(
                ReconstructedEdge(
                    subj=edge.subj,
                    pred=edge.pred,
                    obj=edge.obj,
                    gold_edge_index=edge_index,
                    confidence=confidence,
                    evidence={
                        "subject_label_score": round(subj_score, 6),
                        "object_label_score": round(obj_score, 6),
                        "predicate_cue_score": round(pred_score, 6),
                    },
                )
            )

    return ReconstructedGraphRecord(
        example_id=example.id,
        mode=mode,
        nodes=nodes,
        edges=reconstructed_edges,
        metadata={
            "gold_nodes": len(example.nodes),
            "gold_edges": len(example.edges),
            "recovered_nodes": len(nodes),
            "recovered_edges": len(reconstructed_edges),
        },
    )


def reconstruct_corpus(
    examples: list[GraphTextExample],
    *,
    lexical_cues: dict[str, list[str]] | None = None,
    mode: ReconstructionMode = "lexical",
) -> list[ReconstructedGraphRecord]:
    return [reconstruct_example_graph(example, lexical_cues=lexical_cues, mode=mode) for example in examples]


def write_reconstructed_graphs(records: list[ReconstructedGraphRecord], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record.model_dump(mode="json"), ensure_ascii=False) + "\n")


def read_reconstructed_graphs(path: str | Path) -> list[ReconstructedGraphRecord]:
    records: list[ReconstructedGraphRecord] = []
    with Path(path).open("r", encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(ReconstructedGraphRecord.model_validate_json(stripped))
            except Exception as exc:  # pragma: no cover
                raise ValueError(f"Invalid reconstructed graph at {path}:{line_no}") from exc
    return records


def summarize_reconstructed_graphs(
    examples: list[GraphTextExample], records: list[ReconstructedGraphRecord]
) -> dict[str, object]:
    gold_nodes = sum(len(example.nodes) for example in examples)
    gold_edges = sum(len(example.edges) for example in examples)
    recovered_nodes = sum(len(record.nodes) for record in records)
    recovered_edges = sum(len(record.edges) for record in records)
    return {
        "examples": len(examples),
        "gold_nodes": gold_nodes,
        "gold_edges": gold_edges,
        "recovered_nodes": recovered_nodes,
        "recovered_edges": recovered_edges,
        "node_recovery_rate": round(recovered_nodes / gold_nodes, 6) if gold_nodes else 0.0,
        "edge_recovery_rate": round(recovered_edges / gold_edges, 6) if gold_edges else 0.0,
        "mode": records[0].mode if records else None,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", help="Unified GraphText JSONL")
    parser.add_argument("--lexical-cues", default=None, help="Predicate/factor lexical cue JSON")
    parser.add_argument(
        "--mode",
        choices=["lexical", "oracle_nodes", "oracle_edges"],
        default="lexical",
        help="Deterministic reconstruction mode",
    )
    parser.add_argument("--out", required=True, help="Output reconstructed graph JSONL")
    parser.add_argument("--report", default=None, help="Optional reconstruction summary JSON")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    examples = read_jsonl(args.jsonl)
    lexical_cues = load_lexical_cues(args.lexical_cues)
    records = reconstruct_corpus(examples, lexical_cues=lexical_cues, mode=args.mode)
    write_reconstructed_graphs(records, args.out)
    payload = {"out": args.out}
    if args.report:
        report = summarize_reconstructed_graphs(examples, records)
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        payload["report"] = args.report
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
