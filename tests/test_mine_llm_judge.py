import json

from lemon_factor.mine_nodes_edges.judge_schema import FactRecoverabilityJudgment, validate_fact_judgment
from lemon_factor.mine_nodes_edges.llm_judge import build_judge_payloads, read_offline_judgment_fixture, render_judge_prompt
from lemon_factor.mine_nodes_edges.scoring import apply_fact_judgments, build_mine_style_report, score_mine_style_fact
from lemon_factor.reverse.reconstruct_graph import reconstruct_example_graph
from lemon_factor.schema.graphtext import Edge, GraphTextExample, Node, Split


def make_example():
    return GraphTextExample(
        id="ex1",
        dataset="toy",
        split=Split.dev,
        text="Alan Bean was born in Wheeler, Texas.",
        nodes=[Node(id="s", label="Alan Bean"), Node(id="o", label="Wheeler, Texas")],
        edges=[Edge(subj="s", pred="birthPlace", obj="o")],
    )


def make_score():
    example = make_example()
    record = reconstruct_example_graph(example, lexical_cues={"birthPlace": ["born in"]})
    return score_mine_style_fact(example, example.edges[0], 0, record, top_k=2, hops=1)


def test_fact_recoverability_schema_validates_fact_id():
    payload = {
        "fact_id": "ex1::edge-0",
        "recoverable": True,
        "confidence": 0.9,
        "evidence_nodes": ["s", "o"],
        "evidence_edges": ["birthPlace"],
        "reason": "The relation is explicit.",
    }
    judgment = validate_fact_judgment(expected_fact_id="ex1::edge-0", content=json.dumps(payload))
    assert judgment.recoverable is True
    assert judgment.confidence == 0.9


def test_render_judge_prompt_contains_fact_and_subgraph():
    prompt = render_judge_prompt(make_score())
    assert "Alan Bean" in prompt
    assert "Retrieved nodes" in prompt
    assert "birthPlace" in prompt
    assert "Do not use outside knowledge" in prompt


def test_build_judge_payload_uses_response_format_without_api_key():
    score = make_score()
    payloads = build_judge_payloads([score], models=["meta-llama/llama-3.1-70b-instruct"])
    assert payloads[0]["fact_id"] == "ex1::edge-0"
    assert "response_format" in payloads[0]["payload"]
    assert "Authorization" not in json.dumps(payloads[0])


def test_offline_judgment_fixture_and_apply_scores(tmp_path):
    fixture = tmp_path / "fixture.jsonl"
    fixture.write_text(
        json.dumps(
            {
                "fact_id": "ex1::edge-0",
                "content": json.dumps(
                    {
                        "fact_id": "ex1::edge-0",
                        "recoverable": False,
                        "confidence": 0.8,
                        "evidence_nodes": ["s"],
                        "evidence_edges": [],
                        "reason": "Object or relation is missing.",
                    }
                ),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    judgments, raw = read_offline_judgment_fixture(fixture)
    assert raw[0]["parsed"] is True
    score = make_score()
    judged = apply_fact_judgments([score], judgments, judge_mode="offline")
    assert judged[0].fact_recoverable is False
    assert judged[0].mine_style_score == 0.0
    assert judged[0].judge_confidence == 0.8


def test_llm_judged_report_tracks_parse_success_and_confidence():
    score = make_score()
    judgment = FactRecoverabilityJudgment(
        fact_id=score.fact_id,
        recoverable=True,
        confidence=0.75,
        evidence_nodes=["s", "o"],
        evidence_edges=["birthPlace"],
        reason="Supported.",
    )
    judged = apply_fact_judgments([score], {score.fact_id: judgment}, judge_mode="llm")
    report = build_mine_style_report(
        judged,
        examples=1,
        top_k=2,
        hops=1,
        judge_mode="llm",
        parse_success_rate=1.0,
        models=["m"],
    )
    assert report.judged_facts == 1
    assert report.mean_judge_confidence == 0.75
    assert report.metadata["llm_judge"] is True

import pytest
from pydantic import ValidationError

from lemon_factor.mine_nodes_edges.llm_judge import compact_retrieved_context


def test_fact_recoverability_rejects_long_reason():
    payload = {
        "fact_id": "ex1::edge-0",
        "recoverable": True,
        "confidence": 0.9,
        "evidence_nodes": ["s", "s", "o"],
        "evidence_edges": ["birthPlace"],
        "reason": " ".join(["word"] * 31),
    }
    with pytest.raises(ValidationError):
        FactRecoverabilityJudgment.model_validate(payload)


def test_fact_recoverability_deduplicates_evidence():
    judgment = FactRecoverabilityJudgment(
        fact_id="ex1::edge-0",
        recoverable=True,
        confidence=0.9,
        evidence_nodes=["s", "s", "o"],
        evidence_edges=["birthPlace", "birthPlace"],
        reason="Supported.",
    )
    assert judgment.evidence_nodes == ["s", "o"]
    assert judgment.evidence_edges == ["birthPlace"]


def test_compact_context_limits_nodes_and_edges():
    score = make_score()
    score.retrieved_nodes = [f"node-{i}" for i in range(10)]
    score.retrieved_edges = [{"subj": f"s{i}", "pred": "p", "obj": f"o{i}"} for i in range(10)]
    nodes, edges = compact_retrieved_context(score, max_nodes=3, max_edges=4)
    assert len(nodes) == 3
    assert len(edges) == 4


def test_build_judge_payload_uses_compact_options():
    score = make_score()
    payloads = build_judge_payloads(
        [score],
        models=["meta-llama/llama-3.1-70b-instruct"],
        compact_context=True,
        max_context_nodes=1,
        max_context_edges=1,
        reason_max_words=12,
        max_tokens=123,
    )
    record = payloads[0]
    assert "<= 12 words" in record["prompt"]
    assert record["payload"]["max_tokens"] == 123
    assert "repair_payload" in record


def test_llm_judged_report_tracks_subset_comparison():
    score = make_score()
    judgment = FactRecoverabilityJudgment(
        fact_id=score.fact_id,
        recoverable=not score.fact_recoverable,
        confidence=0.75,
        evidence_nodes=["s"],
        evidence_edges=[],
        reason="Unsupported relation.",
    )
    judged = apply_fact_judgments([score], {score.fact_id: judgment}, judge_mode="llm")
    report = build_mine_style_report(
        judged,
        examples=1,
        top_k=2,
        hops=1,
        judge_mode="llm",
        parse_success_rate=1.0,
        models=["m"],
        requested_judgments=1,
        failed_judgments=0,
        retry_attempts=1,
        retry_successes=1,
        deterministic_scores=[score],
    )
    assert report.requested_judgments == 1
    assert report.valid_judgments == 1
    assert report.failed_judgments == 0
    assert report.retry_attempts == 1
    assert report.retry_successes == 1
    assert report.judge_changed_count == 1
    assert report.judge_agreement_with_deterministic == 0.0
    assert report.deterministic_score_on_subset == score.mine_style_score


def test_llm_judged_report_separates_composite_and_fact_recoverability():
    score = make_score()
    judgment = FactRecoverabilityJudgment(
        fact_id=score.fact_id,
        recoverable=False,
        confidence=0.7,
        evidence_nodes=["s"],
        evidence_edges=[],
        reason="Relation missing.",
    )
    judged = apply_fact_judgments([score], {score.fact_id: judgment}, judge_mode="llm")
    report = build_mine_style_report(
        judged,
        examples=1,
        top_k=2,
        hops=1,
        judge_mode="llm",
        parse_success_rate=1.0,
        models=["m"],
        deterministic_scores=[score],
    )
    assert report.composite_node_edge_score == 1.0
    assert report.deterministic_fact_recoverability == 1.0
    assert report.llm_fact_recoverability == 0.0
    assert report.metadata["score_semantics"] == "binary_fact_recoverability"
