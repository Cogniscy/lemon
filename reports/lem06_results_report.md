# LEM-06 Results Report

Status: passed.

LEM-06 aggregates deterministic perturbation scoring and updates the paper text. It keeps the main paper within the SPECOM/LNCS page budget and does not introduce new LLM evaluation.

## Generated artifacts

- `reports/scoring_webnlg_summary.json`
- `reports/scoring_biomedical_summary.json`
- `paper/tables/table_webnlg_final.tex`
- `paper/tables/table_biomedical_final.tex`
- `paper/tables/table_scoring_final_compact.tex`
- `paper/build/lemon_lem06_final_results.pdf`

## Commands

```powershell
python -m pytest -q

python -m lemon_factor.scoring.aggregate `
  --inputs reports/scoring_webnlg.json `
  --out reports/scoring_webnlg_summary.json `
  --table-out paper/tables/table_webnlg_final.tex `
  --caption "WebNLG perturbation scoring summary." `
  --label "tab:webnlg-final"

python -m lemon_factor.scoring.aggregate `
  --inputs reports/scoring_drugprot.json reports/scoring_bc5cdr.json `
  --out reports/scoring_biomedical_summary.json `
  --table-out paper/tables/table_biomedical_final.tex `
  --caption "Biomedical perturbation scoring summary." `
  --label "tab:biomedical-final"
```

## Notes

The paper uses the compact deterministic scoring table to avoid exceeding 15 pages. The detailed WebNLG and biomedical tables remain in `paper/tables/` for inspection and appendix use.
