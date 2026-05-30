"""Prompt construction for MINE-1-compatible LLM judging."""

from __future__ import annotations

from typing import Any

from .core import retrieval_context

MINE_JUDGE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "item_id": {"type": "string"},
        "recoverable": {"type": "boolean"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "evidence": {"type": "string"},
    },
    "required": ["item_id", "recoverable", "confidence", "evidence"],
}

SYSTEM_PROMPT = (
    "You are evaluating whether a reference fact is recoverable from a knowledge-graph subgraph. "
    "Use only the nodes and edges in the provided subgraph. Do not use outside knowledge. "
    "Return JSON only."
)


def build_user_prompt(context: dict[str, Any]) -> str:
    edges = context.get("subgraph_edges") or []
    edge_lines = [f"- {edge.get('subject')} --{edge.get('predicate')}--> {edge.get('object')}" for edge in edges]
    if not edge_lines:
        edge_lines = ["- <empty subgraph>"]
    return "\n".join(
        [
            f"Item ID: {context.get('item_id')}",
            f"Reference fact: {context.get('fact')}",
            "",
            "Retrieved subgraph edges:",
            *edge_lines,
            "",
            "Question: Can the reference fact be inferred from the retrieved subgraph alone?",
            "Return exactly this JSON shape:",
            '{"item_id":"...","recoverable":true|false,"confidence":0.0-1.0,"evidence":"short phrase"}',
        ]
    )


def build_prompt_payload(item: dict[str, Any], *, model: str, judge_id: str, top_k: int = 3, hops: int = 2) -> dict[str, Any]:
    context = retrieval_context(item, top_k=top_k, hops=hops)
    return {
        "item_id": context["item_id"],
        "dataset": context.get("dataset"),
        "variant": context.get("variant"),
        "judge_id": judge_id,
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(context)},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "mine_recoverability_judgment",
                "strict": True,
                "schema": MINE_JUDGE_SCHEMA,
            },
        },
        "retrieval_context": context,
    }
