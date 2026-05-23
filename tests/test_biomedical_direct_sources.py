from __future__ import annotations

from pathlib import Path

from lemon_factor.datasets.convert_bc5cdr import download_direct_corpus as download_bc5cdr_direct
from lemon_factor.datasets.convert_biored import download_direct_corpus as download_biored_direct


def test_bc5cdr_direct_download_path_uses_local_loader_layout(tmp_path: Path, monkeypatch) -> None:
    import lemon_factor.datasets.convert_bc5cdr as mod

    def fake_download(owner: str, repo: str, out_dir: str | Path, *, branch: str = "master") -> Path:
        raw = Path(out_dir) / "biocreative-v-cdr-master" / "original-data"
        raw.mkdir(parents=True)
        (raw / "CDR_TrainingSet.PubTator.txt").write_text(
            "1|t|Aspirin bleeding\n"
            "1|a|Aspirin causes bleeding.\n"
            "1\t0\t7\tAspirin\tChemical\tMESH:D001241\n"
            "1\t15\t23\tbleeding\tDisease\tMESH:D001908\n"
            "1\tCID\tMESH:D001241\tMESH:D001908\n\n",
            encoding="utf-8",
        )
        return Path(out_dir)

    monkeypatch.setattr(mod, "download_github_repo_zip", fake_download)
    monkeypatch.setattr(mod, "extract_nested_zips", lambda out_dir: [])
    raw_dir = download_bc5cdr_direct(tmp_path / "bc5cdr", tmp_path / "acq.json")
    assert (raw_dir / "biocreative-v-cdr-master" / "original-data" / "CDR_TrainingSet.PubTator.txt").exists()
    assert (tmp_path / "acq.json").exists()


def test_biored_direct_download_writes_manifest(tmp_path: Path, monkeypatch) -> None:
    import lemon_factor.datasets.convert_biored as mod

    def fake_download(owner: str, repo: str, out_dir: str | Path, *, branch: str = "master") -> Path:
        raw = Path(out_dir) / "BioRED-master"
        raw.mkdir(parents=True)
        (raw / "Train.PubTator.txt").write_text("1|t|T\n1|a|A\n\n", encoding="utf-8")
        return Path(out_dir)

    monkeypatch.setattr(mod, "download_github_repo_zip", fake_download)
    monkeypatch.setattr(mod, "extract_nested_zips", lambda out_dir: [])
    raw_dir = download_biored_direct(tmp_path / "biored", tmp_path / "acq.json")
    assert raw_dir.exists()
    assert (tmp_path / "acq.json").exists()
