# lemon-07 — LEMON-Factor graph–text coverage metric

## Goal

Implement the first deterministic LEMON-Factor graph–text coverage metric on
WebNLG dev. The metric evaluates whether an explicit graph edge is supported by
its textual verbalization at the level of semantic factor components.

This stage intentionally avoids extraction and LLM text understanding. It uses
explicit WebNLG graph edges, predicate decompositions, and a small lexical cue
baseline.

## Inputs

- `data/processed/webnlg_dev.jsonl`
- `data/interim/webnlg_predicate_decompositions_synthetic_adjudicated.json`
- `data/interim/webnlg_lexical_cues_seed.json`

## Outputs

- `data/reports/webnlg_lemon_factor_coverage.json`
- `data/reports/webnlg_lemon_factor_coverage_details.jsonl`
- `paper/tables/table_webnlg_lemon_factor_coverage.md`

## Method

For each edge `subject --predicate--> object`:

1. Load the predicate decomposition.
2. Check subject-domain factors against subject label evidence in text.
3. Check object-domain factors against object label evidence in text.
4. Check predicate-meaning factors against predicate/factor lexical cues.
5. Compute weighted coverage:

```text
coverage(edge) = sum(weight_i * covered_i) / sum(weight_i)
```

The corpus report contains three interpretable scores:

- exact label coverage;
- predicate cue coverage;
- LEMON-Factor weighted coverage.

It also reports `missing_decomposition_rate`, because coverage is only as reliable
as the available predicate decomposition inventory.

## Run

```powershell
python -m lemon_factor.coverage.run_webnlg_coverage `
  data/processed/webnlg_dev.jsonl `
  --decompositions data/interim/webnlg_predicate_decompositions_synthetic_adjudicated.json `
  --lexical-cues data/interim/webnlg_lexical_cues_seed.json `
  --out data/reports/webnlg_lemon_factor_coverage.json `
  --details data/reports/webnlg_lemon_factor_coverage_details.jsonl `
  --table paper/tables/table_webnlg_lemon_factor_coverage.md
```

## Interpretation

An edge-level detail record explains which factors were covered or missed:

```text
covered: subject_domain, object_domain
missing: predicate_meaning
```

This is the diagnostic advantage over a single surface score.

## Limitations

- Lexical cues are a deterministic baseline, not a full semantic parser.
- Short or generic cues can produce false positives, so standalone stopword cues
  are ignored.
- Text can express relations without explicit lexical cues; this will be handled
  later with embedding or LLM evidence.
- Synthetic adjudicated decompositions are temporary references, not human gold.

## Acceptance criteria

- `pytest` passes.
- Coverage CLI writes report, details, and paper table.
- Missing decompositions are counted.
- Edge details expose covered/missing factor components.
