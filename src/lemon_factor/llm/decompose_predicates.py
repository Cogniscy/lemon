"""Generate LLM-assisted predicate decomposition candidates.

The live mode is optional and requires OPENROUTER_API_KEY. Dry-run and offline
fixture modes are deterministic and are used by tests.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from lemon_factor.factors.decomposition import read_factor_schema
from lemon_factor.factors.inventory import FactorInventory, PredicateInventoryItem
from lemon_factor.llm.openrouter_client import (
    build_chat_payload,
    call_openrouter,
    extract_message_content,
)
from lemon_factor.llm.prompting import build_messages, render_decomposition_prompt
from lemon_factor.llm.schema import (
    LLMDecompositionRecord,
    LLMPredicateDecomposition,
    LLMRawResponseRecord,
    decomposition_response_json_schema,
    validate_against_factor_schema,
    write_jsonl,
)


def read_model_config(path: str | Path) -> list[str]:
    """Read a tiny YAML-like model config without depending on PyYAML."""

    models: list[str] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped == "models:":
            continue
        if stripped.startswith("-"):
            model = stripped[1:].strip().strip('"').strip("'")
            if model:
                models.append(model)
    return models


def top_predicate_items(inventory: FactorInventory, *, limit: int) -> list[PredicateInventoryItem]:
    """Return top predicates by count."""

    return sorted(inventory.predicates.values(), key=lambda item: (-item.count, item.predicate))[:limit]


def build_prompt_payloads(
    inventory: FactorInventory,
    factor_schema_path: str | Path,
    *,
    models: list[str],
    limit: int,
    temperature: float = 0.0,
) -> list[dict[str, Any]]:
    """Build prompt/payload records for dry-run or live calls."""

    factors = read_factor_schema(factor_schema_path)
    response_schema = decomposition_response_json_schema()
    records: list[dict[str, Any]] = []
    for item in top_predicate_items(inventory, limit=limit):
        prompt = render_decomposition_prompt(item, factors)
        messages = build_messages(prompt)
        for model in models:
            payload = build_chat_payload(
                model=model,
                messages=messages,
                response_schema=response_schema,
                temperature=temperature,
            )
            records.append(
                {
                    "model": model,
                    "predicate": item.predicate,
                    "prompt": prompt,
                    "payload": payload,
                }
            )
    return records


def parse_llm_content(
    *,
    model: str,
    predicate: str,
    content: str,
    factors_path: str | Path,
    raw_response_id: str | None = None,
) -> LLMDecompositionRecord:
    """Parse and schema-check one LLM content string."""

    candidate = LLMPredicateDecomposition.model_validate_json(content)
    if candidate.predicate != predicate:
        raise ValueError(f"Expected predicate {predicate!r}, got {candidate.predicate!r}")
    factors = read_factor_schema(factors_path)
    validate_against_factor_schema(candidate, factors)
    return LLMDecompositionRecord(
        model=model,
        predicate=predicate,
        decomposition=candidate,
        raw_response_id=raw_response_id,
    )


def read_offline_fixture(
    path: str | Path,
    *,
    factors_path: str | Path,
) -> tuple[list[LLMDecompositionRecord], list[LLMRawResponseRecord]]:
    """Read model responses from a JSONL fixture and validate them."""

    candidates: list[LLMDecompositionRecord] = []
    raw_records: list[LLMRawResponseRecord] = []
    with Path(path).open("r", encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            model = payload["model"]
            predicate = payload["predicate"]
            content = payload.get("content")
            raw_response = payload.get("raw_response", content)
            raw_id = payload.get("raw_response_id") or f"fixture-{line_no}"
            try:
                record = parse_llm_content(
                    model=model,
                    predicate=predicate,
                    content=content,
                    factors_path=factors_path,
                    raw_response_id=raw_id,
                )
                candidates.append(record)
                raw_records.append(
                    LLMRawResponseRecord(
                        model=model,
                        predicate=predicate,
                        raw_response=raw_response,
                        parsed=True,
                    )
                )
            except Exception as exc:
                raw_records.append(
                    LLMRawResponseRecord(
                        model=model,
                        predicate=predicate,
                        raw_response=raw_response,
                        parsed=False,
                        error=str(exc),
                    )
                )
    return candidates, raw_records


def run_live_generation(
    prompt_records: list[dict[str, Any]],
    *,
    factors_path: str | Path,
) -> tuple[list[LLMDecompositionRecord], list[LLMRawResponseRecord]]:
    """Call OpenRouter for prompt records and validate the outputs."""

    candidates: list[LLMDecompositionRecord] = []
    raw_records: list[LLMRawResponseRecord] = []
    for index, prompt_record in enumerate(prompt_records, start=1):
        model = prompt_record["model"]
        predicate = prompt_record["predicate"]
        raw_id = f"openrouter-{index}"
        try:
            response = call_openrouter(prompt_record["payload"])
            content = extract_message_content(response)
            candidate = parse_llm_content(
                model=model,
                predicate=predicate,
                content=content,
                factors_path=factors_path,
                raw_response_id=raw_id,
            )
            candidates.append(candidate)
            raw_records.append(
                LLMRawResponseRecord(
                    model=model,
                    predicate=predicate,
                    raw_response=response,
                    parsed=True,
                    metadata={"raw_response_id": raw_id},
                )
            )
        except Exception as exc:
            raw_records.append(
                LLMRawResponseRecord(
                    model=model,
                    predicate=predicate,
                    raw_response={},
                    parsed=False,
                    error=str(exc),
                    metadata={"raw_response_id": raw_id},
                )
            )
    return candidates, raw_records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inventory", help="Factor inventory JSON from lemon-03")
    parser.add_argument("--factor-schema", required=True, help="Seed factor schema JSON")
    parser.add_argument("--models", help="YAML-like model config")
    parser.add_argument("--model", action="append", help="Single model id; may be repeated")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--out", default="data/interim/llm_predicate_decomposition_candidates.jsonl")
    parser.add_argument("--raw-out", default="data/interim/llm_raw_responses.jsonl")
    parser.add_argument("--prompts-out", default="data/interim/llm_predicate_decomposition_prompts.jsonl")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--offline-fixture")
    return parser.parse_args()


def _resolve_models(args: argparse.Namespace) -> list[str]:
    models: list[str] = []
    if args.models:
        models.extend(read_model_config(args.models))
    if args.model:
        models.extend(args.model)
    if not models:
        models = ["openai/gpt-4o-mini"]
    return list(dict.fromkeys(models))


def main() -> None:
    args = parse_args()
    inventory = FactorInventory.from_json_file(args.inventory)
    models = _resolve_models(args)

    if args.offline_fixture:
        candidates, raw_records = read_offline_fixture(
            args.offline_fixture, factors_path=args.factor_schema
        )
        write_jsonl(args.out, candidates)
        write_jsonl(args.raw_out, raw_records)
        print(json.dumps({"out": args.out, "raw_out": args.raw_out}, indent=2))
        return

    prompt_records = build_prompt_payloads(
        inventory,
        args.factor_schema,
        models=models,
        limit=args.limit,
    )

    if args.dry_run:
        write_jsonl(args.prompts_out, prompt_records)
        print(json.dumps({"prompts": args.prompts_out, "records": len(prompt_records)}, indent=2))
        return

    candidates, raw_records = run_live_generation(prompt_records, factors_path=args.factor_schema)
    write_jsonl(args.out, candidates)
    write_jsonl(args.raw_out, raw_records)
    print(json.dumps({"out": args.out, "raw_out": args.raw_out}, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
