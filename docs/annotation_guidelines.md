# Annotation Guidelines

This document defines the human expert input needed for LEMON-Factor pilot experiments.

## 1. Factor decomposition review

Input columns:

```text
term, dataset, proposed_factors, proposed_roles, proposed_weights, context
```

Expert output columns:

```text
is_valid, missing_factors, extra_factors, wrong_roles, weight_comment, confidence, notes
```

Decision policy:

- Mark `is_valid=true` if the decomposition preserves the core meaning for graph/text comparison.
- Do not demand philosophical completeness.
- Focus on whether the decomposition supports reasonable similarity judgments.

## 2. Pair similarity labels

Labels:

- `equivalent`: same concept or standard alias.
- `near`: same broad concept class and close subtype, but not equivalent.
- `related`: meaningful domain relation, but different concept.
- `different`: no useful semantic overlap for evaluation.

Examples:

```text
UCVA — uncorrected visual acuity: equivalent
myopia — astigmatism: near
drug — disease: related
myopia — birthPlace: different
```

Expert output columns:

```text
left, right, label, confidence, comment
```

## 3. MINE judge validation

Input:

```text
fact, retrieved_subgraph, llm_judge_answer
```

Expert question:

> Can the fact be inferred from the subgraph alone?

Answers:

- `yes`
- `no`
- `unclear`

Expert output columns:

```text
fact_id, human_answer, confidence, judge_error_type, notes
```

Judge error types:

- `retrieval_failure`
- `judge_false_positive`
- `judge_false_negative`
- `ambiguous_fact`
- `insufficient_subgraph_context`

## 4. Error analysis categories

Use these categories in `reports/error_cases.csv`:

- `wrong_factor`
- `missing_factor`
- `too_generic_factor`
- `too_specific_factor`
- `wrong_role`
- `biomedical_type_error`
- `numeric_unit_mismatch`
- `mine_retrieval_failure`
- `mine_judge_failure`
- `dataset_conversion_error`
