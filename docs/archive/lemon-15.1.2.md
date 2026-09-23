# lemon-15.1.2 — Biomedical acquisition layer

## Goal

Make biomedical dataset acquisition less fragile. `bigbio/bc5cdr` and similar scripted datasets are unreliable with current `datasets` versions, and ChemProt often requires local manual access. This patch adds direct public-source workflows where possible.

## Changes

- Added `src/lemon_factor/datasets/biomedical_download.py` for downloads, zip extraction, nested zip extraction, Zenodo record access, and acquisition manifests.
- Added `--source direct` to `convert_bc5cdr` using the Open Biomedical Corpora GitHub mirror.
- Added `--source direct` to `convert_biored` using the NCBI BioRED GitHub repository.
- Added `convert_drugprot.py` as an accessible chemical--gene/protein alternative to ChemProt, with `--source direct` via Zenodo record 4955411.
- Added `biomedical_sources_check.py` and `paper/tables/table_biomedical_sources_check.md` generation.
- `choose_local_files` now searches recursively so extracted repository archives and nested corpus zips can be passed as one raw directory.

## Commands

```powershell
python -m lemon_factor.datasets.biomedical_sources_check `
  --out data/biomedical/reports/biomedical_sources_check.json `
  --table paper/tables/table_biomedical_sources_check.md
```

```powershell
python -m lemon_factor.datasets.convert_bc5cdr `
  --source direct `
  --download-dir data/biomedical/raw/bc5cdr `
  --out-dir data/biomedical/processed `
  --manifest data/biomedical/manifests/bc5cdr_manifest.json `
  --limit 200
```

```powershell
python -m lemon_factor.datasets.convert_drugprot `
  --source direct `
  --download-dir data/biomedical/raw/drugprot `
  --out-dir data/biomedical/processed `
  --manifest data/biomedical/manifests/drugprot_manifest.json `
  --limit 200
```

```powershell
python -m lemon_factor.datasets.convert_biored `
  --source direct `
  --download-dir data/biomedical/raw/biored `
  --out-dir data/biomedical/processed `
  --manifest data/biomedical/manifests/biored_manifest.json `
  --limit 200
```

## Notes

Raw biomedical datasets are not committed. Every direct acquisition writes an acquisition manifest under `data/biomedical/manifests/` with source URL, status, file count, and license notes.
