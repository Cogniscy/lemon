# lemon-08 — Decomposition coverage expansion and error analysis

## Goal

`lemon-08` turns the first LEMON-Factor coverage baseline into an error-driven improvement loop. `lemon-07` showed that the metric works, but a large share of WebNLG dev edges could not be scored because their predicates had no factor decompositions. This stage detects those predicates, expands the decomposition and lexical cue dictionaries, reruns coverage, and reports the before/after delta.

## Method contribution

The stage demonstrates that LEMON-Factor is not just a scalar score. It is a diagnostic metric:

1. coverage results expose missing decompositions;
2. missing predicates drive dictionary expansion;
3. expanded decompositions/cues increase scored-edge coverage;
4. low-coverage edges are categorized into interpretable error types.

## Paper contribution

This stage supports a Results subsection on error-driven expansion:

- Table: top missing predicates;
- Table: LEMON-Factor before/after expansion;
- Table: low-coverage error types.

Suggested claim:

> Error-driven expansion of predicate decompositions reduced missing-edge rate and improved factor-level graph–text coverage while preserving interpretability.

## Commands

Analyze missing predicates:

```powershell
python -m lemon_factor.coverage.missing_analysis `
  data/reports/webnlg_lemon_factor_coverage_details.jsonl `
  --examples data/processed/webnlg_dev.jsonl `
  --out data/reports/webnlg_missing_predicates.json `
  --table paper/tables/table_webnlg_missing_predicates.md
```

Expand decompositions:

```powershell
python -m lemon_factor.factors.expand_decompositions `
  --missing data/reports/webnlg_missing_predicates.json `
  --base data/interim/webnlg_predicate_decompositions_synthetic_adjudicated.json `
  --inventory data/interim/webnlg_factor_inventory.json `
  --out data/interim/webnlg_predicate_decompositions_expanded.json
```

Expand lexical cues:

```powershell
python -m lemon_factor.coverage.expand_lexical_cues `
  --missing data/reports/webnlg_missing_predicates.json `
  --base-cues data/interim/webnlg_lexical_cues_seed.json `
  --out data/interim/webnlg_lexical_cues_expanded.json
```

Rerun coverage and write delta table:

```powershell
python -m lemon_factor.coverage.run_coverage_delta `
  data/processed/webnlg_dev.jsonl `
  --before data/reports/webnlg_lemon_factor_coverage.json `
  --expanded-decompositions data/interim/webnlg_predicate_decompositions_expanded.json `
  --expanded-lexical-cues data/interim/webnlg_lexical_cues_expanded.json `
  --out data/reports/webnlg_lemon_factor_coverage_expanded.json `
  --details data/reports/webnlg_lemon_factor_coverage_expanded_details.jsonl `
  --table paper/tables/table_webnlg_coverage_delta.md
```

Analyze errors:

```powershell
python -m lemon_factor.coverage.error_analysis `
  data/reports/webnlg_lemon_factor_coverage_expanded_details.jsonl `
  --out data/reports/webnlg_coverage_error_analysis.json `
  --table paper/tables/table_webnlg_coverage_error_types.md
```

## Limitations

This is still a deterministic lexical baseline. Expansion rules are reproducible, but they are not a replacement for human validation or robust paraphrase detection. The expected next step is a baseline comparison against exact overlap and embedding similarity.

## Acceptance criteria

1. `pytest` passes.
2. Missing predicate report and table are created.
3. Expanded decomposition and lexical cue files are created.
4. Coverage can be rerun with expanded resources.
5. The delta table shows before/after metric changes.
6. Error analysis produces interpretable low-coverage categories.
