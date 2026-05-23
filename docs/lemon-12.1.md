# lemon-12.1 — Stable LLM-judged MINE-style evaluation

## Goal

`lemon-12.1` stabilizes the optional LLM-judged MINE-style WebNLG adaptation. It keeps the `Measure of Information in Nodes and Edges` framing, but adds stricter structured-output handling, fixed-subset comparison, and explicit parse/retry diagnostics.

The stage is still a WebNLG adaptation, not a full reproduction of KGGen's MINE benchmark.

## Changes

- compact judge prompt with a bounded reason field;
- bounded evidence lists and schema validation for short reasons;
- compact retrieved subgraph context via `--compact-context`;
- configurable `--max-tokens`, `--max-context-nodes`, `--max-context-edges`, and `--reason-max-words`;
- one retry with an ultra-compact prompt via `--retry-invalid-json`;
- fixed subset support via `--subset-out` and `--subset-in`;
- report diagnostics for requested/valid/failed judgments, retry attempts, retry successes, judge agreement, and deterministic score on the same subset.

## Commands

### 1. Preflight

```powershell
python -m lemon_factor.llm.model_check `
  --models configs/llm_adjudicator_debug.yaml `
  --out data/reports/openrouter_mine_judge_check.json
```

### 2. Lock a deterministic subset

```powershell
python -m lemon_factor.mine_nodes_edges.run_mine_style `
  data/processed/webnlg_dev.jsonl `
  --reconstructed data/interim/webnlg_reconstructed_graphs_lexical.jsonl `
  --judge deterministic `
  --out data/reports/webnlg_mine_style_subset_det.json `
  --scores data/reports/webnlg_mine_style_subset_det_scores.jsonl `
  --table paper/tables/table_webnlg_mine_style_subset_det.md `
  --subset-out data/interim/mine_style_eval_subset.json `
  --limit 50 `
  --top-k 2 `
  --hops 2
```

### 3. LLM judge on the same subset

```powershell
python -m lemon_factor.mine_nodes_edges.run_mine_style `
  data/processed/webnlg_dev.jsonl `
  --reconstructed data/interim/webnlg_reconstructed_graphs_lexical.jsonl `
  --judge llm `
  --models configs/llm_adjudicator_debug.yaml `
  --subset-in data/interim/mine_style_eval_subset.json `
  --out data/reports/webnlg_mine_style_llm_stable.json `
  --scores data/reports/webnlg_mine_style_llm_stable_scores.jsonl `
  --raw-out data/reports/webnlg_mine_style_llm_stable_raw.jsonl `
  --table paper/tables/table_webnlg_mine_style_llm_stable.md `
  --compact-context `
  --max-context-nodes 6 `
  --max-context-edges 6 `
  --reason-max-words 20 `
  --max-tokens 250 `
  --retry-invalid-json `
  --top-k 2 `
  --hops 2
```

### 4. Updated bidirectional comparison

```powershell
python -m lemon_factor.analysis.bidirectional_comparison `
  --forward data/reports/webnlg_lemon_factor_coverage_expanded.json `
  --reverse data/reports/webnlg_reverse_lemon.json `
  --mine-style data/reports/webnlg_mine_style.json `
  --mine-style-llm data/reports/webnlg_mine_style_llm_stable.json `
  --baseline data/reports/webnlg_baseline_comparison.json `
  --out data/reports/webnlg_bidirectional_comparison_llm_stable.json `
  --table paper/tables/table_webnlg_bidirectional_comparison_llm_stable.md
```

## Acceptance criteria

- Tests pass without an API key.
- Dry-run writes compact prompts.
- Deterministic and LLM-judged MINE-style are evaluated on the same locked subset.
- Live reports include parse success, retry, failure, and agreement diagnostics.
- The paper treats LLM-judged MINE-style as provisional and reports valid judgment coverage.
