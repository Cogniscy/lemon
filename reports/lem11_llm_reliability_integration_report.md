# LEM-11 LLM reliability integration report

## Changes

- Added a compact LLM reliability probe table to the paper.
- Integrated a short RQ6 paragraph into the Results section.
- Compressed the Limitations section to keep the LNCS page budget.
- Added `reports/llm_reliability_note.md` as a repository-facing explanation of the probe.

## Probe setup

- Three 45-item judge batches, 135 total judgments.
- Models:
  - `google/gemini-2.0-flash-001`
  - `openai/gpt-4o-mini`
  - `meta-llama/llama-3.1-70b-instruct`
- Each judge received the source edge, factor inventory, and perturbed text.
- Decisions: `covered`, `partial`, `absent`.
- Numeric mapping: covered = 1.0, partial = 0.5, absent = 0.0.

## Compact results

| Subset | Mean LLM score | Pairwise judge agreement | Deterministic agreement |
|---|---:|---:|---:|
| All judged factors | 0.809 | 0.597 | 0.561 |
| Argument swap | 0.765 | 0.386 | 0.432 |
| Node deletion | 0.731 | 0.502 | 0.408 |
| Polarity flip | 0.857 | 0.766 | 0.694 |
| Relation blur | 0.907 | 0.730 | 0.647 |

## Build check

- LaTeX build: passed.
- Render check: 15 pages rendered.
- Final PDF pages: 15.
