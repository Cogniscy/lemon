# LEM-04 test results

Commands run in the patched repository:

```bash
PYTHONPATH=src python -m pytest -q
```

Result:

```text
185 passed in 0.61s
```

Perturbation builders were exercised on DrugProt, BC5CDR, and WebNLG:

```bash
PYTHONPATH=src python -m lemon_factor.perturbations.build \
  --input data/biomedical/processed/drugprot_train.jsonl \
  --out data/biomedical/perturbed/drugprot_perturbed.jsonl \
  --limit 500 \
  --report-out reports/perturbation_drugprot_report.json \
  --table-out reports/perturbation_drugprot_report.md

PYTHONPATH=src python -m lemon_factor.perturbations.build \
  --input data/biomedical/processed/bc5cdr_train.jsonl \
  --out data/biomedical/perturbed/bc5cdr_perturbed.jsonl \
  --limit 500 \
  --report-out reports/perturbation_bc5cdr_report.json \
  --table-out reports/perturbation_bc5cdr_report.md

PYTHONPATH=src python -m lemon_factor.perturbations.build \
  --input data/processed/webnlg_dev.jsonl \
  --out data/processed/webnlg_perturbed.jsonl \
  --limit 500 \
  --report-out reports/perturbation_webnlg_report.json \
  --table-out reports/perturbation_webnlg_report.md
```

Results:

```text
DrugProt: 2100 records
BC5CDR: 2445 records
WebNLG: 500 records
```

PDF build:

```bash
cd paper && latexmk -g -pdf -interaction=nonstopmode main.tex
```

Result:

```text
Output written on main.pdf (14 pages)
```
