from __future__ import annotations

from pathlib import Path

from lemon_factor.analysis.inventory_stats import inventory_to_markdown_table
from lemon_factor.datasets.convert_webnlg import convert_records
from lemon_factor.datasets.unified_io import write_jsonl
from lemon_factor.factors.inventory import FactorInventory, build_inventory, build_inventory_from_jsonl, summarize_inventory


def _examples():
    records = [
        {
            "gem_id": "a",
            "input": [
                "Alan_Bean | birthPlace | Wheeler,_Texas",
                "Alan_Bean | nationality | United_States",
            ],
            "target": "Alan Bean was born in Wheeler, Texas and was American.",
            "category": "Astronaut",
        },
        {
            "gem_id": "b",
            "input": [
                "Aarhus_Airport | cityServed | Aarhus,_Denmark",
                "Aarhus_Airport | location | Tirstrup",
            ],
            "target": "Aarhus Airport serves Aarhus and is in Tirstrup.",
            "category": "Airport",
        },
        {
            "gem_id": "c",
            "input": ["Neil_Armstrong | birthPlace | Wapakoneta,_Ohio"],
            "target": "Neil Armstrong was born in Wapakoneta, Ohio.",
            "category": "Astronaut",
        },
    ]
    return convert_records(records, split="train")


def test_build_inventory_counts_predicates() -> None:
    inventory = build_inventory(_examples())
    assert inventory.examples == 3
    assert inventory.predicates["birthPlace"].count == 2
    assert inventory.predicates["cityServed"].count == 1
    assert inventory.categories == {"Astronaut": 2, "Airport": 1}


def test_predicate_maps_to_categories_and_candidate_factors() -> None:
    inventory = build_inventory(_examples())
    item = inventory.predicates["birthPlace"]
    assert item.categories == {"Astronaut": 2}
    assert item.candidate_factors == ["birth", "place"]
    assert len(item.examples) == 2


def test_node_labels_are_deduplicated_and_counted() -> None:
    inventory = build_inventory(_examples())
    assert inventory.node_labels["Alan Bean"].count == 1
    assert inventory.node_labels["Wheeler, Texas"].count == 1
    assert inventory.node_labels["Alan Bean"].categories == {"Astronaut": 1}


def test_contexts_are_limited() -> None:
    inventory = build_inventory(_examples(), max_contexts_per_item=1)
    assert len(inventory.predicates["birthPlace"].examples) == 1


def test_inventory_json_roundtrip(tmp_path: Path) -> None:
    inventory = build_inventory(_examples())
    path = tmp_path / "inventory.json"
    inventory.to_json_file(path)
    loaded = FactorInventory.from_json_file(path)
    assert loaded.predicates["birthPlace"].count == 2


def test_build_inventory_from_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "examples.jsonl"
    write_jsonl(path, _examples())
    inventory = build_inventory_from_jsonl(path)
    assert inventory.predicates["birthPlace"].count == 2


def test_summarize_inventory_includes_top_candidates() -> None:
    summary = summarize_inventory(build_inventory(_examples()), top_k=3)
    assert summary["predicate_count"] == 4
    assert "top_candidate_factors" in summary
    assert summary["top_predicates"][0]["predicate"] == "birthPlace"


def test_inventory_to_markdown_table() -> None:
    table = inventory_to_markdown_table(build_inventory(_examples()), top_k=2)
    assert "| Predicate | Count | Categories | Candidate factors | Example |" in table
    assert "birthPlace" in table
    assert "birth, place" in table
