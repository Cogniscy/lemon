# lemon-06 — Synthetic LLM adjudication reference

## Goal

Create a temporary synthetic adjudicated predicate-decomposition reference when no human expert is available yet.

This stage combines:

```text
seed predicate decompositions
+ LLM-generated decomposition candidates
+ inventory evidence
+ strong-LLM adjudication
→ synthetic adjudicated reference
```

The output is **not** a human gold standard. It is an intermediate reference for developing and debugging LEMON-Factor before expert validation.

## Why this stage exists

`lemon-05` showed that LLM candidates can reach useful agreement with the seed reference, but the seed reference itself is rule-based and may contain questionable choices. A stronger LLM adjudicator can triage disagreements and produce a temporary synthetic reference.

This lets us continue toward `lemon-07` graph-text coverage while preserving a clear limitation: human adjudication remains future work.

## Commands

Dry-run prompt generation:

```powershell
python -m lemon_factor.llm.adjudicate_decompositions `
  --seed data/interim/webnlg_predicate_decompositions_seed.json `
  --llm data/interim/llm_predicate_decomposition_candidates.jsonl `
  --inventory data/interim/webnlg_factor_inventory.json `
  --models configs/llm_adjudicator.yaml `
  --limit 20 `
  --dry-run
```

Live synthetic adjudication via OpenRouter:

```powershell
$env:OPENROUTER_API_KEY="..."

python -m lemon_factor.llm.adjudicate_decompositions `
  --seed data/interim/webnlg_predicate_decompositions_seed.json `
  --llm data/interim/llm_predicate_decomposition_candidates.jsonl `
  --inventory data/interim/webnlg_factor_inventory.json `
  --models configs/llm_adjudicator.yaml `
  --out data/interim/webnlg_predicate_decompositions_synthetic_adjudicated.json `
  --raw-out data/interim/llm_synthetic_adjudication_raw.jsonl `
  --review-out data/annotation/synthetic_adjudication_review.csv `
  --stats-out data/reports/synthetic_adjudication_stats.json `
  --table paper/tables/table_synthetic_adjudication_stats.md `
  --limit 30
```

No-network fallback for testing downstream code:

```powershell
python -m lemon_factor.llm.adjudicate_decompositions `
  --seed data/interim/webnlg_predicate_decompositions_seed.json `
  --llm data/interim/llm_predicate_decomposition_candidates.jsonl `
  --inventory data/interim/webnlg_factor_inventory.json `
  --seed-fallback `
  --limit 30
```

Evaluate LLM candidates against the synthetic adjudicated reference:

```powershell
python -m lemon_factor.llm.evaluate_decompositions `
  data/interim/llm_predicate_decomposition_candidates.jsonl `
  data/interim/webnlg_predicate_decompositions_synthetic_adjudicated.json `
  --out data/reports/llm_decomposition_eval_synthetic_adjudicated.json `
  --table paper/tables/table_llm_decomposition_eval_synthetic_adjudicated.md `
  --review-out data/annotation/llm_decomposition_review_synthetic_adjudicated.csv
```

## Outputs

```text
data/interim/webnlg_predicate_decompositions_synthetic_adjudicated.json
data/interim/llm_synthetic_adjudication_raw.jsonl
data/annotation/synthetic_adjudication_review.csv
data/reports/synthetic_adjudication_stats.json
paper/tables/table_synthetic_adjudication_stats.md
```

## Method contribution

This stage adds a third reference layer:

```text
seed reference → rule-based, deterministic
LLM candidates → model-generated alternatives
synthetic adjudicated reference → strong-LLM temporary calibration
```

It helps separate errors caused by weak seed rules from errors caused by LLM candidate generation.

## Paper contribution

The paper can report a pilot result as:

> In the absence of human experts, we use a stronger LLM as a temporary synthetic adjudicator. The resulting reference is used only for development and is explicitly not treated as human gold.

This is more honest than silently treating rule-based seed decompositions as gold.

## Risks

| Risk | Mitigation |
|---|---|
| LLM adjudicator bias | Mark output as synthetic and keep raw responses |
| Circular LLM evaluation | Use a stronger/separate adjudicator model; report limitation |
| Invalid JSON | JSON Schema response format + Pydantic validation |
| Invalid factors/roles | Validate against factor schema |
| No API key | Dry-run and seed-fallback modes remain available |
| Human validation absent | Human expert review remains explicit future work |

## Acceptance criteria

1. `pytest` passes without `OPENROUTER_API_KEY`.
2. Dry-run creates adjudication prompts.
3. Offline fixture and seed fallback create valid synthetic references.
4. Live mode can create `webnlg_predicate_decompositions_synthetic_adjudicated.json` when a key is present.
5. Synthetic outputs include a warning that they are not human gold.
6. The synthetic reference can be used by the existing LLM evaluator.
