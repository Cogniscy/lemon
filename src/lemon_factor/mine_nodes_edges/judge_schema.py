"""Schemas for LLM-judged MINE-style fact recoverability."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

DEFAULT_REASON_MAX_WORDS = 30
MAX_REASON_CHARS = 240
MAX_EVIDENCE_ITEMS = 5


def _dedupe_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        item = str(value).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def word_count(text: str) -> int:
    return len([part for part in text.strip().split() if part])


class FactRecoverabilityJudgment(BaseModel):
    """Binary judgment for whether a gold fact is recoverable from a subgraph."""

    fact_id: str = Field(min_length=1)
    recoverable: bool
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence_nodes: list[str] = Field(default_factory=list, max_length=MAX_EVIDENCE_ITEMS)
    evidence_edges: list[str] = Field(default_factory=list, max_length=MAX_EVIDENCE_ITEMS)
    reason: str = Field(default="", max_length=MAX_REASON_CHARS)

    @field_validator("evidence_nodes", "evidence_edges", mode="after")
    @classmethod
    def deduplicate_evidence(cls, values: list[str]) -> list[str]:
        return _dedupe_keep_order(values)

    @field_validator("reason", mode="after")
    @classmethod
    def reason_is_compact(cls, value: str) -> str:
        reason = value.strip()
        if word_count(reason) > DEFAULT_REASON_MAX_WORDS:
            raise ValueError(f"reason must contain at most {DEFAULT_REASON_MAX_WORDS} words")
        return reason


def fact_recoverability_response_json_schema() -> dict:
    """Return a JSON Schema suitable for OpenRouter structured outputs."""

    return FactRecoverabilityJudgment.model_json_schema()


def validate_fact_judgment(*, expected_fact_id: str, content: str) -> FactRecoverabilityJudgment:
    """Parse and validate one LLM judgment content string."""

    judgment = FactRecoverabilityJudgment.model_validate_json(content)
    if judgment.fact_id != expected_fact_id:
        raise ValueError(f"Expected fact_id {expected_fact_id!r}, got {judgment.fact_id!r}")
    return judgment
