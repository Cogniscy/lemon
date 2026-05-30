# LEM-19: Radar Diagnostic Profile

## Goal

Add a compact radar/spider figure that visualizes the diagnostic niche of LEMON-Factor under controlled semantic perturbations.

The figure is not an accuracy leaderboard. It plots mean score drops under controlled perturbations, so larger values mean stronger sensitivity to induced semantic damage.

## Files added or changed

- `scripts/make_radar_profile.py`
- `reports/radar_diagnostic_profile_values.json`
- `paper/figures/figure_radar_diagnostic_profile.pdf`
- `paper/figures/figure_radar_diagnostic_profile.png`
- `paper/sections/06_results.tex`
- `docs/CLAIMS_AND_METRICS_AUDIT.md`
- `tests/test_radar_profile_values.py`
- `reports/lem19_radar_diagnostic_profile_report.md`

## Data source

Primary source:

- `reports/paper_metric_sensitivity_drops.json`

Context source:

- `reports/layer_profile_values.json`

Axes:

- Node deletion
- Edge deletion
- Argument swap
- Polarity flip
- Relation blur

Methods plotted:

- LEMON-Factor (`lemon_full`)
- Entity recall (`entity_recall`)
- Triple match (`triple_match`)

## Interpretation

Safe claim:

> The radar profile visualizes diagnostic sensitivity to controlled semantic perturbations. Larger values mean stronger response to induced damage, not higher task accuracy.

Unsafe claim:

> The radar profile proves that LEMON-Factor is globally better than entity, triple, embedding, or LLM metrics.

## Tests

Added `tests/test_radar_profile_values.py` to check:

- the generator creates JSON/PDF/PNG outputs;
- all plotted values are bounded in `[0, 1]`;
- every axis has documented source and normalization rule;
- the Results section includes the figure and caveat wording.

## Remaining caveats

- The radar figure does not include embeddings. The embedding baseline is planned for a later patch.
- The figure compares perturbation sensitivity, not semantic accuracy.
- Polarity sensitivity remains inventory-dependent.

## Verification

Commands run:

```bash
python scripts/make_radar_profile.py
```

```bash
python -m pytest -q
```

Result:

```text
216 passed
```

```bash
cd paper
latexmk -pdf -interaction=nonstopmode main.tex
```

Result:

```text
latexmk success
paper/main.pdf: 15 pages
no undefined references or citations in main.log
```

PDF render check:

```bash
python /home/oai/skills/pdfs/scripts/render_pdf.py paper/main.pdf --out_dir pdf_render_lem19 --dpi 150
```

Result:

```text
15 pages rendered successfully
```
