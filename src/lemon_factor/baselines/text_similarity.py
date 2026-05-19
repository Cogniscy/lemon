"""Lightweight graph-text baseline similarities.

The module intentionally avoids heavyweight embedding dependencies.  It provides
transparent lexical baselines that can be run in CI and used as a lower bound
before optional sentence-transformer experiments are added.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping
from typing import Any

from lemon_factor.coverage.text_evidence import text_tokens


def jaccard_similarity(left: str, right: str) -> float:
    """Return set-token Jaccard similarity for two texts."""

    left_tokens = set(text_tokens(left))
    right_tokens = set(text_tokens(right))
    if not left_tokens and not right_tokens:
        return 1.0
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def token_cosine_similarity(left: str, right: str) -> float:
    """Return cosine similarity over normalized token-count vectors."""

    left_counts = Counter(text_tokens(left))
    right_counts = Counter(text_tokens(right))
    if not left_counts and not right_counts:
        return 1.0
    if not left_counts or not right_counts:
        return 0.0
    common = set(left_counts) & set(right_counts)
    dot = sum(left_counts[token] * right_counts[token] for token in common)
    left_norm = math.sqrt(sum(value * value for value in left_counts.values()))
    right_norm = math.sqrt(sum(value * value for value in right_counts.values()))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)


def node_label_map(example: Mapping[str, Any]) -> dict[str, str]:
    """Return node id -> label map for a unified GraphText example."""

    return {str(node.get("id")): str(node.get("label", "")) for node in example.get("nodes", [])}


def graph_source_text(example: Mapping[str, Any]) -> str:
    """Build a compact lexical representation of a graph example."""

    labels = node_label_map(example)
    parts: list[str] = []
    for edge in example.get("edges", []):
        subj_label = labels.get(str(edge.get("subj")), str(edge.get("subj", "")))
        obj_label = labels.get(str(edge.get("obj")), str(edge.get("obj", "")))
        pred = str(edge.get("pred", ""))
        parts.extend([subj_label, pred, obj_label])
    return " ".join(part for part in parts if part)


def score_example_graph_text_similarity(example: Mapping[str, Any]) -> dict[str, float]:
    """Score lexical graph-text similarity for one example."""

    graph_text = graph_source_text(example)
    text = str(example.get("text", ""))
    return {
        "token_jaccard": round(jaccard_similarity(graph_text, text), 6),
        "token_cosine": round(token_cosine_similarity(graph_text, text), 6),
    }


def score_corpus_graph_text_similarity(examples: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Compute corpus-level lexical graph-text similarity baselines."""

    example_scores = []
    for example in examples:
        scores = score_example_graph_text_similarity(example)
        example_scores.append(
            {
                "example_id": str(example.get("id", "")),
                "category": str(example.get("category", example.get("metadata", {}).get("category", ""))),
                **scores,
            }
        )
    count = len(example_scores)
    if count == 0:
        return {
            "examples": 0,
            "token_jaccard": 0.0,
            "token_cosine": 0.0,
            "example_scores": [],
        }
    return {
        "examples": count,
        "token_jaccard": round(sum(item["token_jaccard"] for item in example_scores) / count, 6),
        "token_cosine": round(sum(item["token_cosine"] for item in example_scores) / count, 6),
        "example_scores": example_scores,
    }
