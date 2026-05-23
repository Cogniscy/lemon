from __future__ import annotations

from lemon_factor.datasets.biomedical_common import (
    BioDocument,
    BioEntity,
    BioRelation,
    document_to_graphtext,
    normalize_entity_id,
)


def test_normalize_entity_id_preserves_prefix_and_sanitizes() -> None:
    assert normalize_entity_id("MESH:D001241", prefix="bc5cdr", fallback="x") == "bc5cdr_MESH_D001241"
    assert normalize_entity_id("bc5cdr_existing", prefix="bc5cdr", fallback="x") == "bc5cdr_existing"


def test_document_to_graphtext_validates_nodes_edges_facts() -> None:
    doc = BioDocument(
        id="p1",
        split="train",
        title="Title",
        abstract="Abstract",
        entities=[
            BioEntity(id="n1", label="Drug", type="Chemical", external_id="MESH:D1"),
            BioEntity(id="n2", label="Disease", type="Disease", external_id="MESH:D2"),
        ],
        relations=[BioRelation(id="r1", subj="n1", pred="chemical_disease_interaction", obj="n2")],
    )
    ex = document_to_graphtext(doc, dataset="bc5cdr")
    assert ex.id == "bc5cdr::train::p1"
    assert ex.text == "Title Abstract"
    assert len(ex.nodes) == 2
    assert len(ex.edges) == 1
    assert len(ex.facts) == 1
    assert ex.nodes[0].external_ids["mesh"] == "MESH:D1"
