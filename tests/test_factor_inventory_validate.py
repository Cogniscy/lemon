from __future__ import annotations

import json
from pathlib import Path

from lemon_factor.factors.decomposition import PredicateDecompositionSet
from lemon_factor.factors.validate import report_to_markdown, validate_inventory


def test_drugprot_inventory_is_valid() -> None:
    inventory = PredicateDecompositionSet.from_json_file("resources/factors/drugprot.json")
    assert inventory.metadata["dataset"] == "drugprot"
    assert "chemical_inhibits_gene_or_protein" in inventory.decompositions
    assert len(inventory.decompositions) >= 13


def test_bc5cdr_inventory_separates_causality_from_entities() -> None:
    inventory = PredicateDecompositionSet.from_json_file("resources/factors/bc5cdr.json")
    decomp = inventory.decompositions["chemical_disease_interaction"]
    factors = {component.factor for component in decomp.components}
    assert {"chemical", "disease", "causal_polarity"}.issubset(factors)


def test_validate_inventory_reports_full_bc5cdr_coverage(tmp_path: Path) -> None:
    data = tmp_path / "bc5cdr.jsonl"
    data.write_text(
        json.dumps(
            {
                "id": "x",
                "dataset": "bc5cdr",
                "split": "train",
                "text": "Chemical X induces disease Y.",
                "language": "en",
                "nodes": [
                    {"id": "c", "label": "Chemical X", "type": "Chemical", "aliases": [], "external_ids": {}, "metadata": {}},
                    {"id": "d", "label": "Disease Y", "type": "Disease", "aliases": [], "external_ids": {}, "metadata": {}},
                ],
                "edges": [{"subj": "c", "pred": "chemical_disease_interaction", "obj": "d", "evidence": "", "metadata": {}}],
                "facts": [],
                "metadata": {},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    report = validate_inventory("resources/factors/bc5cdr.json", data_paths=[data], min_coverage=1.0)
    assert report["predicate_coverage"] == 1.0
    assert report["weight_sums_valid"] is True
    assert "Predicate coverage" in report_to_markdown(report)
