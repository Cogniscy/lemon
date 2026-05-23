# LEM-02 build and test results

## Commands run

```bash
python -m pytest -q
PYTHONPATH=src python -m lemon_factor.datasets.convert_drugprot --source direct --download-dir data/biomedical/raw/drugprot --out-dir data/biomedical/processed --manifest data/biomedical/manifests/drugprot_manifest.json --limit 500
PYTHONPATH=src python -m lemon_factor.datasets.convert_bc5cdr --source direct --download-dir data/biomedical/raw/bc5cdr --out-dir data/biomedical/processed --manifest data/biomedical/manifests/bc5cdr_manifest.json --limit 500
PYTHONPATH=src python -m lemon_factor.datasets.biomedical_quality data/biomedical/processed/drugprot_train.jsonl --out data/biomedical/reports/drugprot_quality_check.json --min-examples 500 --min-edges 1 --min-predicates 10
PYTHONPATH=src python -m lemon_factor.datasets.biomedical_quality data/biomedical/processed/bc5cdr_train.jsonl data/biomedical/processed/bc5cdr_dev.jsonl --out data/biomedical/reports/bc5cdr_quality_check.json --min-examples 500 --min-edges 1 --min-predicates 1
PYTHONPATH=src python -m lemon_factor.analysis.biomedical_dataset_stats data/biomedical/processed/drugprot_train.jsonl data/biomedical/processed/bc5cdr_train.jsonl data/biomedical/processed/bc5cdr_dev.jsonl --out data/biomedical/reports/biomedical_dataset_stats.json --table paper/tables/table_biomedical_dataset_stats.md
cd paper && latexmk -g -pdf -interaction=nonstopmode main.tex
```

## Results

```text
179 passed in 0.55s
DrugProt quality: passed
BC5CDR quality: passed
Output written on main.pdf (14 pages)
```

## Known warnings

LaTeX reports only minor overfull/underfull hbox warnings.  They do not block the PDF build.
