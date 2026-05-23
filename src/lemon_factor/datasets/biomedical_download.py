"""Acquisition helpers for biomedical datasets.

These helpers keep raw downloads outside versioned source files, write a
separate acquisition manifest, and expose deterministic, testable primitives for
converter CLIs. Network calls are intentionally thin wrappers around urllib so
that tests can monkeypatch them easily.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

from lemon_factor.datasets.biomedical_common import now_utc_iso


class DownloadError(RuntimeError):
    """Raised when a direct dataset download cannot be completed."""


def download_file(url: str, out_path: str | Path, *, sha256: str | None = None, timeout: int = 120) -> Path:
    """Download a URL to a local path.

    Existing non-empty files are reused. If ``sha256`` is supplied, the file is
    verified after download/reuse.
    """

    target = Path(out_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists() or target.stat().st_size == 0:
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310 - URLs are explicit dataset sources
                with target.open("wb") as fh:
                    shutil.copyfileobj(response, fh)
        except urllib.error.URLError as exc:  # pragma: no cover - network dependent
            raise DownloadError(f"Could not download {url}. Manual download may be required.") from exc
    if sha256:
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if digest.lower() != sha256.lower():
            raise DownloadError(f"Checksum mismatch for {target}: expected {sha256}, got {digest}")
    return target


def extract_zip(zip_path: str | Path, out_dir: str | Path) -> Path:
    """Extract a zip archive into ``out_dir`` and return the directory."""

    archive = Path(zip_path)
    target = Path(out_dir)
    target.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(target)
    except zipfile.BadZipFile as exc:
        raise DownloadError(f"Downloaded file is not a valid zip archive: {archive}") from exc
    return target


def extract_nested_zips(base_dir: str | Path) -> list[Path]:
    """Extract zip files found under ``base_dir`` next to each archive.

    This is useful for GitHub repository archives that contain corpus archives
    such as ``BIORED.zip`` inside the downloaded repository zip.
    """

    base = Path(base_dir)
    extracted: list[Path] = []
    for archive in sorted(base.rglob("*.zip")):
        nested_out = archive.with_suffix("")
        if nested_out.exists() and any(nested_out.iterdir()):
            extracted.append(nested_out)
            continue
        extract_zip(archive, nested_out)
        extracted.append(nested_out)
    return extracted


def download_github_repo_zip(owner: str, repo: str, out_dir: str | Path, *, branch: str = "master") -> Path:
    """Download a GitHub repository archive and extract it under ``out_dir``."""

    url = f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{branch}"
    target_dir = Path(out_dir)
    archive = target_dir / f"{repo}-{branch}.zip"
    download_file(url, archive)
    return extract_zip(archive, target_dir)


def read_zenodo_record(record_id: str) -> dict[str, Any]:
    """Read a Zenodo record metadata payload."""

    url = f"https://zenodo.org/api/records/{record_id}"
    try:
        with urllib.request.urlopen(url, timeout=60) as response:  # noqa: S310 - fixed Zenodo API URL
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError) as exc:  # pragma: no cover - network dependent
        raise DownloadError(f"Could not reach Zenodo record API: {url}") from exc


def download_zenodo_record_files(record_id: str, out_dir: str | Path, *, filename_contains: str | None = None) -> list[Path]:
    """Download files from a Zenodo record.

    If ``filename_contains`` is provided, only files whose key/name contains the
    token are downloaded.
    """

    payload = read_zenodo_record(record_id)
    files = payload.get("files") or []
    if not isinstance(files, list) or not files:
        raise DownloadError(f"Zenodo record {record_id} does not expose downloadable files")
    downloaded: list[Path] = []
    target_dir = Path(out_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    token = filename_contains.lower() if filename_contains else None
    for file_info in files:
        if not isinstance(file_info, dict):
            continue
        name = str(file_info.get("key") or file_info.get("filename") or "")
        if token and token not in name.lower():
            continue
        links = file_info.get("links") or {}
        url = links.get("self") or links.get("download")
        if not url:
            continue
        downloaded.append(download_file(str(url), target_dir / name))
    if not downloaded:
        raise DownloadError(f"No matching files were downloaded from Zenodo record {record_id}")
    return downloaded


def write_acquisition_manifest(
    path: str | Path,
    *,
    dataset: str,
    source_type: str,
    source_url: str,
    raw_dir: str | Path,
    status: str,
    license_note: str | None = None,
    notes: list[str] | None = None,
    limitations: list[str] | None = None,
) -> dict[str, Any]:
    """Write a raw-data acquisition manifest."""

    base = Path(raw_dir)
    files = [str(p.relative_to(base)) for p in sorted(base.rglob("*")) if p.is_file()] if base.exists() else []
    payload: dict[str, Any] = {
        "dataset": dataset,
        "source_type": source_type,
        "source_url": source_url,
        "raw_dir": str(base),
        "status": status,
        "downloaded_at": now_utc_iso(),
        "files_detected": files[:500],
        "file_count": len(files),
        "license_note": license_note,
        "notes": notes or [],
        "limitations": limitations or [],
    }
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload
