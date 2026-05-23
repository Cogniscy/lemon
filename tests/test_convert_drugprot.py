from __future__ import annotations

from pathlib import Path

from lemon_factor.datasets.biomedical_common import write_graphtext_splits
from lemon_factor.datasets.convert_drugprot import load_local_documents, map_drugprot_relation, _is_abstract_file
from lemon_factor.datasets.unified_io import read_jsonl


def test_drugprot_relation_mapping() -> None:
    assert map_drugprot_relation("INHIBITOR") == "chemical_inhibits_gene_or_protein"
    assert map_drugprot_relation("PRODUCT-OF") == "chemical_product_of_gene_or_protein"
    assert map_drugprot_relation("DIRECT-REGULATOR") == "chemical_directly_regulates_gene_or_protein"
    assert map_drugprot_relation("SUBSTRATE_PRODUCT-OF") == "chemical_substrate_product_of_gene_or_protein"


def test_drugprot_accepts_official_abstracs_typo() -> None:
    assert _is_abstract_file(Path("drugprot_training_abstracs.tsv"))
    assert _is_abstract_file(Path("drugprot_development_abstracts.tsv"))


def test_drugprot_fixture_converts(tmp_path: Path) -> None:
    docs = load_local_documents("tests/fixtures/biomedical/drugprot")
    assert {doc.id for doc in docs} >= {"4001", "4002"}
    outputs = write_graphtext_splits(tmp_path, dataset="drugprot", documents=docs)
    examples = read_jsonl(outputs["train"])
    assert all(ex.text.strip() for ex in examples)
    predicates = {edge.pred for ex in examples for edge in ex.edges}
    assert "chemical_inhibits_gene_or_protein" in predicates
    assert "chemical_substrate_of_gene_or_protein" in predicates
    assert any(node.type == "GeneOrProtein" for ex in examples for node in ex.nodes)
