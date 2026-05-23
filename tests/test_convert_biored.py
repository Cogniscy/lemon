from __future__ import annotations

from pathlib import Path

from lemon_factor.datasets.biomedical_common import write_graphtext_splits
from lemon_factor.datasets.convert_biored import load_local_documents, map_biored_relation
from lemon_factor.datasets.unified_io import read_jsonl


def test_biored_relation_mapping() -> None:
    assert map_biored_relation("Positive_Correlation") == "positive_correlation"
    assert map_biored_relation("Drug_Interaction") == "drug_interaction"


def test_biored_fixture_converts(tmp_path: Path) -> None:
    docs = load_local_documents("tests/fixtures/biomedical/biored")
    assert {doc.id for doc in docs} >= {"3001", "3002"}
    outputs = write_graphtext_splits(tmp_path, dataset="biored", documents=docs)
    examples = read_jsonl(outputs["train"])
    predicates = {edge.pred for ex in examples for edge in ex.edges}
    assert "positive_correlation" in predicates
    assert "biomolecular_binding" in predicates
