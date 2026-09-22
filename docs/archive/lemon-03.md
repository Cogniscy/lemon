# lemon-03 — WebNLG factor inventory

## Goal

Build the first reproducible factor-inventory layer from the stratified WebNLG train split. This stage does not create final semantic decompositions yet. It extracts the graph-side vocabulary that will later be used to define and validate factorized semantic decompositions.

## Research contribution

This stage supports the paper claim that LEMON-Factor starts from explicit graph structure rather than raw text extraction. WebNLG provides RDF-style triples paired with natural-language verbalizations, so predicate and entity inventories can be derived from gold graph structures before any factor similarity experiment.

## Inputs

Expected input after `lemon-02.1`:

```bash
python -m lemon_factor.datasets.convert_webnlg \
  --language en \
  --n-train 200 \
  --n-dev 100 \
  --stratify-category \
  --seed 42 \
  --out-dir data/processed
```

Primary input:

```text
data/processed/webnlg_train.jsonl
```

## Outputs

```text
data/interim/webnlg_factor_inventory.json
data/reports/webnlg_factor_inventory_summary.json
paper/tables/table_webnlg_inventory.md
```

## Code added

```text
src/lemon_factor/factors/candidates.py
src/lemon_factor/factors/inventory.py
src/lemon_factor/factors/inventory_cli.py
src/lemon_factor/analysis/inventory_stats.py
```

## Commands

Build the inventory:

```bash
python -m lemon_factor.factors.inventory_cli \
  data/processed/webnlg_train.jsonl \
  --out data/interim/webnlg_factor_inventory.json \
  --summary data/reports/webnlg_factor_inventory_summary.json
```

Export a compact paper table:

```bash
python -m lemon_factor.analysis.inventory_stats \
  data/interim/webnlg_factor_inventory.json \
  --out paper/tables/table_webnlg_inventory.md
```

Run tests:

```bash
python -m pytest
```

## What the inventory contains

The inventory stores:

- predicate frequencies;
- predicate-to-category counts;
- predicate example edges and text contexts;
- node label frequencies;
- node-label-to-category counts;
- category-to-predicate counts;
- candidate semantic factors extracted from predicate names.

Example predicate decomposition candidate:

```text
elevationAboveTheSeaLevel → elevation + above + the + sea + level
```

These are candidate factors, not final semantic factors. They will be curated and mapped into `factor_schema.json` in the next stage.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Predicate-name splitting is shallow | Label output as candidate factors only |
| DBpedia predicates mix camelCase, slashes, digits | Dedicated `split_predicate_name` normalizer |
| Context lists can grow too large | Limit with `--max-contexts` |
| WebNLG is open-domain, not biomedical | Use it as the clean gold-graph pilot before BioRED |
| Common words such as `the` appear as candidates | Keep by default for auditing; later filtering can be applied |

## Acceptance criteria

The stage is complete when:

1. `python -m pytest` passes.
2. `inventory_cli` creates JSON inventory and summary files.
3. The summary reports predicate, node-label, category, and candidate-factor counts.
4. `inventory_stats` creates a markdown table for the paper.
5. Candidate factors are explicitly documented as non-final evidence for later semantic decomposition.

## Next stage

`lemon-04` should create the first seed `factor_schema.json` and manually/semiautomatically map top WebNLG predicates to factor decompositions.
