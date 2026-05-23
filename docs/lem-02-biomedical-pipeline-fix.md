# LEM-02: Biomedical data pipeline fix and stats

## Purpose

LEM-02 makes the biomedical data branch usable for the final paper.  It fixes
DrugProt text parsing, stabilizes direct-source conversion when raw archives are
already present, and adds conversion quality gates for DrugProt and BC5CDR.

## Scope

- DrugProt is the main biomedical transfer dataset because it contains multiple
  chemical--gene/protein relation predicates.
- BC5CDR is the secondary biomedical sanity check because it provides a robust
  document-level chemical-induced disease relation setting.
- This patch does not implement LEMON scoring for biomedical examples yet.  It
  prepares valid GraphText inputs and stats for the following experimental
  patches.

## Implementation notes

1. The DrugProt Gold Standard archive uses the official misspelled file name
   `drugprot_training_abstracs.tsv`.  The converter now accepts both
   `abstracts` and `abstracs` names.
2. `--source direct` now reuses already downloaded or extracted raw files before
   attempting network access.  This keeps local runs deterministic after the
   first acquisition.
3. A new `biomedical_quality` command checks non-empty text, edges, and predicate
   coverage.
4. The biomedical stats table now reports average text length and predicate type
   counts, which are needed to show that the second domain is valid.

## Commands

```powershell
cd D:\Projects\lemon

python -m pytest -q

python -m lemon_factor.datasets.convert_drugprot `
  --source direct `
  --download-dir data/biomedical/raw/drugprot `
  --out-dir data/biomedical/processed `
  --manifest data/biomedical/manifests/drugprot_manifest.json `
  --limit 500

python -m lemon_factor.datasets.convert_bc5cdr `
  --source direct `
  --download-dir data/biomedical/raw/bc5cdr `
  --out-dir data/biomedical/processed `
  --manifest data/biomedical/manifests/bc5cdr_manifest.json `
  --limit 500

python -m lemon_factor.datasets.biomedical_quality `
  data/biomedical/processed/drugprot_train.jsonl `
  --out data/biomedical/reports/drugprot_quality_check.json `
  --min-examples 500 `
  --min-edges 1 `
  --min-predicates 10

python -m lemon_factor.datasets.biomedical_quality `
  data/biomedical/processed/bc5cdr_train.jsonl `
  data/biomedical/processed/bc5cdr_dev.jsonl `
  --out data/biomedical/reports/bc5cdr_quality_check.json `
  --min-examples 500 `
  --min-edges 1 `
  --min-predicates 1

python -m lemon_factor.analysis.biomedical_dataset_stats `
  data/biomedical/processed/drugprot_train.jsonl `
  data/biomedical/processed/bc5cdr_train.jsonl `
  data/biomedical/processed/bc5cdr_dev.jsonl `
  --out data/biomedical/reports/biomedical_dataset_stats.json `
  --table paper/tables/table_biomedical_dataset_stats.md
```
