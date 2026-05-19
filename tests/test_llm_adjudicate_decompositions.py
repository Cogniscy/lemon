import json

from lemon_factor.factors.decomposition import FactorComponent, PredicateDecomposition, PredicateDecompositionSet
from lemon_factor.factors.seed_schema import build_default_factor_schema
from lemon_factor.llm.adjudicate_decompositions import (
    build_adjudication_payloads,
    read_offline_adjudication_fixture,
    synthetic_seed_fallback,
    write_review_csv,
    write_adjudication_stats,
    write_markdown_stats,
)
from lemon_factor.llm.schema import LLMDecompositionRecord, LLMPredicateDecomposition, LLMFactorComponent


def make_seed_set() -> PredicateDecompositionSet:
    factors = build_default_factor_schema()
    return PredicateDecompositionSet(
        factors=factors,
        decompositions={
            "birthPlace": PredicateDecomposition(
                predicate="birthPlace",
                components=[
                    FactorComponent(factor="biographical_relation", role="predicate_meaning", weight=0.4),
                    FactorComponent(factor="person", role="subject_domain", weight=0.2),
                    FactorComponent(factor="place", role="object_domain", weight=0.4),
                ],
            )
        },
    )


def make_llm_record() -> LLMDecompositionRecord:
    return LLMDecompositionRecord(
        model="m",
        predicate="birthPlace",
        decomposition=LLMPredicateDecomposition(
            predicate="birthPlace",
            components=[
                LLMFactorComponent(factor="biographical_relation", role="predicate_meaning", weight=0.4),
                LLMFactorComponent(factor="person", role="subject_domain", weight=0.2),
                LLMFactorComponent(factor="place", role="object_domain", weight=0.4),
            ],
        ),
    )


def test_build_adjudication_payloads_dry_records():
    seed_set = make_seed_set()
    payloads = build_adjudication_payloads(
        seed_set=seed_set,
        llm_by_predicate={"birthPlace": [make_llm_record()]},
        inventory=None,
        models=["adjudicator-model"],
        limit=1,
    )
    assert len(payloads) == 1
    assert payloads[0]["predicate"] == "birthPlace"
    assert "response_format" in payloads[0]["payload"]
    assert "OPENROUTER_API_KEY" not in json.dumps(payloads[0])


def test_read_offline_adjudication_fixture(tmp_path):
    seed_set = make_seed_set()
    fixture = tmp_path / "fixture.jsonl"
    content = json.dumps(
        {
            "predicate": "birthPlace",
            "status": "accepted_seed",
            "components": [
                {"factor": "biographical_relation", "role": "predicate_meaning", "weight": 0.4},
                {"factor": "person", "role": "subject_domain", "weight": 0.2},
                {"factor": "place", "role": "object_domain", "weight": 0.4},
            ],
            "confidence": 0.9,
            "selected_sources": ["seed"],
            "rationale": "Seed is correct.",
        }
    )
    fixture.write_text(json.dumps({"model": "judge", "predicate": "birthPlace", "content": content}) + "\n")
    decompositions, raw = read_offline_adjudication_fixture(fixture, seed_set=seed_set)
    assert decompositions["birthPlace"].source == "synthetic_adjudication"
    assert decompositions["birthPlace"].confidence == 0.9
    assert raw[0].parsed is True


def test_synthetic_seed_fallback_and_review_csv(tmp_path):
    seed_set = make_seed_set()
    adjudicated, raw = synthetic_seed_fallback(
        seed_set=seed_set,
        llm_by_predicate={"birthPlace": [make_llm_record()]},
        limit=1,
    )
    assert adjudicated["birthPlace"].source == "synthetic_adjudication"
    assert adjudicated["birthPlace"].evidence["fallback"] is True
    assert raw[0].model == "deterministic-seed-fallback"

    out = tmp_path / "review.csv"
    write_review_csv(
        path=out,
        seed_set=seed_set,
        adjudicated=adjudicated,
        llm_by_predicate={"birthPlace": [make_llm_record()]},
    )
    text = out.read_text()
    assert "human_review_status" in text
    assert "birthPlace" in text


def test_adjudication_stats_include_candidate_coverage_and_confidence(tmp_path):
    seed_set = make_seed_set()
    adjudicated, _ = synthetic_seed_fallback(
        seed_set=seed_set,
        llm_by_predicate={},
        limit=1,
    )
    out = tmp_path / "stats.json"
    stats = write_adjudication_stats(
        path=out,
        seed_set=seed_set,
        adjudicated=adjudicated,
        llm_by_predicate={},
        adjudication_limit=1,
    )
    assert stats["llm_candidate_coverage"] == 0.0
    assert stats["predicates_without_llm_candidates"] == 1
    assert stats["missing_confidence_count"] == 1
    assert stats["mean_confidence"] is None

    table = tmp_path / "stats.md"
    write_markdown_stats(stats, table)
    text = table.read_text()
    assert "LLM candidate coverage" in text
    assert "Missing confidence count" in text


def test_synthetic_seed_fallback_uses_missing_confidence_marker():
    seed_set = make_seed_set()
    adjudicated, _ = synthetic_seed_fallback(
        seed_set=seed_set,
        llm_by_predicate={"birthPlace": [make_llm_record()]},
        limit=1,
    )
    decomposition = adjudicated["birthPlace"]
    assert decomposition.confidence is None
    assert decomposition.evidence["confidence_missing"] is True
