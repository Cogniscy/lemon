# lemon-06.1 — OpenRouter model preflight and adjudicator debug config

## Goal

`lemon-06` added synthetic LLM adjudication, but the first live run produced no adjudicated decompositions because the configured adjudicator model returned HTTP 404. This stage prevents that class of failure before expensive runs.

## What changed

- Added `src/lemon_factor/llm/model_check.py`.
- Changed the default adjudicator config to a one-model debug config.
- Added separate adjudicator configs:
  - `configs/llm_adjudicator_debug.yaml`
  - `configs/llm_adjudicator_full.yaml`
- Kept synthetic adjudication explicitly marked as non-human reference.

## Why this matters for the method

LEMON-Factor needs a usable predicate-decomposition reference before graph-text coverage can be computed. A failed adjudicator run silently produces an empty synthetic reference, which would block `lemon-07`. Preflight checks make the LLM layer reproducible enough for development.

## Why this matters for the paper

The paper can state that LLM adjudication was run only after checking model availability. This supports reproducibility and explains why model IDs are configuration, not hardcoded method assumptions.

## Commands

Check the default debug adjudicator:

```powershell
python -m lemon_factor.llm.model_check `
  --models configs/llm_adjudicator_debug.yaml `
  --out data/reports/openrouter_adjudicator_debug_check.json
```

Run synthetic adjudication after preflight:

```powershell
python -m lemon_factor.llm.adjudicate_decompositions `
  --seed data/interim/webnlg_predicate_decompositions_seed.json `
  --llm data/interim/llm_predicate_decomposition_candidates.jsonl `
  --inventory data/interim/webnlg_factor_inventory.json `
  --models configs/llm_adjudicator_debug.yaml `
  --out data/interim/webnlg_predicate_decompositions_synthetic_adjudicated.json `
  --raw-out data/interim/llm_synthetic_adjudication_raw.jsonl `
  --review-out data/annotation/synthetic_adjudication_review.csv `
  --stats-out data/reports/synthetic_adjudication_stats.json `
  --table paper/tables/table_synthetic_adjudication_stats.md `
  --limit 30
```

## Acceptance criteria

- Unit tests pass without `OPENROUTER_API_KEY`.
- `model_check` reports unavailable model IDs before a live run.
- Default adjudicator config contains one debug model, not a stale full model.
- Synthetic adjudication produces `items > 0` before moving to `lemon-07`.

## Technical debt

- Add automatic `--run-name` output naming to avoid overwrites.
- Add retry/fallback routing when one adjudicator fails.
- Add stricter capability checks once OpenRouter catalog metadata is stable enough for this project.
