# Expert Validation Pack: Predicate Factors

## Purpose

This pack asks an expert to review whether LEMON-Factor predicate decompositions are semantically correct and useful for graph-text fidelity evaluation.

The task is intentionally small. It is designed to be completed in **2--3 days** and to support a compact validation statement in the paper if the completed annotations are available in time.

## Files to use

```text
annotation/linguist_review_pack/expert_validation_form.xlsx
```

This is the main reviewer-facing file. It has separated columns, dropdowns, frozen headers, instructions, and a summary sheet. The source CSV remains available at:

```text
annotation/expert_validation_sample.csv
``` It contains 50 rows:

| Domain | Rows | Why included |
|---|---:|---|
| WebNLG | 36 | Common open-domain RDF predicates and diverse relation types. |
| DrugProt | 12 | Observed biomedical chemical--gene/protein relation types. |
| BC5CDR | 2 | Chemical-induced disease examples with document-level causality. |

## What the expert reviews

One row = one predicate factorization in context.

The expert sees:

```text
predicate
example_triple
example_text
proposed_factors
```

The expert does **not** need to review the paper, run code, inspect metric scores, or validate the full dataset.

## Main question

> Are the proposed factors correct and sufficient for checking whether the predicate meaning is preserved in text?

The factors should capture the important semantic commitments of the predicate: participant type, relation meaning, role/direction, polarity when relevant, and evidence type when relevant. They do not need to be philosophically complete.

## Fields to fill

Use short answers. Empty comment fields are acceptable when the row is clearly correct.

| Column | Allowed / expected value | Meaning |
|---|---|---|
| `verdict` | `yes`, `partly`, `no`, `unclear` | Overall quality of the factorization. |
| `missing_factors` | free text or empty | Important factor missing from the decomposition. |
| `wrong_or_extra_factors` | free text or empty | Factor that is wrong, misleading, too broad, too narrow, or unnecessary. |
| `direction_or_role_ok` | `yes`, `partly`, `no`, `not_applicable` | Whether subject/object roles and direction are represented correctly. |
| `polarity_ok` | `yes`, `partly`, `no`, `not_applicable` | Whether positive/negative, activation/inhibition, or causality polarity is correct. |
| `suggested_fix` | free text or empty | Concise corrected factor list or edit. |
| `comment` | free text or empty | Any other short note. |

## Verdict policy

- `yes`: good enough for graph-text fidelity evaluation.
- `partly`: mostly correct, but something is missing, unclear, too broad, or slightly wrong.
- `no`: the decomposition misrepresents the predicate.
- `unclear`: the predicate or example is ambiguous, or the expert cannot judge confidently.

## Examples

### Good row

```text
predicate: birthPlace
example_triple: Marie Curie | birthPlace | Warsaw
example_text: Marie Curie was born in Warsaw.
proposed_factors: person [subject_domain]; biographical_relation [predicate_meaning]; place [object_domain]

verdict: yes
missing_factors:
wrong_or_extra_factors:
direction_or_role_ok: yes
polarity_ok: not_applicable
suggested_fix:
comment:
```

### Problematic row

```text
predicate: chemical_inhibits_gene_or_protein
example_triple: Drug A | chemical_inhibits_gene_or_protein | Protein B
example_text: Drug A inhibits Protein B.
proposed_factors: chemical [subject_domain]; gene_or_protein [object_domain]; activation_relation [predicate_meaning]; positive_polarity [modifier]

verdict: no
missing_factors: inhibition / negative regulation
wrong_or_extra_factors: activation_relation and positive_polarity are wrong
direction_or_role_ok: yes
polarity_ok: no
suggested_fix: replace activation_relation with inhibition_relation; replace positive_polarity with negative_polarity
comment:
```

## What not to do

Do not spend time on:

- metric formulas;
- LEMON scores;
- radar plots;
- MINE or vector baselines;
- LLM judge outputs;
- weight calibration, unless a weight is obviously absurd.

The current task validates the **factor set**, not the whole evaluation framework.

## How the completed file can be summarized

After annotation, use simple aggregate diagnostics:

```text
expert_accept_rate
partly_accept_rate
missing_factor_rate
wrong_or_extra_factor_rate
direction_issue_rate
polarity_issue_rate
```

Safe paper wording after completion:

> We conducted a compact expert review of 50 predicate-factor decompositions covering WebNLG, DrugProt, and BC5CDR. The review was used to estimate accept, missing-factor, wrong-factor, direction, and polarity issue rates.

Unsafe wording:

> The full factor inventory is expert-validated.

This pack reviews a compact sample, not the full inventory.
