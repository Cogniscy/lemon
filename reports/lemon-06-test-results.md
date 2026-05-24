# LEM-06 Test Results

Commands executed in the patch workspace:

```bash
PYTHONPATH=src python -m pytest -q
```

Result:

```text
188 passed in 0.50s
```

Aggregation commands:

```bash
PYTHONPATH=src python -m lemon_factor.scoring.aggregate \
  --inputs reports/scoring_webnlg.json \
  --out reports/scoring_webnlg_summary.json \
  --table-out paper/tables/table_webnlg_final.tex \
  --caption 'WebNLG perturbation scoring summary.' \
  --label 'tab:webnlg-final'

PYTHONPATH=src python -m lemon_factor.scoring.aggregate \
  --inputs reports/scoring_drugprot.json reports/scoring_bc5cdr.json \
  --out reports/scoring_biomedical_summary.json \
  --table-out paper/tables/table_biomedical_final.tex \
  --caption 'Biomedical perturbation scoring summary.' \
  --label 'tab:biomedical-final'
```

LaTeX build:

```bash
cd paper
latexmk -pdf -interaction=nonstopmode main.tex
```

Result:

```text
Output written on main.pdf (15 pages)
```

Notes:

- LEM-06 adds no new LLM calls.
- The main paper uses the compact deterministic scoring table to stay within the 15-page SPECOM/LNCS limit.
- Detailed WebNLG and biomedical tables are generated as separate table artifacts.
