# LEM-25: Reproducibility and submission-readiness pack

## Goal

Make the project easier to rerun before submission. This patch documents the current command order, expected outputs, root-directory assumptions, known warnings, and submission checks.

## Changed files

- `docs/REPRODUCIBILITY.md`
- `docs/SUBMISSION_CHECKLIST.md`
- `README.md`
- `docs/ROADMAP.md`
- `reports/lem25_reproducibility_pack_report.md`

## Main decisions

- Python scripts should be run from the repository root.
- The default vector baseline is `char_ngram_vector_cosine`, not a dense embedding benchmark.
- The radar figure is a perturbation-sensitivity profile, not an accuracy leaderboard.
- LLM/OpenRouter-dependent experiments are not part of the default local reproduction path.
- Expert validation remains prepared but not claimed until the returned workbook is summarized.

## Verification commands

```bash
python scripts/build_expert_validation_pack.py
```

```bash
python scripts/run_embedding_baseline.py
```

```bash
python scripts/make_radar_profile.py
```

```bash
python -m pytest -q
```

```bash
cd paper
```

```bash
latexmk -pdf -interaction=nonstopmode main.tex
```

## Expected outputs

```text
annotation/expert_validation_sample.csv
reports/embedding_baseline_perturbation.json
reports/embedding_baseline_perturbation.md
reports/radar_diagnostic_profile_values.json
paper/figures/figure_radar_diagnostic_profile.pdf
paper/figures/figure_radar_diagnostic_profile.png
paper/main.pdf
```

## Verification result

```text
annotation/expert_validation_sample.csv regenerated
embedding baseline regenerated
radar profile regenerated
225 passed
latexmk success
paper/main.pdf: 15 pages
no undefined references/citations in final main.log
```

## Known remaining issues

The LaTeX build still emits minor LNCS overfull/underfull box warnings. These are mostly caused by compact tables, formulas, and bibliography entries. They are acceptable only if the final rendered PDF has no clipped text, missing figures, broken citations, or broken references.
