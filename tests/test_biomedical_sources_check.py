from __future__ import annotations

from pathlib import Path

from lemon_factor.datasets.biomedical_sources_check import SOURCES, write_markdown_table


def test_biomedical_sources_include_drugprot_and_manual_chemprot(tmp_path: Path) -> None:
    names = {row["dataset"] for row in SOURCES}
    assert {"BC5CDR", "BioRED", "DrugProt", "ChemProt"} <= names
    chemprot = next(row for row in SOURCES if row["dataset"] == "ChemProt")
    assert chemprot["local_required"] is True
    table = tmp_path / "sources.md"
    write_markdown_table(SOURCES, table)
    text = table.read_text(encoding="utf-8")
    assert "DrugProt" in text
    assert "optional/manual" in text
