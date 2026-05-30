# LEM-26 diagnostic profile redesign report

## Goal
Replace the spider/radar chart with a more legible figure style that matches modern paper conventions better and avoids the misleading visual impression that larger scalar drops automatically mean a better metric.

## Changes
- Reworked `scripts/make_radar_profile.py` to generate an **annotated matrix heatmap** instead of a polar chart.
- Kept the same data source files and output figure paths for reproducibility continuity.
- Updated `paper/sections/06_results.tex` so the narrative explains the key interpretation:
  - MINE-style and triple-match are harsher scalar detectors.
  - LEMON-Factor may show smaller aggregate drops, but its response remains attached to predicate factors.
- Updated `tests/test_radar_profile_values.py` to reflect the matrix-style figure and revised wording.
- Updated `docs/CLAIMS_AND_METRICS_AUDIT.md` to refer to a diagnostic-profile figure rather than a radar/spider chart.

## Why this helps
The matrix uses a linear scale, explicit cell values, and a color bar. It is therefore easier to read in print and avoids some common readability problems of radar charts when several traces overlap.

## Interpretation note
The redesigned figure does **not** change the underlying values:
- MINE-style and triple-match still have larger mean drops under perturbation.
- This should be interpreted as stronger scalar sensitivity, not automatic superiority.
- The intended niche of LEMON-Factor remains factor-localized diagnosis rather than the harshest scalar penalty.

## Verification
- `python scripts/make_radar_profile.py`
- `python -m pytest -q`
- `cd paper && latexmk -pdf -interaction=nonstopmode main.tex`

Observed locally:
- `225 passed`
- `paper/main.pdf` rebuilt successfully
- `15 pages`
