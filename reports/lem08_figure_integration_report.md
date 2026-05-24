# LEM-08 Figure integration and space compression

## Figure selection

Ranked candidates:

1. Two-panel predicate-factor + bidirectional evaluation figure. It covers both concepts needed by the method section and is the best main-paper candidate.
2. Bidirectional-only figure. It is clean, but it does not explain predicate-factor decomposition.
3. Decomposition-only figure. It is visually clear, but it lacks the bidirectional procedure and contains typographic issues.

The implemented figure follows candidate 1, but it is redrawn in LaTeX/TikZ rather than inserted as a raster PNG. This keeps the line art vector-based and fixes the generated-image spelling and layout artifacts.

## Main-text compression

- Removed the pipeline table from the method section because the new figure carries the same information more efficiently.
- Removed the WebNLG pilot statistics table from the main text and kept the dataset statistics in prose/repository artifacts.
- Kept the compact scoring and ablation tables in the main text.

## Build check

- LaTeX build: passed.
- Render check: 15 pages rendered.
- PDF length: 15 pages.
- Pytest was not run in this sandbox because the uploaded LEM-07 archive contains paper/data artifacts but not the full `src/` and `tests/` tree. Run `python -m pytest -q` after applying the patch to the full local repository.
