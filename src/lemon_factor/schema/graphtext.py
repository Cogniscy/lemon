"""Unified GraphText schema.

The schema is intentionally compact. It is meant to normalize WebNLG, BioRED,
MINE-style examples, and later small medical literature corpora into one
research format.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class Split(str, Enum):
    train = "train"
    dev = "dev"
    test = "test"
    pilot = "pilot"


class Node(BaseModel):
    """Graph node."""

    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    type: str | None = None
    aliases: list[str] = Field(default_factory=list)
    external_ids: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Edge(BaseModel):
    """Directed graph edge."""

    subj: str = Field(min_length=1)
    pred: str = Field(min_length=1)
    obj: str = Field(min_length=1)
    evidence: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Fact(BaseModel):
    """Fact used for MINE/LEMON-style evaluation."""

    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    source: Literal["gold", "manual", "derived", "mine"] = "gold"
    edge_refs: list[int] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphTextExample(BaseModel):
    """One text plus its explicit graph and fact list."""

    id: str = Field(min_length=1)
    dataset: str = Field(min_length=1)
    split: Split
    text: str = ""
    language: str | None = None
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    facts: list[Fact] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_edge_node_refs(self) -> "GraphTextExample":
        node_ids = {node.id for node in self.nodes}
        for edge in self.edges:
            if edge.subj not in node_ids:
                raise ValueError(f"Edge subject {edge.subj!r} is not defined in nodes")
            if edge.obj not in node_ids:
                raise ValueError(f"Edge object {edge.obj!r} is not defined in nodes")
        for fact in self.facts:
            for edge_ref in fact.edge_refs:
                if edge_ref < 0 or edge_ref >= len(self.edges):
                    raise ValueError(
                        f"Fact {fact.id!r} references missing edge index {edge_ref}"
                    )
        return self

    def node_labels(self) -> dict[str, str]:
        return {node.id: node.label for node in self.nodes}
