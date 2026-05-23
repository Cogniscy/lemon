# lemon-15.1.1 — Biomedical converter UX and HF Parquet fallback

This patch stabilizes the biomedical converters after live checks on Windows.

## Problem

`datasets>=4` no longer supports loading dataset scripts through `trust_remote_code`. As a result, `load_dataset("bigbio/bc5cdr", ..., trust_remote_code=True)` fails with `Dataset scripts are no longer supported`. Local ChemProt/BioRED commands can also fail with raw-directory tracebacks when raw files have not been downloaded.

## Changes

- Added `--source hf-parquet` to `convert_bc5cdr`.
- Retained `--source bigbio` as a legacy alias that routes through converted Parquet and emits an actionable error if unavailable.
- Added HuggingFace `/parquet` endpoint parsing for converted Parquet files.
- Added robust BigBio row parsing for converted Parquet rows.
- Added concise missing-directory / no-raw-files messages for BC5CDR, ChemProt, and BioRED.
- Added unit tests for Parquet API payload parsing and BigBio row conversion.

## Recommended BC5CDR command

```powershell
python -m lemon_factor.datasets.convert_bc5cdr `
  --source hf-parquet `
  --out-dir data/biomedical/processed `
  --manifest data/biomedical/manifests/bc5cdr_manifest.json `
  --limit 200
```

If converted Parquet is unavailable on HuggingFace, use local PubTator/BioC/JSONL raw files:

```powershell
mkdir data\biomedical\raw\bc5cdr
python -m lemon_factor.datasets.convert_bc5cdr `
  --source local `
  --raw-dir data/biomedical/raw/bc5cdr `
  --out-dir data/biomedical/processed `
  --manifest data/biomedical/manifests/bc5cdr_manifest.json
```

## Tests

```text
169 passed
```
