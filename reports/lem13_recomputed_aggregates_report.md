# LEM-13 recalculated paper aggregates

This report replaces opaque pilot diagnostics with publication-facing aggregates.

## Definitions

- Perturbation sensitivity is `1 - preservation_score`; larger values mean the metric reacts more strongly.
- Ablation gain is `full_drop - ablated_drop`; positive values mean the removed component contributed sensitivity.
- LLM mean score maps `covered/partial/absent` to `1/0.5/0`.
- Pairwise LLM agreement is reported only for overlapping factor judgments.

## Overall LLM probe

- Judgments: 135
- Judges: 3
- Mean LLM score: 0.809
- Pairwise agreement on overlap: 0.597
- Deterministic agreement: 0.561

## Recommended paper-table replacements

- Replace Spearman/Viol diagnostics with `table_perturbation_sensitivity_drop.tex`.
- Replace generic ablation score with `table_ablation_gain.tex`.
- Keep LLM reliability compact with `table_llm_reliability.tex`.
- Remove BC5CDR predicate coverage table from the main text; explain it as a single-relation transfer setting.
