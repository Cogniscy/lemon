"""Optional LLM judge for MINE-style fact recoverability.

The live mode uses OpenRouter structured outputs. Offline fixtures and dry-run
payload generation require no API key and are used by tests.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from lemon_factor.llm.openrouter_client import build_chat_payload, call_openrouter, extract_message_content
from lemon_factor.llm.prompting import build_messages
from lemon_factor.mine_nodes_edges.judge_schema import (
    FactRecoverabilityJudgment,
    fact_recoverability_response_json_schema,
    validate_fact_judgment,
)
from lemon_factor.mine_nodes_edges.scoring import MineStyleFactScore

PROMPT_PATH = Path(__file__).parent / "prompts" / "judge_fact_recoverability.md"


def load_prompt_template(path: str | Path | None = None) -> str:
    return Path(path or PROMPT_PATH).read_text(encoding="utf-8")


def _truncate(value: str, max_chars: int) -> str:
    text = str(value)
    return text if len(text) <= max_chars else text[: max_chars - 1].rstrip() + "…"


def _edge_string(edge: dict[str, Any], *, max_chars: int = 80) -> str:
    subj = _truncate(edge.get("subj", ""), max_chars)
    pred = _truncate(edge.get("pred", ""), max_chars)
    obj = _truncate(edge.get("obj", ""), max_chars)
    return f"{subj} --{pred}--> {obj}"


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def compact_retrieved_context(
    score: MineStyleFactScore,
    *,
    max_nodes: int = 6,
    max_edges: int = 6,
    max_label_chars: int = 80,
) -> tuple[list[str], list[str]]:
    """Return compact retrieved node/edge lists for a judge prompt."""

    nodes = _dedupe([_truncate(node, max_label_chars) for node in score.retrieved_nodes])[:max_nodes]
    edge_strings = _dedupe([_edge_string(edge, max_chars=max_label_chars) for edge in score.retrieved_edges])[:max_edges]
    return nodes, edge_strings


def render_judge_prompt(
    score: MineStyleFactScore,
    template: str | None = None,
    *,
    compact_context: bool = False,
    max_context_nodes: int = 6,
    max_context_edges: int = 6,
    reason_max_words: int = 20,
    ultra_compact: bool = False,
) -> str:
    """Render one fact recoverability prompt."""

    template = template or load_prompt_template()
    if compact_context or ultra_compact:
        node_limit = min(max_context_nodes, 3) if ultra_compact else max_context_nodes
        edge_limit = min(max_context_edges, 3) if ultra_compact else max_context_edges
        retrieved_nodes, retrieved_edges = compact_retrieved_context(
            score,
            max_nodes=node_limit,
            max_edges=edge_limit,
        )
    else:
        retrieved_nodes = score.retrieved_nodes
        retrieved_edges = [_edge_string(edge) for edge in score.retrieved_edges]

    return template.format(
        fact_id=score.fact_id,
        fact_text=score.fact_text,
        retrieved_nodes=json.dumps(retrieved_nodes, ensure_ascii=False),
        retrieved_edges=json.dumps(retrieved_edges, ensure_ascii=False),
        reason_max_words=reason_max_words,
    )


def _payload_for_prompt(
    *,
    model: str,
    prompt: str,
    response_schema: dict[str, Any],
    temperature: float,
    max_tokens: int,
) -> dict[str, Any]:
    return build_chat_payload(
        model=model,
        messages=build_messages(prompt),
        response_schema=response_schema,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def build_judge_payloads(
    scores: list[MineStyleFactScore],
    *,
    models: list[str],
    limit: int | None = None,
    temperature: float = 0.0,
    compact_context: bool = False,
    max_context_nodes: int = 6,
    max_context_edges: int = 6,
    reason_max_words: int = 20,
    max_tokens: int = 250,
) -> list[dict[str, Any]]:
    """Build OpenRouter payload records for fact recoverability judgments."""

    response_schema = fact_recoverability_response_json_schema()
    selected = scores[:limit] if limit is not None else scores
    records: list[dict[str, Any]] = []
    for score in selected:
        prompt = render_judge_prompt(
            score,
            compact_context=compact_context,
            max_context_nodes=max_context_nodes,
            max_context_edges=max_context_edges,
            reason_max_words=reason_max_words,
        )
        repair_prompt = render_judge_prompt(
            score,
            compact_context=True,
            max_context_nodes=max_context_nodes,
            max_context_edges=max_context_edges,
            reason_max_words=min(reason_max_words, 15),
            ultra_compact=True,
        )
        for model in models:
            payload = _payload_for_prompt(
                model=model,
                prompt=prompt,
                response_schema=response_schema,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            repair_payload = _payload_for_prompt(
                model=model,
                prompt=repair_prompt,
                response_schema=response_schema,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            records.append(
                {
                    "model": model,
                    "fact_id": score.fact_id,
                    "example_id": score.example_id,
                    "edge_index": score.edge_index,
                    "prompt": prompt,
                    "repair_prompt": repair_prompt,
                    "payload": payload,
                    "repair_payload": repair_payload,
                }
            )
    return records


def read_offline_judgment_fixture(path: str | Path) -> tuple[dict[str, FactRecoverabilityJudgment], list[dict[str, Any]]]:
    """Read a JSONL fixture containing precomputed fact judgments.

    Supported lines:
    - {"fact_id": "...", "content": "{...json...}"}
    - direct judgment objects with fact_id/recoverable/confidence fields
    """

    judgments: dict[str, FactRecoverabilityJudgment] = {}
    raw_records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            fact_id = payload.get("fact_id")
            try:
                if "content" in payload:
                    content = payload["content"]
                    if fact_id is None:
                        parsed = json.loads(content)
                        fact_id = parsed["fact_id"]
                    judgment = validate_fact_judgment(expected_fact_id=fact_id, content=content)
                else:
                    judgment = FactRecoverabilityJudgment.model_validate(payload)
                    fact_id = judgment.fact_id
                judgments[fact_id] = judgment
                raw_records.append(
                    {
                        "fact_id": fact_id,
                        "model": payload.get("model", "offline-fixture"),
                        "raw_response": payload.get("content", payload),
                        "parsed": True,
                        "attempt": 1,
                        "metadata": {"line_no": line_no, "task": "mine_style_fact_recoverability"},
                    }
                )
            except Exception as exc:
                raw_records.append(
                    {
                        "fact_id": fact_id or f"fixture-line-{line_no}",
                        "model": payload.get("model", "offline-fixture"),
                        "raw_response": payload,
                        "parsed": False,
                        "attempt": 1,
                        "error": str(exc),
                        "metadata": {"line_no": line_no, "task": "mine_style_fact_recoverability"},
                    }
                )
    return judgments, raw_records


def _call_and_parse(record: dict[str, Any], *, use_repair_payload: bool = False) -> tuple[FactRecoverabilityJudgment, dict[str, Any]]:
    payload_key = "repair_payload" if use_repair_payload else "payload"
    response = call_openrouter(record[payload_key])
    content = extract_message_content(response)
    judgment = validate_fact_judgment(expected_fact_id=record["fact_id"], content=content)
    return judgment, response


def run_live_judgments(
    prompt_records: list[dict[str, Any]],
    *,
    retry_invalid_json: bool = False,
) -> tuple[dict[str, FactRecoverabilityJudgment], list[dict[str, Any]]]:
    """Call OpenRouter and parse fact recoverability judgments."""

    judgments: dict[str, FactRecoverabilityJudgment] = {}
    raw_records: list[dict[str, Any]] = []
    for index, record in enumerate(prompt_records, start=1):
        fact_id = record["fact_id"]
        model = record["model"]
        raw_id = f"openrouter-mine-judge-{index}"
        try:
            judgment, response = _call_and_parse(record)
            judgments[fact_id] = judgment
            raw_records.append(
                {
                    "fact_id": fact_id,
                    "model": model,
                    "raw_response": response,
                    "parsed": True,
                    "attempt": 1,
                    "metadata": {"raw_response_id": raw_id, "task": "mine_style_fact_recoverability"},
                }
            )
        except Exception as first_exc:
            if retry_invalid_json:
                try:
                    judgment, response = _call_and_parse(record, use_repair_payload=True)
                    judgments[fact_id] = judgment
                    raw_records.append(
                        {
                            "fact_id": fact_id,
                            "model": model,
                            "raw_response": response,
                            "parsed": True,
                            "attempt": 2,
                            "retry_success": True,
                            "first_error": str(first_exc),
                            "metadata": {"raw_response_id": raw_id, "task": "mine_style_fact_recoverability"},
                        }
                    )
                    continue
                except Exception as second_exc:
                    raw_records.append(
                        {
                            "fact_id": fact_id,
                            "model": model,
                            "raw_response": {},
                            "parsed": False,
                            "attempt": 2,
                            "retry_success": False,
                            "first_error": str(first_exc),
                            "error": str(second_exc),
                            "metadata": {"raw_response_id": raw_id, "task": "mine_style_fact_recoverability"},
                        }
                    )
                    continue
            raw_records.append(
                {
                    "fact_id": fact_id,
                    "model": model,
                    "raw_response": {},
                    "parsed": False,
                    "attempt": 1,
                    "error": str(first_exc),
                    "metadata": {"raw_response_id": raw_id, "task": "mine_style_fact_recoverability"},
                }
            )
    return judgments, raw_records


def write_jsonl(path: str | Path, records: list[Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for record in records:
            if hasattr(record, "model_dump"):
                payload = record.model_dump(mode="json")
            else:
                payload = record
            stream.write(json.dumps(payload, ensure_ascii=False) + "\n")
