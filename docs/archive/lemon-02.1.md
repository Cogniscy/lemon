# lemon-02.1 — Stratified WebNLG pilot sampling

## Goal

Make the WebNLG pilot suitable for metric experiments rather than only smoke testing. The initial `lemon-02` converter used the first `n` parquet rows, which can overrepresent early WebNLG categories such as `Airport`. `lemon-02.1` adds deterministic category-stratified sampling so train/dev pilots cover multiple semantic domains.

## Why this matters for the paper

A single-category WebNLG pilot is weak evidence for graph-text meaning preservation. A category-balanced pilot supports the Data and Experimental Setup sections by showing that the evaluation is not restricted to one DBpedia domain.

Paper contribution:

- stronger WebNLG pilot description;
- reproducible `seed`-controlled sampling protocol;
- dataset statistics that report category counts and ratios;
- cleaner setup for `lemon-03` factor inventory extraction.

## Code deliverables

- `src/lemon_factor/datasets/sampling.py`
  - `take_first(records, n)`
  - `stratified_sample(records, n, label_key="category", seed=42, min_per_label=1)`
- `src/lemon_factor/datasets/convert_webnlg.py`
  - new CLI flags: `--stratify-category`, `--seed`, `--min-per-category`
- `src/lemon_factor/analysis/dataset_stats.py`
  - `category_count`
  - `category_ratios`
  - `predicate_count`
  - `examples_by_edges_count`
- tests:
  - `tests/test_sampling.py`
  - `tests/test_dataset_stats.py`
  - additional converter tests for `_select_records`

## Commands

Install research dependencies:

```bash
python -m pip install -e ".[dev,research]"
```

Create a stratified WebNLG pilot:

```bash
python -m lemon_factor.datasets.convert_webnlg \
  --language en \
  --n-train 200 \
  --n-dev 100 \
  --stratify-category \
  --seed 42 \
  --out-dir data/processed
```

Compute statistics:

```bash
python -m lemon_factor.analysis.dataset_stats \
  data/processed/webnlg_train.jsonl \
  data/processed/webnlg_dev.jsonl \
  --out data/reports/webnlg_stats.json
```

Run tests:

```bash
python -m pytest
```

## Acceptance criteria

The stage is complete if:

1. `python -m pytest` passes.
2. The converter still supports the old first-rows behavior by default.
3. `--stratify-category` produces a pilot with more than one category when the source split contains multiple categories.
4. Dataset statistics report both category counts and ratios.
5. README and roadmap document the new sampling mode.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Early-row sampling overfits to one category | Add `--stratify-category` and make it the recommended pilot mode |
| Stratified sampling is non-reproducible | Add explicit `--seed`; tests assert deterministic output |
| Small categories crash the sampler | Exhaust small groups safely and continue round-robin |
| Unit tests depend on internet | Keep all sampling/converter tests synthetic and offline-safe |
| Category balancing hides natural distribution | Keep default first-row mode and report the chosen sampling mode in paper |

## Next stage

`lemon-03` should use the stratified WebNLG train pilot to build a first inventory of terms, predicates, categories, and graph-neighborhood contexts.
