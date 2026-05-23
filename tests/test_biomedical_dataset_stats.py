from __future__ import annotations

from pathlib import Path

from lemon_factor.analysis.biomedical_dataset_stats import summarize_biomedical_examples, write_markdown_table
from lemon_factor.datasets.biomedical_common import BioDocument, BioEntity, BioRelation, document_to_graphtext


def test_biomedical_stats_count_entity_types_and_normalization(tmp_path: Path) -> None:
    ex = document_to_graphtext(
        BioDocument(
            id="p1",
            split="train",
            entities=[
                BioEntity(id="n1", label="Drug", type="Chemical", external_id="MESH:D1"),
                BioEntity(id="n2", label="Protein", type="Protein", external_id="NCBI:1"),
            ],
            relations=[BioRelation(id="r1", subj="n1", pred="chemical_upregulates_protein", obj="n2", metadata={"document_level": False})],
        ),
        dataset="chemprot",
    )
    stats = summarize_biomedical_examples([ex])
    assert stats["examples"] == 1
    assert stats["entity_type_counts"] == {"Chemical": 1, "Protein": 1}
    assert stats["predicate_counts"] == {"chemical_upregulates_protein": 1}
    assert stats["normalization_id_coverage"] == 1.0
    table = tmp_path / "table.md"
    write_markdown_table({"x": {**stats, "dataset": "chemprot", "split": "train"}}, table)
    assert "chemical_upregulates_protein" in table.read_text(encoding="utf-8")
