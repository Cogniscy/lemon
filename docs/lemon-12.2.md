# lemon-12.2 — MINE-style score semantics cleanup

`lemon-12.2` clarifies the difference between two MINE-style quantities that were previously easy to compare incorrectly:

- **Composite node/edge score**: partial-credit information-retention score, computed from node information and edge information.
- **Fact recoverability**: binary fact-level decision, used by the LLM judge over a retrieved subgraph.

The patch keeps backward-compatible fields (`mine_style_score`, `fact_recoverability`) and adds explicit fields:

```text
composite_node_edge_score
deterministic_fact_recoverability
llm_fact_recoverability
deterministic_node_information_on_subset
deterministic_edge_information_on_subset
deterministic_fact_recoverability_on_subset
```

The bidirectional comparison now labels deterministic MINE as **MINE-style composite node/edge** and LLM-judged MINE as **MINE-style LLM fact recoverability**. This avoids placing the deterministic composite score and LLM binary score side by side as if they were the same metric.

## Fixed-subset comparison

When a stable LLM-judged report is provided, the comparison CLI can also write a dedicated fixed-subset table:

```bash
python -m lemon_factor.analysis.bidirectional_comparison \
  --forward data/reports/webnlg_lemon_factor_coverage_expanded.json \
  --reverse data/reports/webnlg_reverse_lemon.json \
  --mine-style data/reports/webnlg_mine_style.json \
  --mine-style-llm data/reports/webnlg_mine_style_llm_stable.json \
  --baseline data/reports/webnlg_baseline_comparison.json \
  --out data/reports/webnlg_bidirectional_comparison_llm_stable.json \
  --table paper/tables/table_webnlg_bidirectional_comparison_llm_stable.md \
  --mine-subset-table paper/tables/table_webnlg_mine_style_subset_comparison.md
```

## Current WebNLG pilot values

On the fixed 50-fact subset:

| Metric | Value |
|---|---:|
| Deterministic node information | 0.9600 |
| Deterministic edge information | 0.5400 |
| Deterministic composite node/edge score | 0.7500 |
| Deterministic fact recoverability | 0.5400 |
| LLM fact recoverability | 0.5200 |
| Judge agreement with deterministic | 0.9800 |
| Parse success rate | 1.0000 |

## Acceptance criteria

- Tests pass without API credentials.
- Reports explicitly separate composite node/edge scores from binary fact recoverability.
- Bidirectional comparison labels MINE rows by score semantics.
- A dedicated fixed-subset table is generated for deterministic-vs-LLM MINE-style comparison.
