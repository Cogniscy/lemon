from __future__ import annotations

from lemon_factor.analysis.dataset_stats import summarize_examples
from lemon_factor.datasets.convert_webnlg import convert_records, webnlg_record_to_graphtext
from lemon_factor.datasets.normalization import clean_label, parse_webnlg_triple, stable_id
from lemon_factor.schema.graphtext import Split


def test_clean_label_removes_quotes_and_underscores() -> None:
    assert clean_label('"Aarhus, Denmark"') == "Aarhus, Denmark"
    assert clean_label("Aarhus_Airport") == "Aarhus Airport"


def test_stable_id_is_deterministic() -> None:
    assert stable_id("n", "Aarhus Airport") == stable_id("n", "aarhus airport")
    assert stable_id("node", "Aarhus Airport").startswith("node_")


def test_parse_webnlg_triple_pipe_format() -> None:
    parsed = parse_webnlg_triple('Aarhus_Airport | cityServed | "Aarhus, Denmark"')
    assert parsed.subj == "Aarhus Airport"
    assert parsed.pred == "cityServed"
    assert parsed.obj == "Aarhus, Denmark"


def test_parse_webnlg_triple_parenthesized_format() -> None:
    parsed = parse_webnlg_triple("(Alan_Bean, birthPlace, Wheeler,_Texas)")
    assert parsed.subj == "Alan Bean"
    assert parsed.pred == "birthPlace"
    assert parsed.obj == "Wheeler, Texas"


def test_convert_record_creates_nodes_edges_facts() -> None:
    record = {
        "gem_id": "web_nlg_en-train-0",
        "gem_parent_id": "web_nlg_en-train-0",
        "input": ['Aarhus_Airport | cityServed | "Aarhus, Denmark"'],
        "target": "The Aarhus is the airport of Aarhus, Denmark.",
        "references": [],
        "category": "Airport",
        "webnlg_id": "train/Airport/1/Id1",
    }
    example = webnlg_record_to_graphtext(record, split="train", language="en")
    assert example.id == "web_nlg_en-train-0"
    assert example.dataset == "webnlg"
    assert example.split == Split.train
    assert example.language == "en"
    assert len(example.nodes) == 2
    assert len(example.edges) == 1
    assert len(example.facts) == 1
    assert example.edges[0].pred == "cityServed"
    assert example.facts[0].metadata["source"] == "webnlg_triple"


def test_validation_split_maps_to_dev() -> None:
    record = {
        "gem_id": "web_nlg_en-validation-0",
        "input": ["Alan_Bean | birthPlace | Wheeler,_Texas"],
        "target": "Alan Bean was born in Wheeler, Texas.",
    }
    example = webnlg_record_to_graphtext(record, split="validation", language="en")
    assert example.split == Split.dev


def test_convert_records_preserves_order() -> None:
    records = [
        {"gem_id": "a", "input": ["A | p | B"], "target": "A p B."},
        {"gem_id": "b", "input": ["C | q | D"], "target": "C q D."},
    ]
    examples = convert_records(records, split="train")
    assert [example.id for example in examples] == ["a", "b"]
    assert [example.edges[0].pred for example in examples] == ["p", "q"]


def test_stats_count_edges_and_predicates() -> None:
    examples = convert_records(
        [
            {"gem_id": "a", "input": ["A | p | B"], "target": "A p B.", "category": "X"},
            {"gem_id": "b", "input": ["C | p | D", "C | q | E"], "target": "C p D and q E."},
        ],
        split="train",
    )
    stats = summarize_examples(examples)
    assert stats["examples"] == 2
    assert stats["edges_total"] == 3
    assert stats["facts_total"] == 3
    assert stats["unique_predicates"] == 2
    assert stats["top_predicates"][0] == ("p", 2)
