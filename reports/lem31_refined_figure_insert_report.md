# LEM-31 refined worked-example figure insert report

## Goal
Insert the refined worked-example figure into the article and update the reproducible figure-generation script.

## Changes
- Replaced `scripts/make_factor_scoring_examples.py` with the refined generator.
- Regenerated:
  - `paper/figures/figure_factor_scoring_examples.pdf`
  - `paper/figures/figure_factor_scoring_examples.png`
- Rebuilt `paper/main.pdf`.

## Notes
The figure keeps the previous article placement and caption. The repository URL remains in the article text/abstract, not in the figure.

## Verification
- `python scripts/make_factor_scoring_examples.py`
- `python -m pytest -q`
- `cd paper && latexmk -pdf -interaction=nonstopmode main.tex`
- rendered `paper/main.pdf` to inspect the figure page

Observed locally:
- `228 passed`
- `paper/main.pdf`: 15 pages
- no undefined references or citations in the final LaTeX build
