from __future__ import annotations

from lemon_factor.datasets.biomedical_common import BioDocument, BioEntity, BioRelation, document_to_graphtext
from lemon_factor.datasets.biomedical_quality import summarize_quality, validate_quality


def test_biomedical_quality_rejects_empty_text() -> None:
    ex = document_to_graphtext(
        BioDocument(
            id="p1",
            split="train",
            title="",
            abstract="",
            entities=[
                BioEntity(id="n1", label="Drug", type="Chemical"),
                BioEntity(id="n2", label="Protein", type="GeneOrProtein"),
            ],
            relations=[BioRelation(id="r1", subj="n1", pred="chemical_inhibits_gene_or_protein", obj="n2")],
        ),
        dataset="drugprot",
    )
    stats = summarize_quality([ex])
    errors = validate_quality(stats)
    assert any("non-empty text" in error for error in errors)


def test_biomedical_quality_accepts_valid_example() -> None:
    ex = document_to_graphtext(
        BioDocument(
            id="p1",
            split="train",
            title="Drug title",
            abstract="Drug inhibits protein.",
            entities=[
                BioEntity(id="n1", label="Drug", type="Chemical"),
                BioEntity(id="n2", label="Protein", type="GeneOrProtein"),
            ],
            relations=[BioRelation(id="r1", subj="n1", pred="chemical_inhibits_gene_or_protein", obj="n2")],
        ),
        dataset="drugprot",
    )
    stats = summarize_quality([ex])
    assert validate_quality(stats) == []
    assert stats["text_chars_avg"] > 0
