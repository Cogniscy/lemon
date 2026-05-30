# LEM-17 Positioning and Documentation Patch Report

## Goal

Fix the project narrative around the current SPECOM paper scope and add lightweight documentation for claims, metrics, and linguistic validation.

## Scope decision

The paper is positioned as a graph-text semantic fidelity study:

```text
explicit source graph / relation inventory + text
  -> predicate factor decomposition
  -> forward KG->Text coverage
  -> reverse Text->KG recoverability diagnostics
```

It is not positioned as a general text-text similarity system, a full text-to-KG extractor, or a replacement for embedding metrics.

## Changed files

- `README.md`
- `docs/ROADMAP.md`
- `docs/CLAIMS_AND_METRICS_AUDIT.md`
- `docs/LINGUIST_VALIDATION.md`
- `docs/annotation_guidelines.md`
- `annotation/linguist_predicate_review_template.csv`
- `paper/main.tex`
- `paper/sections/01_introduction.tex`
- `paper/sections/08_limitations.tex`
- `paper/sections/09_conclusion.tex`
- `reports/lem17_positioning_docs_report.md`

## Main text changes

- Abstract: softened "cross-domain framework" into an interpretable diagnostic layer across open-domain and biomedical data.
- Introduction: added the restricted layered semantic comparison framing.
- Limitations: explicitly states that LEMON-Factor is not a general-purpose text-text similarity metric, does not include dense embedding baselines yet, and does not model pragmatics.
- Conclusion: frames the method as a controlled graph-text instance of layered semantic comparison and points to layer/profile, expert validation, embeddings, and stronger evidence models as next steps.

## Documentation changes

- README now explains scope, non-claims, layout, quick start, current findings, and expert validation entry points.
- Claims audit records safe wording for polarity, LLM judges, MINE-style baseline, radar chart, embeddings, expert validation, and pragmatics.
- Linguist validation guide gives a compact task and simple CSV schema for reviewing predicate factors.
- Roadmap now lists the near-term patch sequence: layer/profile table, radar, embedding baseline, expert validation, and final SPECOM compaction.

## Validation

Commands run:

```bash
python -m pytest -q
cd paper && latexmk -pdf -interaction=nonstopmode main.tex
python /home/oai/skills/pdfs/scripts/render_pdf.py /mnt/data/lemon_work/paper/main.pdf --out_dir /mnt/data/lemon_pdf_render --dpi 150
```

Results:

- `pytest`: 212 passed.
- `latexmk`: success.
- `paper/main.pdf`: 14 pages.
- PDF render check: 14 pages rendered successfully.

## Known issues not addressed in this patch

- No layer/profile table yet.
- No new radar chart values yet.
- No embedding baseline yet.
- No expert validation results yet.
- Existing LaTeX overfull/underfull warnings remain; no fatal compile errors.
