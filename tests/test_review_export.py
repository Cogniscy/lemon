import csv
from pathlib import Path

from lemon_factor.factors.inventory import FactorInventory, PredicateInventoryItem
from lemon_factor.factors.review_export import REVIEW_COLUMNS, write_review_csv
from lemon_factor.factors.seed_builder import build_seed_decomposition_set


def test_review_export_writes_required_columns(tmp_path: Path):
    inventory = FactorInventory(
        examples=1,
        predicates={
            "birthPlace": PredicateInventoryItem(
                predicate="birthPlace",
                count=1,
                categories={"Astronaut": 1},
                candidate_factors=["birth", "place"],
            )
        },
    )
    decomposition_set = build_seed_decomposition_set(inventory, top_k=1)
    decompositions_path = tmp_path / "decompositions.json"
    decomposition_set.to_json_file(decompositions_path)
    out_path = tmp_path / "review.csv"

    write_review_csv(decompositions_path, out_path)

    with out_path.open("r", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
    assert reader.fieldnames == REVIEW_COLUMNS
    assert rows[0]["predicate"] == "birthPlace"
    assert "biographical_relation" in rows[0]["proposed_components"]
