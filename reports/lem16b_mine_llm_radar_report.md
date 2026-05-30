# LEM-16B: MINE-compatible LLM judging and radar comparison

This patch upgrades the local MINE-compatible baseline from a deterministic lexical smoke test to a two-stage MINE-1-compatible workflow:

1. prepare retrieval contexts and JSON-schema judge prompts;
2. optionally run OpenRouter LLM judging;
3. score saved binary judgments with the same MINE-1 mean-decision formula;
4. build a radar-comparison data file and TikZ figure for LEMON-Factor, MINE-1-compatible recoverability, and Triple-F1.

The patch does **not** claim a full reproduction of KGGen/MINE. It supports the safer wording: `MINE-1-compatible recoverability baseline`. A full statement about replication requires running the public KGGen/MINE scripts on a small official subset and comparing the score/logs.

## Local checks

```text
PYTHONPATH=src pytest -q tests/test_mine1_like.py
10 passed

prepare_llm_judge: passed, 5 prompts
run_openrouter_judge --dry-run: passed, 5 judgments
score --mode llm_saved: passed
metric_radar: passed
inspect_external: missing_checkout in sandbox
```

## Main local commands

```powershell
cd D:\Projects\lemon
python -m pytest -q

python -m lemon_factor.baselines.mine1_like.prepare_llm_judge `
  --items data/mine_probe/lemon_mine_items.jsonl `
  --out data/mine_probe/mine1_like_llm_prompts.jsonl `
  --model google/gemini-2.0-flash-001 `
  --judge-id mine1_like_llm

python -m lemon_factor.baselines.mine1_like.run_openrouter_judge `
  --prompts data/mine_probe/mine1_like_llm_prompts.jsonl `
  --out reports/mine1_like_llm_judgments.jsonl

python -m lemon_factor.baselines.mine1_like.score `
  --items data/mine_probe/lemon_mine_items.jsonl `
  --mode llm_saved `
  --judgments reports/mine1_like_llm_judgments.jsonl `
  --out reports/mine1_like_llm_lemon_pilot.json `
  --scores-out reports/mine1_like_llm_lemon_pilot_scores.jsonl

python -m lemon_factor.analysis.metric_radar `
  --scoring reports/scoring_webnlg.json reports/scoring_drugprot.json reports/scoring_bc5cdr.json `
  --mine reports/mine1_like_lemon_pilot.json `
  --triple reports/triple_f1_baseline.json `
  --out reports/metric_radar_comparison.json `
  --tex-out paper/figures/figure_metric_radar.tex
```

## Recommended article wording

Use:

> We include a MINE-1-compatible recoverability baseline that follows the MINE evaluation shape: fact retrieval, two-hop subgraph expansion, and binary recoverability judging.

Avoid:

> We reproduce MINE.
