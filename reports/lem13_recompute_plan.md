# LEM-13 recomputation plan

This patch adds a presentation-level aggregate recomputation command. It does not rerun LLMs and does not change the scoring pipeline.

Main changes:

- Replace opaque Spearman/Viol diagnostics with score-drop sensitivity.
- Rename generic scores into factor preservation / mean score drop.
- Recompute ablation as gain relative to LEMON-full.
- Keep LLM reliability as a compact exploratory table.
- Move BC5CDR predicate coverage out of main-table logic: it is a single-relation biomedical transfer setting, not a predicate-diversity table.
