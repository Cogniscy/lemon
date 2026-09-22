# Proposed CI-only branch

Status: publication and subsequent merge approved by the user; blocked by GitHub write access (HTTP 403).

Base: 723077d07ce00baf8aee00dd73fd500358052716 (current remote master when inspected).
Suggested branch: validation/package-and-ci-20260922.
Merge into the default branch `master` after successful remote CI is authorized.
The repository currently has no default branch named `main`.

Includes code, tests, dependencies and CI. Excludes manuscript edits, documentation archival,
local datasets, historical reports, PDFs and generated metadata.
Validated against the original repository plus these changes: 232 passed,
3 artifact checks deselected, 2 expected failures on Windows Python 3.11.

## Files

- `.github/workflows/ci.yml`
- `constraints/demo-windows-py311.txt`
- `constraints/deterministic-windows-py311.txt`
- `pyproject.toml`
- `scripts/build_metric_radar.ps1`
- `scripts/make_radar_profile.py`
- `scripts/recompute_paper_aggregates.ps1`
- `scripts/reproduce_local_research.py`
- `scripts/run_embedding_baseline.py`
- `scripts/smoke_installed.py`
- `src/lemon_factor/__main__.py`
- `src/lemon_factor/analysis/metric_radar.py`
- `src/lemon_factor/analysis/recompute_paper_aggregates.py`
- `src/lemon_factor/cli.py`
- `src/lemon_factor/demo.py`
- `src/lemon_factor/demo_data/cases.json`
- `src/lemon_factor/scoring/ablate.py`
- `src/lemon_factor/scoring/aggregate.py`
- `src/lemon_factor/scoring/baselines.py`
- `src/lemon_factor/scoring/report_schema.py`
- `src/lemon_factor/scoring/score_perturbations.py`
- `tests/conftest.py`
- `tests/test_demo.py`
- `tests/test_embedding_baseline_report.py`
- `tests/test_layer_profile_values.py`
- `tests/test_mine1_like.py`
- `tests/test_paper_draft_artifacts.py`
- `tests/test_radar_profile_values.py`
- `tests/test_recompute_paper_aggregates.py`
- `tests/test_report_schema.py`
- `tests/test_reproduce_local_research.py`
- `tests/test_scoring_ablation.py`
- `tests/test_scoring_perturbations.py`

## Final local implementation, 2026-09-23

The reduced request was retried and again returned HTTP 403. HTTPS Git also lacks
credentials. No remote branch or workflow was created.

The complete implementation, including expert-review reproduction, Apache-2.0,
RSF project 26-11-00193 acknowledgment and manuscript corrections, is prepared on
local branch `improvement/reproducible-repository`. Full local tests: 239 passed,
2 expected failures. Clean snapshot: 236 passed, 3 artifact tests deselected,
2 expected failures. Build and installed-wheel smoke checks pass.

Once Git write access works, push this branch, open a pull request against `master`,
and merge after all four CI matrix jobs pass. Local master remains at the original
base until remote validation. The earlier file list describes the reduced request,
not the complete local branch.
