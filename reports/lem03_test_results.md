# LEM-03 Test Results

Commands executed:

```bash
PYTHONPATH=src pytest -q
PYTHONPATH=src python -m lemon_factor.factors.validate --inventory resources/factors/drugprot.json --data data/biomedical/processed/drugprot_train.jsonl --out reports/factor_inventory_drugprot.json --table-out reports/factor_inventory_drugprot.md --min-coverage 0.95
PYTHONPATH=src python -m lemon_factor.factors.validate --inventory resources/factors/bc5cdr.json --data data/biomedical/processed/bc5cdr_train.jsonl --out reports/factor_inventory_bc5cdr.json --table-out reports/factor_inventory_bc5cdr.md --min-coverage 1.0
PYTHONPATH=src python -m lemon_factor.factors.validate --inventory resources/factors/webnlg.json --data data/processed/webnlg_dev.jsonl --out reports/factor_inventory_webnlg.json --table-out reports/factor_inventory_webnlg.md --min-coverage 1.0
cd paper && latexmk -g -pdf -interaction=nonstopmode main.tex
```

Results:

```text
182 passed in 1.06s
DrugProt inventory: passed
BC5CDR inventory: passed
WebNLG inventory: passed
LaTeX build: main.pdf, 14 pages
```

Remaining build notes: the PDF still has minor overfull/underfull hbox warnings inherited from the current draft. No build error was produced.
