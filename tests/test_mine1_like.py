import json
from pathlib import Path

from lemon_factor.baselines.mine1_like.core import apply_controlled_perturbation, mine1_score, score_item
from lemon_factor.baselines.mine1_like.prepare import prepare
from lemon_factor.baselines.triple_f1 import run as run_triple_f1


def toy_record(variant="edge_deletion"):
    return {
        "id": f"toy::{variant}",
        "original_id": "toy",
        "dataset": "toy",
        "variant": variant,
        "nodes": [
            {"id": "a", "label": "Drug X"},
            {"id": "b", "label": "Protein Y"},
            {"id": "c", "label": "Disease Z"},
        ],
        "edges": [
            {"subj": "a", "pred": "inhibits", "obj": "b"},
            {"subj": "b", "pred": "associated_with", "obj": "c"},
        ],
        "facts": [
            {"id": "f0", "text": "Drug X inhibits Protein Y", "edge_refs": [0]},
            {"id": "f1", "text": "Protein Y associated with Disease Z", "edge_refs": [1]},
        ],
        "operations": [{"edge_index": 0, "operation": variant, "target": "Drug X"}],
    }


def test_mine1_score_matches_official_mean_formula():
    assert mine1_score([1, 1, 0, True, False]) == 0.6


def test_two_hop_retrieval_recovers_fact_when_graph_contains_it():
    item = {
        "id": "item0",
        "dataset": "toy",
        "variant": "clean",
        "fact": "Drug X inhibits Protein Y",
        "reference_edge": {"subject": "Drug X", "predicate": "inhibits", "object": "Protein Y"},
        "candidate_graph": {
            "edges": [
                {"subject": "Drug X", "predicate": "inhibits", "object": "Protein Y"},
                {"subject": "Protein Y", "predicate": "associated_with", "object": "Disease Z"},
            ]
        },
    }
    scored = score_item(item)
    assert scored["recoverable"] is True
    assert scored["score"] == 1.0


def test_edge_deletion_makes_target_fact_unrecoverable():
    edges = apply_controlled_perturbation(toy_record("edge_deletion"))
    assert all(edge.predicate != "inhibits" for edge in edges)


def test_prepare_and_score_roundtrip(tmp_path: Path):
    input_path = tmp_path / "perturbed.jsonl"
    input_path.write_text(json.dumps(toy_record("edge_deletion")) + "\n", encoding="utf8")
    out_path = tmp_path / "items.jsonl"
    report = prepare([str(input_path)], str(out_path), limit=10)
    assert report["items"] == 1
    item = json.loads(out_path.read_text(encoding="utf8").strip())
    scored = score_item(item)
    assert scored["recoverable"] is False


def test_triple_f1_baseline(tmp_path: Path):
    input_path = tmp_path / "perturbed.jsonl"
    input_path.write_text(json.dumps(toy_record("argument_swap")) + "\n", encoding="utf8")
    out = tmp_path / "triple.json"
    report = run_triple_f1([str(input_path)], str(out))
    assert report["status"] == "passed"
    assert report["items"] == 1
    assert report["exact_recovery"] == 0.0

from lemon_factor.baselines.mine1_like.core import parse_recoverability_judgment, score_item_with_judgment
from lemon_factor.baselines.mine1_like.prompts import build_prompt_payload
from lemon_factor.baselines.mine1_like.prepare_llm_judge import prepare as prepare_llm_judge
from lemon_factor.baselines.mine1_like.score import score as score_mine_like
from lemon_factor.analysis.metric_radar import build as build_metric_radar


def test_llm_prompt_payload_contains_schema():
    item = {
        "id": "item0",
        "dataset": "toy",
        "variant": "clean",
        "fact": "Drug X inhibits Protein Y",
        "reference_edge": {"subject": "Drug X", "predicate": "inhibits", "object": "Protein Y"},
        "candidate_graph": {"edges": [{"subject": "Drug X", "predicate": "inhibits", "object": "Protein Y"}]},
    }
    payload = build_prompt_payload(item, model="test/model", judge_id="judge")
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["item_id"] == "item0"


def test_parse_recoverability_judgment_from_content():
    row = {"item_id": "item0", "content": '{"recoverable": true, "confidence": 0.9, "evidence": "edge present"}'}
    parsed = parse_recoverability_judgment(row)
    assert parsed["item_id"] == "item0"
    assert parsed["recoverable"] is True


def test_score_with_saved_llm_judgments(tmp_path: Path):
    item = {
        "id": "item0",
        "dataset": "toy",
        "variant": "clean",
        "fact": "Drug X inhibits Protein Y",
        "reference_edge": {"subject": "Drug X", "predicate": "inhibits", "object": "Protein Y"},
        "candidate_graph": {"edges": [{"subject": "Drug X", "predicate": "inhibits", "object": "Protein Y"}]},
    }
    items = tmp_path / "items.jsonl"
    judgments = tmp_path / "judgments.jsonl"
    out = tmp_path / "score.json"
    items.write_text(json.dumps(item) + "\n", encoding="utf8")
    judgments.write_text(json.dumps({"item_id": "item0", "recoverable": True, "confidence": 1.0, "evidence": "present"}) + "\n", encoding="utf8")
    report = score_mine_like(str(items), str(out), mode="llm_saved", judgments=str(judgments))
    assert report["mine1_like_score"] == 1.0
    assert report["items_scored"] == 1


def test_prepare_llm_judge_roundtrip(tmp_path: Path):
    item = {
        "id": "item0",
        "dataset": "toy",
        "variant": "clean",
        "fact": "Drug X inhibits Protein Y",
        "reference_edge": {"subject": "Drug X", "predicate": "inhibits", "object": "Protein Y"},
        "candidate_graph": {"edges": [{"subject": "Drug X", "predicate": "inhibits", "object": "Protein Y"}]},
    }
    items = tmp_path / "items.jsonl"
    prompts = tmp_path / "prompts.jsonl"
    items.write_text(json.dumps(item) + "\n", encoding="utf8")
    report = prepare_llm_judge(str(items), str(prompts), model="m", judge_id="j")
    assert report["items"] == 1
    assert prompts.exists()


def test_metric_radar_build(tmp_path: Path):
    scoring = tmp_path / "scoring.json"
    mine = tmp_path / "mine.json"
    triple = tmp_path / "triple.json"
    out = tmp_path / "radar.json"
    tex = tmp_path / "radar.tex"
    scoring.write_text(json.dumps({"summary": [{"variant": "edge_deletion", "metrics": {"lemon_full": 0.25}}, {"variant": "argument_swap", "metrics": {"lemon_full": 0.5}}]}), encoding="utf8")
    mine.write_text(json.dumps({"mode": "lexical", "mine1_like_score": 0.3, "by_dataset_variant": [{"variant": "edge_deletion", "mine1_like_score": 0.0}]}), encoding="utf8")
    triple.write_text(json.dumps({"exact_recovery": 0.1, "by_dataset_variant": [{"variant": "edge_deletion", "exact_recovery": 0.0}]}), encoding="utf8")
    report = build_metric_radar([str(scoring)], str(mine), str(triple), str(out), tex_out=str(tex))
    assert report["status"] == "passed"
    assert "Damage proxy" in report["methods"]
    assert tex.exists()
