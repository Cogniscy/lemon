# lemon-09 — Paper skeleton and baseline comparison prep

## Goal

Turn the implemented LEMON-Factor pipeline into a paper-facing structure and add a lightweight baseline comparison layer.

This milestone does not claim final metric superiority. It prepares the paper and makes the comparison space explicit:

```text
exact entity-label overlap
predicate lexical cue coverage
lexical graph-text token similarity
LEMON-Factor initial coverage
LEMON-Factor expanded coverage
```

## Why this stage matters

The previous stages produced the core diagnostic metric. `lemon-09` connects it to paper writing:

- introduction and related work now have draft content;
- references are collected in `paper/references.bib`;
- the results section has text tied to generated tables;
- a comparison report makes clear which baselines are surface-only and which are factor-aware.

## Commands

Generate the baseline comparison table:

```powershell
python -m lemon_factor.analysis.baseline_comparison `
  data/processed/webnlg_dev.jsonl `
  --baseline-report data/reports/webnlg_lemon_factor_coverage.json `
  --expanded-report data/reports/webnlg_lemon_factor_coverage_expanded.json `
  --out data/reports/webnlg_baseline_comparison.json `
  --table paper/tables/table_webnlg_baseline_comparison.md
```

Run tests:

```powershell
pytest -q
```

## Outputs

```text
src/lemon_factor/baselines/text_similarity.py
src/lemon_factor/analysis/baseline_comparison.py
data/reports/webnlg_baseline_comparison.json
paper/tables/table_webnlg_baseline_comparison.md
paper/main.tex
paper/sections/*.tex
paper/references.bib
```

## Interpretation

The lexical token baselines are not semantic metrics. They are transparent controls showing how much graph-text similarity is explainable by surface token overlap. LEMON-Factor should be positioned as a diagnostic semantic-coverage layer that complements both lexical baselines and reference-based generation metrics.

## Acceptance criteria

1. `pytest -q` passes.
2. `baseline_comparison` creates JSON and Markdown outputs.
3. `paper/main.tex` references all current sections and `references.bib`.
4. Introduction, related work, method, results, and limitations sections contain draft text.
5. The paper language marks synthetic LLM adjudication as provisional, not expert validation.
