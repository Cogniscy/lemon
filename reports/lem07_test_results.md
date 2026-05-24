# LEM-07 test and build results

Patch: Compact ablation study.

## Commands run

```bash
PYTHONPATH=src python -m lemon_factor.scoring.ablate \
  --inputs reports/scoring_webnlg.json reports/scoring_drugprot.json reports/scoring_bc5cdr.json \
  --out reports/ablation_summary.json \
  --table-out paper/tables/table_ablation.tex

PYTHONPATH=src pytest -q

cd paper && latexmk -pdf -interaction=nonstopmode main.tex
python /home/oai/skills/pdfs/scripts/render_pdf.py paper/main.pdf --out_dir /mnt/data/lem07_render --dpi 150
```

## Results

- Tests: 189 passed.
- LaTeX: passed.
- PDF: 15 pages.
- Render check: 15 pages rendered.
- Known warnings: minor overfull/underfull hbox warnings only.

## Notes

The LEM-07 ablation study is deterministic. It uses fixed factor inventories and perturbation metadata, not LLM judging. The RQ3 MINE-style numeric facts are retained in prose while the detailed table is removed from the main text to keep the paper inside the 15-page SPECOM limit and preserve space for figures.
