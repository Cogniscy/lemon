# lemon-06.2 — Synthetic adjudication quality fixes

## Goal

`lemon-06.1` made synthetic LLM adjudication runnable again by adding model preflight. This patch makes the resulting synthetic reference safer to use downstream by separating three cases:

- full LLM-assisted adjudication;
- partial LLM-assisted adjudication;
- seed-only fallback / missing LLM candidates.

The result is still a synthetic reference, not human gold.

## What changed

- `LLMAdjudicationDecision.confidence` is now optional.
- Missing confidence is preserved as `None` instead of being silently converted to `0.00`.
- Seed fallback decompositions are marked with `confidence_missing=true` and `fallback=true`.
- Synthetic adjudication statistics now include LLM candidate coverage.
- The markdown stats table now includes coverage and confidence diagnostics.
- The CLI warns when adjudication includes predicates without LLM candidates.

## Why this matters for the method

LEMON-Factor will use predicate decompositions as semantic references for graph-text coverage. If a synthetic reference mixes LLM-assisted decisions and seed-only fallback cases without marking them, the metric can look more reliable than it is. Coverage diagnostics make that distinction explicit.

## Why this matters for the paper

The paper can now report:

- number of synthetic adjudicated predicates;
- fraction with LLM candidates;
- number of seed-only fallback cases;
- missing confidence count;
- disagreement type distribution.

This supports a cautious claim: synthetic adjudication is a development bridge, while human validation remains future work.

## Commands

Run model preflight:

```powershell
python -m lemon_factor.llm.model_check `
  --models configs/llm_adjudicator_debug.yaml `
  --out data/reports/openrouter_adjudicator_debug_check.json
```

Run synthetic adjudication:

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

Inspect diagnostics:

```powershell
Get-Content data/reports/synthetic_adjudication_stats.json
Get-Content paper/tables/table_synthetic_adjudication_stats.md
```

## Acceptance criteria

- `python -m pytest` passes.
- Missing adjudicator confidence is not rendered as false `0.00`.
- `synthetic_adjudication_stats.json` contains `llm_candidate_coverage`.
- The markdown table contains coverage and confidence rows.
- The CLI warns when predicates lack LLM candidate decompositions.

## Notes

OpenRouter structured outputs should be requested with `response_format` and `type=json_schema` where the chosen model supports it. The model catalog preflight remains necessary because model availability and capabilities can change.
