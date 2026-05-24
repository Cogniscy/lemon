# LEM-15 final results-table cleanup

Status: passed.

Main changes:
- Removed the old WebNLG-only result tables from the main paper.
- Kept only three main result tables: perturbation sensitivity drops, ablation gain, and LLM reliability.
- Removed Spearman/Viol-style calibration reporting from the article logic.
- Rewrote Introduction/Experiments/Results into a narrative progression instead of formal RQ blocks.
- Kept WebNLG forward/reverse and relation-deletion values in prose where they support the argument.
- Rebuilt main.pdf.

Checks:
- LaTeX build passed.
- Rendered PDF pages: 14.
- Main paper grep: no Spearman, Viol, RQ labels, or old WebNLG pilot wording.
- Rendered page check: result tables appear as Tables 1--3.

Known remaining issues:
- Minor overfull/underfull boxes remain in LaTeX log, mostly from narrow LNCS text columns and reference wrapping.
