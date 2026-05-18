# lemon-05 pilot run analysis

Input: `data_05.zip` pilot results supplied after the first live OpenRouter run.

## Summary

The first multi-model run attempted 50 predicates across 5 configured models: 250 raw calls.

| Model | Raw calls | Valid candidates | Valid rate | Factor F1 | Role accuracy | Weight MAE | Main issue |
|---|---:|---:|---:|---:|---:|---:|---|
| `meta-llama/llama-3.1-70b-instruct` | 50 | 49 | 0.98 | 0.575 | 0.408 | 0.245 | 1 schema-role validation error |
| `anthropic/claude-3.5-haiku` | 50 | 44 | 0.88 | 0.552 | 0.394 | 0.201 | JSON/schema-role validation errors |
| `openai/gpt-4o-mini` | 50 | 0 | 0.00 | — | — | — | HTTP 400 for all calls |
| `google/gemini-flash-1.5` | 50 | 0 | 0.00 | — | — | — | HTTP 404 for all calls |
| `mistralai/mistral-small` | 50 | 0 | 0.00 | — | — | — | HTTP 404 for all calls |

## Interpretation

The model-agnostic protocol works: two models produced schema-valid candidates and can be compared with the same metrics.

For development, the initial 5-model config is too noisy and expensive. Three model identifiers failed before candidate validation, likely due to stale model IDs or unsupported request parameters. OpenRouter model availability should be checked before final collection.

## Decision

The default debug config is reduced to one validated model:

```text
configs/llm_models.yaml
  - meta-llama/llama-3.1-70b-instruct
```

Additional configs:

```text
configs/llm_models_debug.yaml  # one-model debug
configs/llm_models_sanity.yaml # two-model sanity check
configs/llm_models_full.yaml   # final multi-model comparison
```

## Next actions

1. Use `configs/llm_models.yaml` for iterative debugging.
2. Use `configs/llm_models_sanity.yaml` before final collection to verify cross-model comparison still works.
3. Before using `configs/llm_models_full.yaml`, validate model IDs against OpenRouter's model list.
4. Add a preflight model check in a later patch.
