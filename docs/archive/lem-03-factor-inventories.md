# LEM-03: Factor Inventories

LEM-03 fixes the predicate-factor inventories used by the final submission pipeline. The inventories are deterministic JSON resources, not LLM calls.

## Outputs

- `resources/factors/schema.json` - inventory JSON schema documentation.
- `resources/factors/webnlg.json` - fixed WebNLG predicate-factor inventory for the current development split.
- `resources/factors/drugprot.json` - biomedical chemical-gene/protein inventory.
- `resources/factors/bc5cdr.json` - biomedical chemical-induced disease inventory.
- `src/lemon_factor/factors/validate.py` - offline inventory validator and predicate-coverage reporter.
- `paper/tables/table_factor_inventory.tex` - paper-ready inventory summary table.

## Commands

```powershell
python -m pytest -q

python -m lemon_factor.factors.validate `
  --inventory resources/factors/drugprot.json `
  --data data/biomedical/processed/drugprot_train.jsonl `
  --out reports/factor_inventory_drugprot.json `
  --table-out reports/factor_inventory_drugprot.md `
  --min-coverage 0.95

python -m lemon_factor.factors.validate `
  --inventory resources/factors/bc5cdr.json `
  --data data/biomedical/processed/bc5cdr_train.jsonl `
  --out reports/factor_inventory_bc5cdr.json `
  --table-out reports/factor_inventory_bc5cdr.md `
  --min-coverage 1.0

python -m lemon_factor.factors.validate `
  --inventory resources/factors/webnlg.json `
  --data data/processed/webnlg_dev.jsonl `
  --out reports/factor_inventory_webnlg.json `
  --table-out reports/factor_inventory_webnlg.md `
  --min-coverage 1.0
```

## Scope

The biomedical resources encode participant roles, polarity, directionality, and evidence form. They are fixed inventories for evaluation, not full biomedical ontologies.
