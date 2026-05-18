# lemon-05 — Optional LLM candidate generator via OpenRouter

## Goal

Add an optional, model-agnostic LLM layer for generating candidate predicate decompositions. The deterministic seed schema from `lemon-04` remains the reference layer. LLM output is treated as candidate evidence only.

The research question for this stage is:

> Given a controlled factor schema and a fixed prompt, can different LLMs produce usable predicate decompositions with measurable agreement against a seed/expert reference?

## Why this matters for the article

This stage supports the scalability argument. `lemon-04` shows that decompositions can be built deterministically. `lemon-05` tests whether any LLM behind the same API can propose decompositions that are schema-valid and close to the reference.

This gives the article a model-agnostic claim:

> The LLM is not a source of truth. It is a replaceable candidate generator evaluated by parse success, schema validity, factor F1, role accuracy, and expert acceptance.

## Inputs

```text
data/interim/webnlg_factor_inventory.json
data/interim/factor_schema_seed.json
data/interim/webnlg_predicate_decompositions_seed.json
configs/llm_models.yaml
```

## Outputs

```text
data/interim/llm_predicate_decomposition_prompts.jsonl
data/interim/llm_predicate_decomposition_candidates.jsonl
data/interim/llm_raw_responses.jsonl
data/reports/llm_decomposition_eval.json
data/annotation/llm_decomposition_review.csv
paper/tables/table_llm_decomposition_eval.md
```

## Commands

Dry run. This requires no API key and writes the prompts/payloads only:

```powershell
python -m lemon_factor.llm.decompose_predicates `
  data/interim/webnlg_factor_inventory.json `
  --factor-schema data/interim/factor_schema_seed.json `
  --models configs/llm_models.yaml `
  --limit 10 `
  --dry-run
```

Live run through OpenRouter:

```powershell
$env:OPENROUTER_API_KEY="..."
python -m lemon_factor.llm.decompose_predicates `
  data/interim/webnlg_factor_inventory.json `
  --factor-schema data/interim/factor_schema_seed.json `
  --models configs/llm_models.yaml `
  --out data/interim/llm_predicate_decomposition_candidates.jsonl `
  --raw-out data/interim/llm_raw_responses.jsonl `
  --limit 50
```

Evaluate LLM candidates against the deterministic seed reference:

```powershell
python -m lemon_factor.llm.evaluate_decompositions `
  data/interim/llm_predicate_decomposition_candidates.jsonl `
  data/interim/webnlg_predicate_decompositions_seed.json `
  --out data/reports/llm_decomposition_eval.json `
  --table paper/tables/table_llm_decomposition_eval.md `
  --review-out data/annotation/llm_decomposition_review.csv
```

Offline fixture mode for tests and reproducible examples:

```powershell
python -m lemon_factor.llm.decompose_predicates `
  data/interim/webnlg_factor_inventory.json `
  --factor-schema data/interim/factor_schema_seed.json `
  --offline-fixture path/to/fixture.jsonl
```

## Metrics

For each model:

- parse success rate;
- schema validity rate;
- factor precision;
- factor recall;
- factor F1;
- role accuracy;
- weight MAE;
- expert acceptance rate after manual review.

The current evaluator assumes candidates are already parseable and schema-valid. Parse/schema failures are preserved in `llm_raw_responses.jsonl` and can be summarized separately in a later patch.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Model returns non-JSON | use structured output payload; save raw response; validate with Pydantic |
| Model invents factors | validate against `factor_schema_seed.json` |
| API key leakage | key is read from env only and never stored in payloads |
| Non-reproducibility | temperature=0; fixed prompt; raw response audit log |
| Model ids change | model list is externalized in `configs/llm_models.yaml` |
| Seed reference is not gold | call it seed/reference; export expert review CSV |
| Cost | `--limit`, dry-run mode, offline fixtures |



## Debug model policy

During development, the default model list is intentionally short:

```text
configs/llm_models.yaml        # one-model debug run
configs/llm_models_debug.yaml  # explicit one-model debug run
configs/llm_models_sanity.yaml # two-model sanity comparison
configs/llm_models_full.yaml   # final multi-model comparison
```

The default debug model is `meta-llama/llama-3.1-70b-instruct`, because the first pilot run produced the highest valid-candidate rate among the tested models. Use the full config only when collecting final comparative results for the paper.

Recommended development command:

```powershell
python -m lemon_factor.llm.decompose_predicates `
  data/interim/webnlg_factor_inventory.json `
  --factor-schema data/interim/factor_schema_seed.json `
  --models configs/llm_models.yaml `
  --out data/interim/llm_predicate_decomposition_candidates.jsonl `
  --raw-out data/interim/llm_raw_responses.jsonl `
  --limit 10
```

Recommended final-results command:

```powershell
python -m lemon_factor.llm.decompose_predicates `
  data/interim/webnlg_factor_inventory.json `
  --factor-schema data/interim/factor_schema_seed.json `
  --models configs/llm_models_full.yaml `
  --out data/interim/llm_predicate_decomposition_candidates.jsonl `
  --raw-out data/interim/llm_raw_responses.jsonl `
  --limit 50
```


## Acceptance criteria

- `python -m pytest` passes without `OPENROUTER_API_KEY`.
- Dry-run creates prompt/payload records.
- Offline fixture mode validates candidates and raw records.
- Live mode works if `OPENROUTER_API_KEY` is available.
- Evaluation produces JSON, Markdown table, and expert-review CSV.
- Documentation clearly states that LLM output is candidate evidence, not ground truth.
