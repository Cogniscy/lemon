# LEM-09 LLM reliability probe

This patch adds infrastructure for an exploratory LLM reliability probe. It does not call an LLM directly and does not change the main paper results.

The probe samples controlled perturbation items from WebNLG, DrugProt, and BC5CDR. External judges receive the source edge, the fixed LEMON factor decomposition, the original text, and the perturbed text. Judges return JSON-only factor decisions: `covered`, `partial`, or `absent`.

The summarizer reports mean LLM factor score, pairwise judge agreement, and agreement with the deterministic perturbation expectation. The outputs are intended for `reports/` first. They should enter the paper only if they clarify the claims without replacing human validation.

Recommended use:

```powershell
python -m lemon_factor.reliability.prepare_llm_probe `
  --inputs data/processed/webnlg_perturbed.jsonl data/biomedical/perturbed/drugprot_perturbed.jsonl data/biomedical/perturbed/bc5cdr_perturbed.jsonl `
  --inventories resources/factors/webnlg.json resources/factors/drugprot.json resources/factors/bc5cdr.json `
  --out data/reliability/llm_probe_items.jsonl `
  --prompt-out data/reliability/llm_probe_prompts.jsonl `
  --per-dataset 50

python -m lemon_factor.reliability.summarize_llm_probe `
  --items data/reliability/llm_probe_items.jsonl `
  --judgments reports/llm_judgments/*.jsonl `
  --out reports/llm_reliability_summary.json `
  --examples-out reports/llm_reliability_disagreements.md
```

Offline pipeline test:

```powershell
python -m lemon_factor.reliability.mock_judgments `
  --items data/reliability/llm_probe_items.jsonl `
  --out reports/llm_judgments/mock_strict.jsonl `
  --judge-id mock_strict
```
