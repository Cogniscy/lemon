# lemon-15.1 — Biomedical dataset feasibility and converters

This stage adds biomedical dataset converters without running LEMON metrics yet. The goal is to make BC5CDR, ChemProt, and BioRED usable as GraphText inputs for later cross-domain validation.

## Scope

- BC5CDR: chemical--disease interactions.
- ChemProt: chemical--protein interaction classes, with CPR:3/4/5/6/9 kept by default.
- BioRED: document-level multi-entity biomedical relation annotations.

Raw biomedical data should live under `data/biomedical/raw/` and should not be committed. Conversion manifests are written under `data/biomedical/manifests/` and preserve source/access/license notes.

## Commands

BC5CDR from local PubTator/JSON fixtures:

```powershell
python -m lemon_factor.datasets.convert_bc5cdr `
  --source local `
  --raw-dir data/biomedical/raw/bc5cdr `
  --out-dir data/biomedical/processed `
  --manifest data/biomedical/manifests/bc5cdr_manifest.json
```

BC5CDR through HuggingFace converted Parquet, if the `datasets` package and network access are available:

```powershell
python -m lemon_factor.datasets.convert_bc5cdr `
  --source hf-parquet `
  --out-dir data/biomedical/processed `
  --manifest data/biomedical/manifests/bc5cdr_manifest.json `
  --limit 200
```

`--source bigbio` is retained only as a legacy alias. With `datasets>=4`, scripted datasets are no longer loaded through `trust_remote_code`, so the converter now routes that alias through the converted Parquet path and emits an actionable error if Parquet is unavailable.

ChemProt from local raw files:

```powershell
python -m lemon_factor.datasets.convert_chemprot `
  --raw-dir data/biomedical/raw/chemprot `
  --out-dir data/biomedical/processed `
  --manifest data/biomedical/manifests/chemprot_manifest.json `
  --keep-relations CPR:3 CPR:4 CPR:5 CPR:6 CPR:9
```

BioRED from local raw files:

```powershell
python -m lemon_factor.datasets.convert_biored `
  --raw-dir data/biomedical/raw/biored `
  --out-dir data/biomedical/processed `
  --manifest data/biomedical/manifests/biored_manifest.json
```

Dataset statistics:

```powershell
python -m lemon_factor.analysis.biomedical_dataset_stats `
  data/biomedical/processed/bc5cdr_train.jsonl `
  --out data/biomedical/reports/biomedical_dataset_stats.json `
  --table paper/tables/table_biomedical_dataset_stats.md
```

## Notes

This stage deliberately avoids metric claims. It only establishes cross-domain data feasibility and conversion reliability. ChemProt and BioRED access may require manually downloaded raw files; their converters are fixture-tested and local-ready. Missing raw directories now produce short actionable messages instead of Python tracebacks.
