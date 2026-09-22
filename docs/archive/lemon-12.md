# lemon-12 — LLM-judged MINE-style fact recoverability

## Goal

`lemon-12` brings the WebNLG MINE-style baseline closer to KGGen's Measure of Information in Nodes and Edges by adding an optional LLM judge over retrieved subgraphs.

The previous deterministic mode answers:

```text
Are the gold subject/object nodes and exact predicate edge present in the reconstructed graph?
```

The new LLM-judged mode answers:

```text
Given a gold fact and retrieved nodes/edges, can the fact be inferred from the retrieved subgraph?
```

This remains a WebNLG adaptation, not a full reproduction of KGGen MINE.

## New modules

```text
src/lemon_factor/mine_nodes_edges/judge_schema.py
src/lemon_factor/mine_nodes_edges/llm_judge.py
src/lemon_factor/mine_nodes_edges/prompts/judge_fact_recoverability.md
```

Updated modules:

```text
src/lemon_factor/mine_nodes_edges/scoring.py
src/lemon_factor/mine_nodes_edges/run_mine_style.py
src/lemon_factor/analysis/bidirectional_comparison.py
```

## Modes

```text
deterministic  node/edge hit scoring, no LLM
offline        read fixture judgments, no API key
llm            call OpenRouter with structured JSON schema
```

## Commands

### 1. OpenRouter model preflight

```powershell
python -m lemon_factor.llm.model_check `
  --models configs/llm_adjudicator_debug.yaml `
  --out data/reports/openrouter_mine_judge_check.json
```

### 2. Dry-run prompt generation

```powershell
python -m lemon_factor.mine_nodes_edges.run_mine_style `
  data/processed/webnlg_dev.jsonl `
  --reconstructed data/interim/webnlg_reconstructed_graphs_lexical.jsonl `
  --judge llm `
  --models configs/llm_adjudicator_debug.yaml `
  --prompts-out data/interim/mine_style_judge_prompts.jsonl `
  --dry-run `
  --limit 10 `
  --out data/reports/webnlg_mine_style_llm.json `
  --scores data/reports/webnlg_mine_style_llm_scores.jsonl `
  --table paper/tables/table_webnlg_mine_style_llm.md
```

### 3. Live LLM-judged MINE-style run

```powershell
python -m lemon_factor.mine_nodes_edges.run_mine_style `
  data/processed/webnlg_dev.jsonl `
  --reconstructed data/interim/webnlg_reconstructed_graphs_lexical.jsonl `
  --judge llm `
  --models configs/llm_adjudicator_debug.yaml `
  --out data/reports/webnlg_mine_style_llm.json `
  --scores data/reports/webnlg_mine_style_llm_scores.jsonl `
  --raw-out data/reports/webnlg_mine_style_llm_raw.jsonl `
  --table paper/tables/table_webnlg_mine_style_llm.md `
  --top-k 2 `
  --hops 2 `
  --limit 50
```

### 4. Updated bidirectional comparison

```powershell
python -m lemon_factor.analysis.bidirectional_comparison `
  --forward data/reports/webnlg_lemon_factor_coverage_expanded.json `
  --reverse data/reports/webnlg_reverse_lemon.json `
  --mine-style data/reports/webnlg_mine_style.json `
  --mine-style-llm data/reports/webnlg_mine_style_llm.json `
  --baseline data/reports/webnlg_baseline_comparison.json `
  --out data/reports/webnlg_bidirectional_comparison_llm.json `
  --table paper/tables/table_webnlg_bidirectional_comparison_llm.md
```

## Output fields

The LLM-judged report adds:

```text
judge_mode
judged_facts
judge_parse_success_rate
mean_judge_confidence
llm_judge=true
```

Each fact score adds:

```text
fact_id
judge_recoverable
judge_confidence
judge_reason
judge_evidence_nodes
judge_evidence_edges
```

## Interpretation

The deterministic MINE-style score is strict and surface-bound. The LLM-judged score can accept paraphrased relation evidence if the retrieved subgraph supports the fact. It should reject cases where the subject, object, or relation meaning is absent.

## Limitations

- The LLM judge is provisional and may be biased.
- This is not a human validation layer.
- The reconstructed graph is still deterministic and lexical.
- This is a WebNLG adaptation of MINE, not the original KGGen benchmark protocol.
- Full calibration requires controlled perturbation experiments planned for `lemon-13`.
