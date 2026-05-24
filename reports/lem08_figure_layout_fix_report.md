# LEM-08 figure layout fix

Status: passed.

Changes:
- Replaced the previous two-panel TikZ figure with a simpler one-panel vector figure.
- Preserved the core message: source graph, predicate decomposition into factors, forward coverage, reverse recoverability, and diagnostics.
- Removed the cramped example card that caused overlaps and poor scaling.
- Kept the figure as TikZ/vector artwork rather than PNG.

Validation:
- LaTeX build passed with `latexmk -pdf -interaction=nonstopmode main.tex`.
- PDF length: 15 pages.
- Render check passed: all 15 pages rendered; page 5 inspected for figure layout.

Notes:
- Existing minor overfull/underfull hbox warnings remain elsewhere in the paper.
- No Python tests were run in the sandbox because the uploaded working archive contained paper/data artifacts, not the full `src/` and `tests/` tree.
