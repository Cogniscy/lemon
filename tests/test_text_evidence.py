from lemon_factor.coverage.text_evidence import (
    cue_in_text,
    label_in_text,
    normalize_text,
    token_overlap_score,
)


def test_normalize_text_handles_underscores_and_camel_case():
    assert normalize_text("Aarhus_Airport") == "aarhus airport"
    assert normalize_text("birthPlace") == "birth place"


def test_label_in_text_handles_entity_parts():
    assert label_in_text("Aarhus_Airport", "The Aarhus airport serves Aarhus, Denmark.")


def test_token_overlap_score_counts_label_tokens():
    assert token_overlap_score("Alan Bean", "Alan Bean was born in Texas.") == 1.0
    assert token_overlap_score("Alan Bean", "Alan was born in Texas.") == 0.5


def test_cue_in_text_ignores_standalone_weak_stopword():
    assert cue_in_text("born in", "Alan Bean was born in Wheeler, Texas.")
    assert not cue_in_text("in", "Alan Bean was born in Wheeler, Texas.")
