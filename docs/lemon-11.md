# lemon-11 — Bidirectional LEMON and MINE-style node/edge baseline

## Goal

`lemon-11` extends the project from one-directional KG→Text coverage to a bidirectional graph-text alignment pilot:

```text
Gold KG → Text → forward LEMON-Factor coverage
Text → reconstructed KG → reverse LEMON-Factor coverage
Text → reconstructed KG → MINE-style node/edge information retention
```

The MINE-style baseline is inspired by KGGen's **Measure of Information in Nodes and Edges**. This implementation is a deterministic WebNLG adaptation, not a full reproduction of KGGen MINE. It does not use an LLM judge yet.

## New modules

```text
src/lemon_factor/reverse/reconstruct_graph.py
src/lemon_factor/reverse/reverse_coverage.py
src/lemon_factor/reverse/run_reverse_lemon.py
src/lemon_factor/mine_nodes_edges/retrieval.py
src/lemon_factor/mine_nodes_edges/scoring.py
src/lemon_factor/mine_nodes_edges/run_mine_style.py
src/lemon_factor/analysis/bidirectional_comparison.py
```

## Reconstruction modes

```text
lexical       recover nodes from entity-label evidence and edges from predicate lexical cues
oracle_nodes  recover all nodes, but require predicate lexical cues for edges
oracle_edges  recover all gold nodes and edges; ceiling mode
```

Use `lexical` for the default experiment.

## Commands

### 1. Reconstruct text-to-KG graphs

```powershell
python -m lemon_factor.reverse.reconstruct_graph `
  data/processed/webnlg_dev.jsonl `
  --lexical-cues data/interim/webnlg_lexical_cues_expanded.json `
  --mode lexical `
  --out data/interim/webnlg_reconstructed_graphs_lexical.jsonl `
  --report data/reports/webnlg_reconstruction_lexical.json
```

### 2. Run reverse LEMON-Factor

```powershell
python -m lemon_factor.reverse.run_reverse_lemon `
  data/processed/webnlg_dev.jsonl `
  --reconstructed data/interim/webnlg_reconstructed_graphs_lexical.jsonl `
  --decompositions data/interim/webnlg_predicate_decompositions_expanded.json `
  --out data/reports/webnlg_reverse_lemon.json `
  --details data/reports/webnlg_reverse_lemon_details.jsonl `
  --table paper/tables/table_webnlg_reverse_lemon.md
```

### 3. Run deterministic MINE-style baseline

```powershell
python -m lemon_factor.mine_nodes_edges.run_mine_style `
  data/processed/webnlg_dev.jsonl `
  --reconstructed data/interim/webnlg_reconstructed_graphs_lexical.jsonl `
  --out data/reports/webnlg_mine_style.json `
  --scores data/reports/webnlg_mine_style_scores.jsonl `
  --table paper/tables/table_webnlg_mine_style.md `
  --top-k 2 `
  --hops 2
```

### 4. Build bidirectional comparison table

```powershell
python -m lemon_factor.analysis.bidirectional_comparison `
  --forward data/reports/webnlg_lemon_factor_coverage_expanded.json `
  --reverse data/reports/webnlg_reverse_lemon.json `
  --mine-style data/reports/webnlg_mine_style.json `
  --baseline data/reports/webnlg_baseline_comparison.json `
  --out data/reports/webnlg_bidirectional_comparison.json `
  --table paper/tables/table_webnlg_bidirectional_comparison.md
```

## Pilot results

On the WebNLG dev pilot with lexical reconstruction:

```text
recovered_nodes = 390 / 408
recovered_edges = 196 / 308
reverse_lemon_coverage = 0.778896
mine_style_score = 0.802760
forward_lemon_expanded = 0.791476
```

## Interpretation

Forward and reverse LEMON use the same predicate-factor schema and produce factor/edge/example/corpus diagnostics. MINE-style node/edge scoring measures information retained in reconstructed graphs via node and edge hits. The two methods are complementary: MINE-style scoring answers whether facts are recoverable from reconstructed nodes/edges; reverse LEMON answers which role-aware predicate factors were retained.

## Limitations

- This is a deterministic WebNLG adaptation of MINE, not full KGGen MINE.
- There is no LLM binary judge in this patch.
- The reconstructed graph is a weak lexical pseudo-extractor, not a full text-to-KG extractor.
- WebNLG texts are short controlled verbalizations; KGGen evaluates longer plain-text articles.

## Acceptance criteria

- Tests pass.
- Reconstructed graph JSONL is created.
- Reverse LEMON report/details/table are created.
- MINE-style report/scores/table are created.
- Bidirectional comparison JSON/table are created.
- Paper text can describe bidirectional graph-text semantic alignment.
