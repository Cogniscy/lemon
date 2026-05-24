# LEM-09 test results

## Checks

```text
python -m pytest -q -> 192 passed
prepare_llm_probe -> passed, 30 items for offline smoke test
mock_judgments -> passed, 60 judgments from two mock judges
summarize_llm_probe -> passed
```

## Offline smoke-test summary

| Dataset | Variant | Mean mock score | Pairwise agreement | Deterministic agreement | Votes |
|---|---|---:|---:|---:|---:|
| bc5cdr | argument_swap | 0.6250 | 0.5 | 0.75 | 24 |
| bc5cdr | edge_deletion | 0.7500 | 0.6667 | 0.8333 | 24 |
| bc5cdr | node_deletion | 0.7500 | 0.6667 | 0.8333 | 24 |
| bc5cdr | polarity_flip | 0.7500 | 0.6667 | 0.8333 | 24 |
| bc5cdr | relation_blur | 0.7917 | 0.8333 | 0.9167 | 24 |
| drugprot | argument_swap | 0.6250 | 0.5 | 0.75 | 24 |
| drugprot | edge_deletion | 0.7500 | 0.6667 | 0.8333 | 24 |
| drugprot | node_deletion | 0.7500 | 0.6667 | 0.8333 | 24 |
| drugprot | polarity_flip | 0.8750 | 0.8333 | 0.9167 | 24 |
| drugprot | relation_blur | 0.7917 | 0.8333 | 0.9167 | 24 |
| webnlg | argument_swap | 0.6786 | 0.5833 | 0.7857 | 14 |
| webnlg | edge_deletion | 0.7500 | 0.6667 | 0.8333 | 12 |
| webnlg | node_deletion | 0.5000 | 0.3333 | 0.6667 | 12 |
| webnlg | polarity_flip | 0.7500 | 0.6667 | 0.8333 | 12 |
| webnlg | relation_blur | 0.8333 | 1.0 | 1.0 | 12 |

These are mock judgments only. They validate the reliability pipeline but must not be reported as LLM results. External judge outputs should be saved under `reports/llm_judgments/` and summarized with `summarize_llm_probe`.