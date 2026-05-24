# LEM-05 test and build results

## Tests

```text
python -m pytest -q
188 passed in 0.51s
```

## Scoring commands

```text
python -m lemon_factor.scoring.score_perturbations --input data/processed/webnlg_perturbed.jsonl --inventory resources/factors/webnlg.json --dataset webnlg --out reports/scoring_webnlg.json --table-out paper/tables/table_webnlg_final.tex
status: passed, records: 500

python -m lemon_factor.scoring.score_perturbations --input data/biomedical/perturbed/drugprot_perturbed.jsonl --inventory resources/factors/drugprot.json --dataset drugprot --out reports/scoring_drugprot.json --table-out reports/scoring_drugprot.md
status: passed, records: 2100

python -m lemon_factor.scoring.score_perturbations --input data/biomedical/perturbed/bc5cdr_perturbed.jsonl --inventory resources/factors/bc5cdr.json --dataset bc5cdr --out reports/scoring_bc5cdr.json --table-out reports/scoring_bc5cdr.md
status: passed, records: 2445

python -m lemon_factor.scoring.aggregate --inputs reports/scoring_drugprot.json reports/scoring_bc5cdr.json --out reports/scoring_biomedical_summary.json --table-out paper/tables/table_biomedical_final.tex
status: passed
```

## PDF build

```text
cd paper
latexmk -pdf -interaction=nonstopmode main.tex
Output written on main.pdf (15 pages)
```

The PDF renders successfully to PNG pages. Remaining LaTeX warnings are existing underfull/overfull box warnings.
