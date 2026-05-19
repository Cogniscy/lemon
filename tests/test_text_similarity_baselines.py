import pytest

from lemon_factor.baselines.text_similarity import (
    graph_source_text,
    jaccard_similarity,
    score_example_graph_text_similarity,
    token_cosine_similarity,
)


def test_token_cosine_similarity_is_one_for_identical_texts():
    assert token_cosine_similarity("Alan Bean", "Alan Bean") == pytest.approx(1.0)


def test_jaccard_similarity_handles_overlap():
    assert jaccard_similarity("Alan Bean astronaut", "Alan Bean pilot") == 0.5


def test_graph_source_text_uses_node_labels_and_predicates():
    example = {
        "nodes": [{"id": "n1", "label": "Alan Bean"}, {"id": "n2", "label": "Wheeler Texas"}],
        "edges": [{"subj": "n1", "pred": "birthPlace", "obj": "n2"}],
        "text": "Alan Bean was born in Wheeler, Texas.",
    }
    source = graph_source_text(example)
    assert "Alan Bean" in source
    assert "birthPlace" in source
    assert "Wheeler Texas" in source


def test_score_example_graph_text_similarity_returns_two_scores():
    example = {
        "nodes": [{"id": "n1", "label": "Alan Bean"}, {"id": "n2", "label": "Wheeler Texas"}],
        "edges": [{"subj": "n1", "pred": "birthPlace", "obj": "n2"}],
        "text": "Alan Bean was born in Wheeler, Texas.",
    }
    scores = score_example_graph_text_similarity(example)
    assert 0.0 < scores["token_cosine"] <= 1.0
    assert 0.0 < scores["token_jaccard"] <= 1.0
