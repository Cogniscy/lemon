# LEM-10 OpenRouter judge runner

This patch adds an OpenRouter-backed runner for the LEMON-Factor LLM reliability probe. The runner reads prompt payloads prepared by `prepare_llm_probe`, sends them to one OpenRouter model, validates JSON judgments, and writes schema-valid JSONL records for `summarize_llm_probe`.

The runner is separate from deterministic LEMON scoring. It is intended for reliability analysis only.

## Main command

```powershell
python -m lemon_factor.reliability.run_openrouter_judge `
  --prompts data/reliability/llm_probe_prompts.jsonl `
  --out reports/llm_judgments/openrouter_strict.jsonl `
  --model openrouter/auto `
  --judge-id openrouter_auto_strict `
  --prompt-style strict `
  --response-format json_object `
  --report-out reports/llm_judgments/openrouter_strict_report.json
```

## Second prompt condition

```powershell
python -m lemon_factor.reliability.run_openrouter_judge `
  --prompts data/reliability/llm_probe_prompts.jsonl `
  --out reports/llm_judgments/openrouter_no_rationale.jsonl `
  --model openrouter/auto `
  --judge-id openrouter_auto_no_rationale `
  --prompt-style no_rationale `
  --response-format json_object `
  --report-out reports/llm_judgments/openrouter_no_rationale_report.json
```

## Safety check before paid calls

```powershell
python -m lemon_factor.reliability.run_openrouter_judge `
  --prompts data/reliability/llm_probe_prompts.jsonl `
  --out reports/llm_judgments/openrouter_dry_run.jsonl `
  --model openrouter/auto `
  --judge-id dry_run `
  --dry-run `
  --limit 1 `
  --report-out reports/llm_judgments/openrouter_dry_run_report.json
```

## Summarize judgments

```powershell
python -m lemon_factor.reliability.summarize_llm_probe `
  --items data/reliability/llm_probe_items.jsonl `
  --judgments reports/llm_judgments/*.jsonl `
  --out reports/llm_reliability_summary.json `
  --examples-out reports/llm_reliability_disagreements.md
```
