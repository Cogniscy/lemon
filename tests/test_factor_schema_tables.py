from pathlib import Path

from lemon_factor.analysis.factor_schema_tables import (
    decompositions_to_markdown,
    factor_schema_to_markdown,
)
from lemon_factor.factors.decomposition import write_factor_schema
from lemon_factor.factors.inventory import FactorInventory, PredicateInventoryItem
from lemon_factor.factors.seed_builder import build_seed_decomposition_set
from lemon_factor.factors.seed_schema import build_default_factor_schema


def test_factor_schema_to_markdown_contains_factor_rows(tmp_path: Path):
    schema_path = tmp_path / "schema.json"
    write_factor_schema(schema_path, build_default_factor_schema())
    table = factor_schema_to_markdown(schema_path)
    assert "| Factor | Level |" in table
    assert "biographical_relation" in table


def test_decompositions_to_markdown_contains_components(tmp_path: Path):
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
    path = tmp_path / "decompositions.json"
    decomposition_set.to_json_file(path)
    table = decompositions_to_markdown(path)
    assert "birthPlace" in table
    assert "biographical_relation" in table
