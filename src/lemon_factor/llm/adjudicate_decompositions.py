"""Create a synthetic adjudicated predicate-decomposition reference with a strong LLM.

This is an optional bridge step used when no human expert is available. The
resulting reference must be treated as synthetic, not as human gold.
"""

from __future__ import annotations

import argparse
import csv
import json
import warnings
from collections import defaultdict
from pathlib import Path
from typing import Any

from lemon_factor.factors.decomposition import (
    PredicateDecomposition,
    PredicateDecompositionSet,
    read_factor_schema,
)
from lemon_factor.factors.disagreement import classify_disagreement
from lemon_factor.factors.inventory import FactorInventory, PredicateInventoryItem
from lemon_factor.llm.adjudication_schema import (
    LLMAdjudicationDecision,
    adjudication_response_json_schema,
    validate_adjudication_against_schema,
)
from lemon_factor.llm.decompose_predicates import read_model_config
from lemon_factor.llm.openrouter_client import build_chat_payload, call_openrouter, extract_message_content
from lemon_factor.llm.prompting import build_messages, factor_schema_brief, predicate_context_brief
from lemon_factor.llm.schema import LLMRawResponseRecord, read_llm_records, write_jsonl

PROMPT_PATH = Path(__file__).parent / "prompts" / "adjudicate_decomposition.md"


def load_prompt_template(path: str | Path | None = None) -> str:
    return Path(path or PROMPT_PATH).read_text(encoding="utf-8")


def _component_string(component: Any) -> str:
    rationale = f" // {component.rationale}" if getattr(component, "rationale", None) else ""
    return f"{component.factor}:{component.role}:{component.weight:.3f}{rationale}"


def _confidence_string(value: float | None) -> str:
    return "NA" if value is None else f"{value:.2f}"


def decomposition_brief(decomposition: PredicateDecomposition) -> str:
    components = "; ".join(_component_string(component) for component in decomposition.components)
    return (
        f"predicate={decomposition.predicate}; source={decomposition.source}; "
        f"confidence={_confidence_string(decomposition.confidence)}; components=[{components}]"
    )


def llm_candidates_brief(candidates: list[Any]) -> str:
    if not candidates:
        return "No LLM candidates available."
    lines: list[str] = []
    for candidate in candidates:
        components = "; ".join(
            _component_string(component) for component in candidate.decomposition.components
        )
        lines.append(
            f"- model={candidate.model}; confidence={candidate.decomposition.confidence:.2f}; "
            f"components=[{components}]; rationale={candidate.decomposition.rationale}"
        )
    return "\n".join(lines)


def render_adjudication_prompt(
    *,
    predicate_item: PredicateInventoryItem | None,
    seed: PredicateDecomposition,
    llm_candidates: list[Any],
    factors: list[Any],
    template: str | None = None,
) -> str:
    """Render one synthetic adjudication prompt."""

    if predicate_item is None:
        predicate_context = f"Predicate: {seed.predicate}\nNo inventory context available."
    else:
        predicate_context = predicate_context_brief(predicate_item)
    template = template or load_prompt_template()
    return template.format(
        predicate_context=predicate_context,
        seed_decomposition=decomposition_brief(seed),
        llm_candidates=llm_candidates_brief(llm_candidates),
        factor_schema=factor_schema_brief(factors),
    )


def group_llm_records_by_predicate(path: str | Path) -> dict[str, list[Any]]:
    grouped: dict[str, list[Any]] = defaultdict(list)
    for record in read_llm_records(path):
        grouped[record.predicate].append(record)
    return dict(grouped)


def _top_seed_predicates(reference: PredicateDecompositionSet, *, limit: int) -> list[str]:
    return list(reference.decompositions.keys())[:limit]


def build_adjudication_payloads(
    *,
    seed_set: PredicateDecompositionSet,
    llm_by_predicate: dict[str, list[Any]],
    inventory: FactorInventory | None,
    models: list[str],
    limit: int,
    temperature: float = 0.0,
) -> list[dict[str, Any]]:
    """Build prompt/payload records for dry-run or live synthetic adjudication."""

    response_schema = adjudication_response_json_schema()
    records: list[dict[str, Any]] = []
    for predicate in _top_seed_predicates(seed_set, limit=limit):
        seed = seed_set.decompositions[predicate]
        predicate_item = inventory.predicates.get(predicate) if inventory else None
        prompt = render_adjudication_prompt(
            predicate_item=predicate_item,
            seed=seed,
            llm_candidates=llm_by_predicate.get(predicate, []),
            factors=seed_set.factors,
        )
        for model in models:
            payload = build_chat_payload(
                model=model,
                messages=build_messages(prompt),
                response_schema=response_schema,
                temperature=temperature,
            )
            records.append({"model": model, "predicate": predicate, "prompt": prompt, "payload": payload})
    return records


def parse_adjudication_content(
    *,
    model: str,
    predicate: str,
    content: str,
    seed_set: PredicateDecompositionSet,
    raw_response_id: str | None = None,
    disagreement_type: str | None = None,
) -> tuple[PredicateDecomposition, LLMRawResponseRecord]:
    decision = LLMAdjudicationDecision.model_validate_json(content)
    if decision.predicate != predicate:
        raise ValueError(f"Expected predicate {predicate!r}, got {decision.predicate!r}")
    decomposition = validate_adjudication_against_schema(
        decision,
        seed_set.factors,
        evidence={
            "adjudicator_model": model,
            "raw_response_id": raw_response_id,
            "disagreement_type": disagreement_type,
            "synthetic": True,
        },
    )
    raw = LLMRawResponseRecord(
        model=model,
        predicate=predicate,
        raw_response=content,
        parsed=True,
        metadata={"raw_response_id": raw_response_id, "task": "synthetic_adjudication"},
    )
    return decomposition, raw


def read_offline_adjudication_fixture(
    path: str | Path,
    *,
    seed_set: PredicateDecompositionSet,
) -> tuple[dict[str, PredicateDecomposition], list[LLMRawResponseRecord]]:
    decompositions: dict[str, PredicateDecomposition] = {}
    raw_records: list[LLMRawResponseRecord] = []
    with Path(path).open("r", encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            model = payload.get("model", "offline-adjudicator")
            predicate = payload["predicate"]
            content = payload.get("content")
            raw_id = payload.get("raw_response_id") or f"fixture-adjudication-{line_no}"
            try:
                decomposition, raw = parse_adjudication_content(
                    model=model,
                    predicate=predicate,
                    content=content,
                    seed_set=seed_set,
                    raw_response_id=raw_id,
                    disagreement_type=payload.get("disagreement_type"),
                )
                decompositions[predicate] = decomposition
                raw_records.append(raw)
            except Exception as exc:
                raw_records.append(
                    LLMRawResponseRecord(
                        model=model,
                        predicate=predicate,
                        raw_response=payload.get("raw_response", content),
                        parsed=False,
                        error=str(exc),
                        metadata={"raw_response_id": raw_id, "task": "synthetic_adjudication"},
                    )
                )
    return decompositions, raw_records


def synthetic_seed_fallback(
    *,
    seed_set: PredicateDecompositionSet,
    llm_by_predicate: dict[str, list[Any]],
    limit: int,
) -> tuple[dict[str, PredicateDecomposition], list[LLMRawResponseRecord]]:
    """Deterministic no-network fallback used for dry integration checks.

    It does not emulate a real LLM. It marks seed decompositions as synthetic
    placeholders so that downstream code can be tested without API calls.
    """

    decompositions: dict[str, PredicateDecomposition] = {}
    raw_records: list[LLMRawResponseRecord] = []
    for predicate in _top_seed_predicates(seed_set, limit=limit):
        seed = seed_set.decompositions[predicate]
        disagreement = classify_disagreement(seed, llm_by_predicate.get(predicate, []))
        decomposition = PredicateDecomposition(
            predicate=predicate,
            components=seed.components,
            source="synthetic_adjudication",
            confidence=None,
            evidence={
                "adjudication_status": "accepted_seed",
                "selected_sources": ["seed"],
                "rationale": "Deterministic fallback used without an adjudicator LLM.",
                "synthetic": True,
                "fallback": True,
                "confidence_missing": True,
                "disagreement_type": disagreement,
            },
        )
        decompositions[predicate] = decomposition
        raw_records.append(
            LLMRawResponseRecord(
                model="deterministic-seed-fallback",
                predicate=predicate,
                raw_response={"source": "seed", "disagreement_type": disagreement},
                parsed=True,
                metadata={"task": "synthetic_adjudication", "fallback": True},
            )
        )
    return decompositions, raw_records


def run_live_adjudication(
    prompt_records: list[dict[str, Any]],
    *,
    seed_set: PredicateDecompositionSet,
    llm_by_predicate: dict[str, list[Any]],
) -> tuple[dict[str, PredicateDecomposition], list[LLMRawResponseRecord]]:
    decompositions: dict[str, PredicateDecomposition] = {}
    raw_records: list[LLMRawResponseRecord] = []
    for index, prompt_record in enumerate(prompt_records, start=1):
        model = prompt_record["model"]
        predicate = prompt_record["predicate"]
        raw_id = f"openrouter-adjudication-{index}"
        disagreement = classify_disagreement(
            seed_set.decompositions[predicate], llm_by_predicate.get(predicate, [])
        )
        try:
            response = call_openrouter(prompt_record["payload"])
            content = extract_message_content(response)
            decomposition, raw = parse_adjudication_content(
                model=model,
                predicate=predicate,
                content=content,
                seed_set=seed_set,
                raw_response_id=raw_id,
                disagreement_type=disagreement,
            )
            decompositions[predicate] = decomposition
            raw.raw_response = response
            raw_records.append(raw)
        except Exception as exc:
            raw_records.append(
                LLMRawResponseRecord(
                    model=model,
                    predicate=predicate,
                    raw_response={},
                    parsed=False,
                    error=str(exc),
                    metadata={"raw_response_id": raw_id, "task": "synthetic_adjudication"},
                )
            )
    return decompositions, raw_records


def write_review_csv(
    *,
    path: str | Path,
    seed_set: PredicateDecompositionSet,
    adjudicated: dict[str, PredicateDecomposition],
    llm_by_predicate: dict[str, list[Any]],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "predicate",
        "disagreement_type",
        "seed_decomposition",
        "llm_candidates",
        "synthetic_final_decomposition",
        "synthetic_status",
        "synthetic_confidence",
        "human_review_status",
        "human_notes",
    ]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for predicate, decomposition in adjudicated.items():
            seed = seed_set.decompositions[predicate]
            llm_candidates = llm_by_predicate.get(predicate, [])
            writer.writerow(
                {
                    "predicate": predicate,
                    "disagreement_type": classify_disagreement(seed, llm_candidates),
                    "seed_decomposition": decomposition_brief(seed),
                    "llm_candidates": llm_candidates_brief(llm_candidates),
                    "synthetic_final_decomposition": decomposition_brief(decomposition),
                    "synthetic_status": decomposition.evidence.get("adjudication_status", ""),
                    "synthetic_confidence": "" if decomposition.confidence is None else f"{decomposition.confidence:.2f}",
                    "human_review_status": "",
                    "human_notes": "",
                }
            )


def _llm_candidate_coverage_stats(
    *,
    adjudicated_predicates: list[str],
    llm_by_predicate: dict[str, list[Any]],
) -> dict[str, Any]:
    predicates_with_llm = [predicate for predicate in adjudicated_predicates if llm_by_predicate.get(predicate)]
    predicates_without_llm = [
        predicate for predicate in adjudicated_predicates if not llm_by_predicate.get(predicate)
    ]
    total = len(adjudicated_predicates)
    return {
        "llm_candidate_coverage": round(len(predicates_with_llm) / total, 6) if total else 0.0,
        "predicates_with_llm_candidates": len(predicates_with_llm),
        "predicates_without_llm_candidates": len(predicates_without_llm),
        "predicates_without_llm_candidate_ids": predicates_without_llm,
        "llm_candidate_predicate_count": len(llm_by_predicate),
    }


def write_adjudication_stats(
    *,
    path: str | Path,
    seed_set: PredicateDecompositionSet,
    adjudicated: dict[str, PredicateDecomposition],
    llm_by_predicate: dict[str, list[Any]],
    adjudication_limit: int | None = None,
) -> dict[str, Any]:
    from collections import Counter

    disagreement_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    confidence_values: list[float] = []
    missing_confidence_count = 0
    fallback_count = 0
    for predicate, decomposition in adjudicated.items():
        disagreement_counts[
            classify_disagreement(seed_set.decompositions[predicate], llm_by_predicate.get(predicate, []))
        ] += 1
        status_counts[str(decomposition.evidence.get("adjudication_status", "unknown"))] += 1
        if decomposition.confidence is None:
            missing_confidence_count += 1
        else:
            confidence_values.append(decomposition.confidence)
        if decomposition.evidence.get("fallback"):
            fallback_count += 1

    adjudicated_predicates = list(adjudicated)
    coverage = _llm_candidate_coverage_stats(
        adjudicated_predicates=adjudicated_predicates,
        llm_by_predicate=llm_by_predicate,
    )
    payload = {
        "items": len(adjudicated),
        "synthetic": True,
        "adjudication_limit": adjudication_limit,
        **coverage,
        "missing_confidence_count": missing_confidence_count,
        "mean_confidence": (
            round(sum(confidence_values) / len(confidence_values), 6) if confidence_values else None
        ),
        "fallback_count": fallback_count,
        "disagreement_counts": dict(sorted(disagreement_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def _markdown_value(value: Any) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def write_markdown_stats(stats: dict[str, Any], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "| Metric | Value |",
        "|---|---:|",
        f"| Items | {stats['items']} |",
        f"| Synthetic reference | {stats['synthetic']} |",
        f"| LLM candidate coverage | {_markdown_value(stats.get('llm_candidate_coverage'))} |",
        f"| Predicates with LLM candidates | {stats.get('predicates_with_llm_candidates', 0)} |",
        f"| Predicates without LLM candidates | {stats.get('predicates_without_llm_candidates', 0)} |",
        f"| Mean confidence | {_markdown_value(stats.get('mean_confidence'))} |",
        f"| Missing confidence count | {stats.get('missing_confidence_count', 0)} |",
        f"| Seed fallback count | {stats.get('fallback_count', 0)} |",
    ]
    for label, value in stats["disagreement_counts"].items():
        lines.append(f"| disagreement:{label} | {value} |")
    for label, value in stats["status_counts"].items():
        lines.append(f"| status:{label} | {value} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", required=True, help="Seed predicate decompositions JSON")
    parser.add_argument("--llm", required=True, help="LLM candidate decompositions JSONL")
    parser.add_argument("--inventory", help="WebNLG factor inventory JSON")
    parser.add_argument("--models", help="YAML-like adjudicator model config")
    parser.add_argument("--model", action="append", help="Single adjudicator model id; may be repeated")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--out", default="data/interim/webnlg_predicate_decompositions_synthetic_adjudicated.json")
    parser.add_argument("--raw-out", default="data/interim/llm_synthetic_adjudication_raw.jsonl")
    parser.add_argument("--review-out", default="data/annotation/synthetic_adjudication_review.csv")
    parser.add_argument("--stats-out", default="data/reports/synthetic_adjudication_stats.json")
    parser.add_argument("--table", default="paper/tables/table_synthetic_adjudication_stats.md")
    parser.add_argument("--prompts-out", default="data/interim/llm_synthetic_adjudication_prompts.jsonl")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--offline-fixture")
    parser.add_argument("--seed-fallback", action="store_true")
    return parser.parse_args()


def _resolve_models(args: argparse.Namespace) -> list[str]:
    models: list[str] = []
    if args.models:
        models.extend(read_model_config(args.models))
    if args.model:
        models.extend(args.model)
    if not models:
        models = ["meta-llama/llama-3.1-70b-instruct"]
    return list(dict.fromkeys(models))


def main() -> None:
    args = parse_args()
    seed_set = PredicateDecompositionSet.from_json_file(args.seed)
    llm_by_predicate = group_llm_records_by_predicate(args.llm)
    inventory = FactorInventory.from_json_file(args.inventory) if args.inventory else None
    models = _resolve_models(args)

    prompt_records = build_adjudication_payloads(
        seed_set=seed_set,
        llm_by_predicate=llm_by_predicate,
        inventory=inventory,
        models=models,
        limit=args.limit,
    )

    adjudicated_predicates_planned = _top_seed_predicates(seed_set, limit=args.limit)
    predicates_without_llm = [
        predicate for predicate in adjudicated_predicates_planned if not llm_by_predicate.get(predicate)
    ]
    if predicates_without_llm:
        warnings.warn(
            "Synthetic adjudication includes predicates without LLM candidates; "
            "results will include seed-only or weakly supported cases.",
            RuntimeWarning,
        )

    if args.dry_run:
        write_jsonl(args.prompts_out, prompt_records)
        print(json.dumps({"prompts": args.prompts_out, "records": len(prompt_records)}, indent=2))
        return

    if args.offline_fixture:
        adjudicated, raw_records = read_offline_adjudication_fixture(args.offline_fixture, seed_set=seed_set)
    elif args.seed_fallback:
        adjudicated, raw_records = synthetic_seed_fallback(
            seed_set=seed_set, llm_by_predicate=llm_by_predicate, limit=args.limit
        )
    else:
        adjudicated, raw_records = run_live_adjudication(
            prompt_records, seed_set=seed_set, llm_by_predicate=llm_by_predicate
        )

    output_set = PredicateDecompositionSet(
        schema_version="synthetic-adjudicated-v1",
        factors=seed_set.factors,
        decompositions=adjudicated,
        metadata={
            "synthetic": True,
            "warning": "Synthetic LLM adjudication; not a human expert gold reference.",
            "adjudicator_models": models,
        },
    )
    output_set.to_json_file(args.out)
    write_jsonl(args.raw_out, raw_records)
    write_review_csv(
        path=args.review_out,
        seed_set=seed_set,
        adjudicated=adjudicated,
        llm_by_predicate=llm_by_predicate,
    )
    stats = write_adjudication_stats(
        path=args.stats_out,
        seed_set=seed_set,
        adjudicated=adjudicated,
        llm_by_predicate=llm_by_predicate,
        adjudication_limit=args.limit,
    )
    write_markdown_stats(stats, args.table)
    print(
        json.dumps(
            {
                "out": args.out,
                "raw_out": args.raw_out,
                "review": args.review_out,
                "stats": args.stats_out,
                "table": args.table,
            },
            indent=2,
        )
    )


if __name__ == "__main__":  # pragma: no cover
    main()
