# LEM-11 LLM reliability note

This note summarizes the exploratory LLM factor-judging probe integrated into the paper.

## Setup

- Batches: three 45-item judge batches sampled from the prepared LLM probe pool.
- Judgments: 135 total judgments, three LLM judges. Pairwise agreement is computed on overlapping factor judgments.
- Judge models:
  - `google/gemini-2.0-flash-001`
  - `openai/gpt-4o-mini`
  - `meta-llama/llama-3.1-70b-instruct`
- Access: OpenRouter, JSON-schema constrained output.
- Decision labels: `covered`, `partial`, `absent` for each semantic factor.
- Numeric mapping for summary: covered = 1.0, partial = 0.5, absent = 0.0.

## Compact results

| Subset | Mean LLM score | Pairwise judge agreement | Deterministic agreement |
|---|---:|---:|---:|
| All judged factors | 0.809 | 0.597 | 0.561 |
| Argument swap | 0.765 | 0.386 | 0.432 |
| Node deletion | 0.731 | 0.502 | 0.408 |
| Polarity flip | 0.857 | 0.766 | 0.694 |
| Relation blur | 0.907 | 0.730 | 0.647 |

## Interpretation

The probe suggests that deterministic perturbation labels are stricter than LLM-based semantic recovery. LLM judges often recover semantic factors from residual context, especially under node deletion and argument swap. This supports using LLM judging as a diagnostic complement, not as human validation.

Source summary: `reports/llm_reliability_summary_3judges.json`.
