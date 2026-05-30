# LEM-24: Paper audit, style, layout, and references

## Goal

Tighten the SPECOM paper before submission without adding new experiments. The patch focuses on narrative clarity, conservative claims, less generic wording, final future-work framing, bibliography freshness, and the 15-page LNCS budget.

## Main edits

- Rewrote the abstract to start from the central failure mode: entity names can survive while predicate meaning is lost.
- Reworked the introduction into a single line of reasoning: graph edge -> predicate meaning -> factor audit -> bidirectional evaluation -> controlled perturbations.
- Tightened the experiments/results prose and removed redundant explanatory phrases.
- Kept the radar wording explicitly non-leaderboard and clarified the offline character n-gram vector baseline.
- Rewrote the conclusion to summarize the empirical claim and state concrete next steps.
- Updated the bibliography with recent LLM graph-to-text work: He et al. 2025 / PlanGTG.
- Scanned for common generic LLM-style words and avoided high-salience patterns such as “delve”, “tapestry”, “realm”, “underscore”, “pivotal”, “seamless”, “comprehensive”, “landscape”, and “in conclusion”.

## Changed files

- `paper/main.tex`
- `paper/sections/01_introduction.tex`
- `paper/sections/02_related_work.tex`
- `paper/sections/05_experiments.tex`
- `paper/sections/06_results.tex`
- `paper/sections/07_error_analysis.tex`
- `paper/sections/08_limitations.tex`
- `paper/sections/09_conclusion.tex`
- `paper/references_latex.tex`
- `paper/references.bib`
- `paper/main.pdf`
- `docs/ROADMAP.md`
- `docs/CLAIMS_AND_METRICS_AUDIT.md`
- `reports/lem24_paper_audit_layout_report.md`

## Verification

```bash
python -m pytest -q
```

```text
225 passed
```

```bash
cd paper
latexmk -pdf -interaction=nonstopmode main.tex
```

```text
latexmk success
paper/main.pdf: 15 pages
no undefined references/citations
```

```bash
python /home/oai/skills/pdfs/scripts/render_pdf.py paper/main.pdf --out_dir /mnt/data/lem24_after_render --dpi 120
```

```text
15 pages rendered successfully
```

## Known remaining issues

The build still has minor LNCS layout warnings, mostly overfull/underfull boxes caused by long method expressions, references, and compact tables. They do not produce missing content or broken references in the rendered PDF.

## Not changed

- No new experiments.
- No dense embedding run.
- No OpenRouter run.
- No expert-validation results until the linguist form is returned.
- No change to core metric implementation.
