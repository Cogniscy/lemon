# LEM-14 final narrative/table cleanup

## Changes

- Reworked the abstract and introduction so the paper reads as a coherent diagnostic study rather than a sequence of pilots.
- Removed the fixed factor-inventory coverage table from the main text; BC5CDR is now described as a deliberate single-relation biomedical transfer setting.
- Removed Spearman/Viol calibration from the main text and replaced it with score-drop interpretation.
- Replaced the old compact scoring table with perturbation sensitivity as mean score drop.
- Replaced the old ablation table with gain-vs-full interpretation.
- Rewrote the Results narrative so each subsection explains what the table shows and why it matters.
- Rewrote the Conclusion around the central claim: LEMON-Factor is a diagnostic layer that explains relation-level failures hidden by entity/triple/node-edge metrics.
- Kept LLM reliability as an exploratory diagnostic complement, not as human validation.

## Verification

- LaTeX build: passed.
- PDF page count: 15 pages.
- Render check: 15 pages rendered.
- Undefined citations: none detected in the final build log.
- pytest was not run in this sandbox because the supplied archive contains paper/reports only, not the full source and tests.
