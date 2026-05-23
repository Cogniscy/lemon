from __future__ import annotations

from pathlib import Path

from lemon_factor.datasets.convert_bc5cdr import load_local_documents, map_bc5cdr_relation
from lemon_factor.datasets.unified_io import read_jsonl


def test_bc5cdr_relation_mapping() -> None:
    assert map_bc5cdr_relation("CID") == "chemical_disease_interaction"


def test_bc5cdr_json_fixture_converts(tmp_path: Path) -> None:
    from lemon_factor.datasets.biomedical_common import write_graphtext_splits

    docs = load_local_documents("tests/fixtures/biomedical/bc5cdr")
    assert {doc.id for doc in docs} >= {"1001", "1002"}
    outputs = write_graphtext_splits(tmp_path, dataset="bc5cdr", documents=docs)
    examples = read_jsonl(outputs["train"])
    assert any(ex.edges[0].pred == "chemical_disease_interaction" for ex in examples if ex.edges)
    assert any(node.type == "Chemical" for ex in examples for node in ex.nodes)


def test_bc5cdr_hf_parquet_payload_to_data_files() -> None:
    from lemon_factor.datasets.convert_bc5cdr import parquet_payload_to_data_files

    data_files = parquet_payload_to_data_files(
        {
            "parquet_files": [
                {
                    "config": "bc5cdr_bigbio_kb",
                    "split": "train",
                    "filename": "0000.parquet",
                },
                {
                    "config": "bc5cdr_bigbio_kb",
                    "split": "validation",
                    "url": "https://example.test/dev.parquet",
                },
            ]
        }
    )
    assert set(data_files) == {"train", "dev"}
    assert data_files["train"][0].startswith("hf://datasets/bigbio/bc5cdr@refs/convert/parquet/")
    assert data_files["dev"] == ["https://example.test/dev.parquet"]


def test_bc5cdr_bigbio_row_to_document() -> None:
    from lemon_factor.datasets.convert_bc5cdr import bigbio_row_to_document

    document = bigbio_row_to_document(
        {
            "document_id": "42",
            "passages": [
                {"type": "title", "text": "Drug and disease"},
                {"type": "abstract", "text": "Aspirin causes bleeding."},
            ],
            "entities": [
                {"id": "T1", "text": "Aspirin", "type": "Chemical", "db_id": "MESH:D001241"},
                {"id": "T2", "text": "bleeding", "type": "Disease", "db_id": "MESH:D001908"},
            ],
            "relations": [{"type": "CID", "arg_ids": ["T1", "T2"]}],
        },
        "train",
    )
    assert document.id == "42"
    assert document.title == "Drug and disease"
    assert document.relations[0].pred == "chemical_disease_interaction"
    assert {entity.type for entity in document.entities} == {"Chemical", "Disease"}
