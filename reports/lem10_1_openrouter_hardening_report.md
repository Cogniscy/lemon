# LEM-10.1 OpenRouter runner hardening

This patch stabilizes the LLM reliability runner after pilot runs showed slow responses, empty OpenRouter content, malformed JSON, and misleading summaries caused by mock judgments being mixed with real judgments.

## Changes

- Default OpenRouter response mode changed to `json_schema`.
- Added optional fallback to `json_object` on retry.
- Added OpenRouter `response-healing` plugin by default.
- Added `stream: false` explicitly.
- Added `--require-parameters` for routing to providers that support structured outputs.
- Added progress bar on stderr.
- Added per-item report updates while the run is still active.
- Added `--raw-out` for raw success/failure logging.
- Added `--offset`, `--dataset`, `--variant`, `--shuffle`, and `--seed` for controlled partial runs.
- Added local JSON repair for common malformed outputs.
- Added support for dict-style decisions.
- Updated summarizer to exclude `mock_*` judgments by default.

## Smoke tests

```text
PYTHONPATH=/mnt/data/lem101work/src pytest -q \
  /mnt/data/lem101work/tests/test_openrouter_judge_runner.py \
  /mnt/data/lem101work/tests/test_llm_reliability_summarizer_filters.py

7 passed in 0.18s
```

## Recommended pilot command

```powershell
python -m lemon_factor.reliability.run_openrouter_judge `
  --prompts data/reliability/llm_probe_prompts.jsonl `
  --out reports/llm_judgments/gemini_flash_strict_pilot.jsonl `
  --model google/gemini-2.0-flash-001 `
  --judge-id gemini_flash_strict `
  --prompt-style no_rationale `
  --response-format json_schema `
  --fallback-response-format json_object `
  --require-parameters `
  --limit 15 `
  --timeout 45 `
  --max-retries 3 `
  --raw-out reports/llm_judgments/gemini_flash_strict_pilot_raw.jsonl `
  --report-out reports/llm_judgments/gemini_flash_strict_pilot_report.json
```

## Summary command

Mock judgments are excluded by default now.

```powershell
python -m lemon_factor.reliability.summarize_llm_probe `
  --items data/reliability/llm_probe_items.jsonl `
  --judgments reports/llm_judgments/*.jsonl `
  --out reports/llm_reliability_summary.json `
  --examples-out reports/llm_reliability_disagreements.md
```
