# LEM-29 publication figure insertion report

## Goal
Insert the polished worked-example figure into the paper and add the public repository URL to the article text rather than to the figure.

## Changes
- Regenerated `paper/figures/figure_factor_scoring_examples.pdf` as a controlled vector figure.
- Regenerated the matching PNG preview at `paper/figures/figure_factor_scoring_examples.png`.
- Added the repository link to the abstract: `https://github.com/Cogniscy/lemon`.
- Kept the repository URL out of the figure itself.
- Added/updated `scripts/make_factor_scoring_examples.py` as the figure generator.

## Verification
- `python scripts/make_factor_scoring_examples.py`
- `cd paper`
- `latexmk -pdf -interaction=nonstopmode main.tex`

Observed:
- `paper/main.pdf` rebuilt successfully.
- `paper/main.pdf` remains 15 pages.
- Final log has no undefined references or citations.
- The repository URL appears on page 1 in the abstract.
- The worked-example figure appears as Fig. 1.
