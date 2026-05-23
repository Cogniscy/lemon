from __future__ import annotations

from pathlib import Path

from lemon_factor.datasets.biomedical_common import write_graphtext_splits
from lemon_factor.datasets.convert_chemprot import load_local_documents, map_chemprot_relation
from lemon_factor.datasets.unified_io import read_jsonl


def test_chemprot_relation_mapping() -> None:
    assert map_chemprot_relation("CPR:5") == "chemical_agonist_of_protein"
    assert map_chemprot_relation("CPR_6") == "chemical_antagonist_of_protein"


def test_chemprot_fixture_converts(tmp_path: Path) -> None:
    docs = load_local_documents("tests/fixtures/biomedical/chemprot", keep_relations={"CPR:3", "CPR:4", "CPR:5", "CPR:6", "CPR:9"})
    assert {doc.id for doc in docs} >= {"2001", "2002"}
    outputs = write_graphtext_splits(tmp_path, dataset="chemprot", documents=docs)
    examples = read_jsonl(outputs["train"])
    predicates = {edge.pred for ex in examples for edge in ex.edges}
    assert "chemical_agonist_of_protein" in predicates
    assert "chemical_antagonist_of_protein" in predicates
