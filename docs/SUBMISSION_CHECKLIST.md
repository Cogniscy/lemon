# Submission checklist

This checklist is for the SPECOM/LNCS paper package. It separates paper readiness from later expert-validation integration. The LEM-27 formal pass filled the author block and created a reviewer-facing submission package; final conference portal metadata should still be checked manually before upload.

## Paper scope

- [ ] The paper is framed as graph-text semantic fidelity, not general text-text similarity.
- [ ] LEMON-Factor is described as a diagnostic factor-level metric, not a universal semantic metric.
- [ ] The MINE baseline is called `MINE-style` or `MINE-inspired`, not a reproduction of KGGen/MINE.
- [ ] The vector baseline is called an offline character n-gram vector baseline unless a dense backend was explicitly run.
- [ ] LLM judges are described as a recoverability probe, not expert validation.
- [ ] Expert validation is not claimed until the linguist workbook is returned and summarized.

## Paper build

- [ ] `paper/main.pdf` builds with `latexmk`.
- [ ] No undefined citations remain in the final log.
- [ ] No undefined references remain in the final log.
- [ ] The PDF has 15 pages or fewer.
- [ ] Figures and tables are legible in the rendered PDF.
- [ ] The diagnostic-profile figure caption states that the profile is based on perturbation drops, not accuracy.
- [ ] The author block has no placeholders before final submission.
- [ ] Affiliations and acknowledgements match the submission metadata.

## Reproducibility

- [ ] `python -m pytest -q` passes.
- [ ] `python scripts/run_embedding_baseline.py` regenerates the vector baseline report.
- [ ] `python scripts/make_radar_profile.py` regenerates the diagnostic-profile JSON and figures.
- [ ] `docs/REPRODUCIBILITY.md` matches the current command sequence.
- [ ] Known LaTeX warnings are documented and do not affect visible output.

## Repository hygiene

- [ ] No API keys, local credentials, or private config files are included.
- [ ] No local absolute paths are mentioned in the paper text.
- [ ] Generated helper renders and temporary build logs are not included in the submission archive unless intentionally needed.
- [ ] The source archive contains `paper/`, `src/`, `scripts/`, `reports/`, `resources/`, `docs/`, `tests/`, and required data subsets.
- [ ] The reviewer-facing linguist pack is kept separate from claimed paper results unless completed.

## Final package split

Recommended final artifacts after the LEM-27 cleanup:

```text
paper_submission/        PDF and required LaTeX source files, generated as `lemon_specom_submission_package.zip`
reproducibility_pack/    code, reports, resources, tests, docs
internal_review_pack/    expert-validation workbook and returned annotations
```

Do not submit internal review material as validation evidence unless it has been completed and summarized.
