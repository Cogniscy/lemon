# LEM-27 formal submission cleanup report

## Goal
Finalize the formal submission-facing metadata and package the paper sources after the author-block update.

## Author block

Final author order:

1. Anton Tomilov — STC-Innovation, Saint Petersburg, Russian Federation
2. Daria Gineva — ITMO University, Saint Petersburg, 197101, Russian Federation
3. Danil Tirskikh — ITMO University, Saint Petersburg, 197101, Russian Federation
4. Olesia Koroteeva — ITMO University, Saint Petersburg, 197101, Russian Federation
5. Yuri Matveev — ITMO University, Saint Petersburg, 197101, Russian Federation

The ITMO affiliation format follows the Springer page supplied by the author for the related SPECOM chapter. STC-Innovation was added as supplied by the author.

## Files updated

- `paper/main.tex`
- `paper/main.pdf`
- `docs/SUBMISSION_CHECKLIST.md`
- `docs/ROADMAP.md`
- `tests/test_paper_draft_artifacts.py`
- `reports/lem27_submission_formal_cleanup_report.md`

## Verification

Commands run from the repository root unless noted otherwise:

```bash
python scripts/make_radar_profile.py
```

```bash
python -m pytest -q
```

Observed result:

```text
225 passed
```

```bash
cd paper
latexmk -pdf -interaction=nonstopmode main.tex
```

Observed result:

```text
latexmk success
paper/main.pdf: 15 pages
```

Log sanity checks:

```text
no undefined citations
no undefined references
no remaining author-affiliation placeholders
```

The only remaining warning class in the final log is a known `amsmath` warning about `\vec`; visible PDF output is unaffected.

## Render check

`paper/main.pdf` was rendered to images with the PDF render helper. The first page shows the updated author block and two affiliations. The full PDF remains 15 pages.

## Submission package

A reviewer-facing paper package was generated as:

```text
lemon_specom_submission_package.zip
```

It contains:

- `paper/main.pdf`
- `paper/main.tex`
- `paper/references_latex.tex`
- `paper/references.bib`
- `paper/sections/*.tex`
- `paper/tables/*.tex`
- `paper/figures/*` needed by the manuscript
- `README_SUBMISSION.txt`

## Remaining manual checks

- Confirm whether the conference portal requires emails, ORCID IDs, or funding/acknowledgement text.
- Confirm whether the submission should be anonymized or non-anonymized.
- Integrate expert-validation results only after the linguist workbook is returned and summarized.
