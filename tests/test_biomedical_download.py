from __future__ import annotations

import zipfile
from pathlib import Path

from lemon_factor.datasets.biomedical_download import extract_nested_zips, write_acquisition_manifest


def test_extract_nested_zips(tmp_path: Path) -> None:
    nested = tmp_path / "nested.zip"
    with zipfile.ZipFile(nested, "w") as zf:
        zf.writestr("data/file.txt", "hello")
    extracted = extract_nested_zips(tmp_path)
    assert extracted
    assert (tmp_path / "nested" / "data" / "file.txt").read_text(encoding="utf-8") == "hello"


def test_write_acquisition_manifest_lists_files(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "x.txt").write_text("x", encoding="utf-8")
    manifest = write_acquisition_manifest(
        tmp_path / "manifest.json",
        dataset="x",
        source_type="fixture",
        source_url="https://example.test",
        raw_dir=raw,
        status="downloaded",
    )
    assert manifest["file_count"] == 1
    assert manifest["files_detected"] == ["x.txt"]
