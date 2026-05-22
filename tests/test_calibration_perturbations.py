import json
from pathlib import Path

from lemon_factor.calibration.calibration_stats import summarize_calibration_rows
from lemon_factor.calibration.perturb_graph import perturb_reconstructed_graph_corpus
from lemon_factor.calibration.perturb_text import perturb_text_corpus
from lemon_factor.datasets.unified_io import write_jsonl
from lemon_factor.reverse.reconstruct_graph import reconstruct_corpus
from lemon_factor.schema.graphtext import Edge, GraphTextExample, Node, Split


def toy_example() -> GraphTextExample:
    return GraphTextExample(
        id="ex1",
        dataset="toy",
        split=Split.dev,
        text="Alan Bean was born in Wheeler Texas.",
        nodes=[Node(id="n1", label="Alan Bean"), Node(id="n2", label="Wheeler Texas")],
        edges=[Edge(subj="n1", pred="birthPlace", obj="n2")],
    )


def test_text_perturbation_saves_manifest(tmp_path: Path):
    examples = [toy_example()]
    perturbed, manifest = perturb_text_corpus(
        examples,
        noise_type="delete_relation_phrase",
        noise_level=1.0,
        lexical_cues={"birthPlace": ["born in"]},
        seed=1,
    )
    assert perturbed[0].text != examples[0].text
    assert manifest[0].changed_edges == [0]
    assert manifest[0].expected_direction == "down"


def test_preserving_text_noise_has_stable_expectation():
    perturbed, manifest = perturb_text_corpus(
        [toy_example()],
        noise_type="entity_alias",
        noise_level=1.0,
        lexical_cues={"birthPlace": ["born in"]},
        seed=1,
    )
    assert manifest[0].expected_direction == "stable"
    assert perturbed[0].metadata["calibration_noise"]["noise_type"] == "entity_alias"


def test_graph_drop_edge_perturbation_reduces_edges():
    examples = [toy_example()]
    records = reconstruct_corpus(examples, lexical_cues={"birthPlace": ["born in"]})
    assert len(records[0].edges) == 1
    perturbed, manifest = perturb_reconstructed_graph_corpus(
        examples,
        records,
        noise_type="drop_edge",
        noise_level=1.0,
        seed=1,
    )
    assert len(perturbed[0].edges) == 0
    assert manifest[0].original_edge_count == 1
    assert manifest[0].perturbed_edge_count == 0


def test_calibration_summary_detects_negative_slope():
    rows = [
        {"noise_type": "drop_edge", "expected_direction": "down", "noise_level": 0.0, "forward_lemon": 1.0},
        {"noise_type": "drop_edge", "expected_direction": "down", "noise_level": 0.5, "forward_lemon": 0.5},
    ]
    summary = summarize_calibration_rows(rows, metrics=["forward_lemon"])
    assert summary[0]["sensitivity_slope"] < 0
    assert summary[0]["spearman_noise_score"] < 0


def test_calibration_summary_adds_target_and_quality():
    rows = [
        {"noise_type": "delete_relation_phrase", "noise_target": "text", "perturbation_quality": "clean", "expected_direction": "down", "noise_level": 0.0, "forward_lemon": 1.0},
        {"noise_type": "delete_relation_phrase", "noise_target": "text", "perturbation_quality": "clean", "expected_direction": "down", "noise_level": 0.5, "forward_lemon": 0.5},
    ]
    summary = summarize_calibration_rows(rows, metrics=["forward_lemon"])
    assert summary[0]["noise_target"] == "text"
    assert summary[0]["perturbation_quality"] == "clean"
