# LEM-18 Layer/Profile and Build Hygiene Report

## Goal

Add a compact semantic layer/profile view to the SPECOM paper and prepare a checked numeric source for the future radar/spider figure, without adding the embedding baseline yet.

## Changed files

- `paper/sections/06_results.tex`
- `paper/tables/table_layer_profile.tex`
- `reports/layer_profile_values.json`
- `docs/CLAIMS_AND_METRICS_AUDIT.md`
- `tests/test_layer_profile_values.py`
- `reports/lem18_layer_profile_build_hygiene_report.md`
- `paper/main.pdf` after recompilation

## What changed

1. Added a compact layer table that maps the current factor schema to diagnostic layers:
   - entity/domain;
   - predicate cue;
   - role/argument;
   - direction;
   - polarity;
   - evidence/recoverability.
2. Inserted the table before the cross-domain perturbation summary to clarify what LEMON-Factor can and cannot diagnose.
3. Added `reports/layer_profile_values.json` as a numeric source file for the future radar figure.
4. Updated the claims audit with safe wording for the future radar/profile figure.
5. Added tests that check the layer-profile JSON and confirm that the paper includes the layer-profile table.

## Numeric sources for future radar

The new JSON intentionally records values as diagnostic properties, not absolute accuracy:

- node deletion sensitivity: LEMON-full mean drop from `reports/paper_metric_sensitivity_drops.json`;
- predicate-cue sensitivity: LEMON-full mean drop under edge deletion;
- role/argument sensitivity: LEMON-full mean drop under argument swap;
- polarity sensitivity: LEMON-full mean drop under polarity flip, with the inventory-dependent caveat;
- relation-blur sensitivity: LEMON-full mean drop under relation blur;
- role ablation gain: full-vs-minus-roles gain from `reports/paper_ablation_gain.json`;
- determinism: legacy radar determinism value from `reports/metric_radar_comparison.json`.

## Build hygiene notes

The user-side Windows log showed successful pytest but an initial LaTeX pass with undefined citations/references. A repeated `latexmk` run resolves cross-references in the generated `main.log`; the final log has no undefined citation/reference warnings. Remaining issues are layout warnings only.

## Verification

- `python -m pytest -q`: 214 passed.
- `cd paper && latexmk -pdf -interaction=nonstopmode main.tex`: success.
- `paper/main.pdf`: 15 pages.
- PDF render verification: 15 pages rendered successfully with `render_pdf.py` at 150 dpi.

## Deferred

- No embedding baseline.
- No radar figure yet.
- No new LLM calls.
- No expert validation results.
- No changes to metric implementation.
