# Linguistic Validation Task: Predicate Factors

## Purpose

We are developing a metric that checks whether a text preserves the meaning of graph relations. Instead of treating a graph predicate as one atomic label, we decompose it into several semantic factors.

Example:

```text
Marie Curie -- birthPlace -- Warsaw
Text: Marie Curie was born in Warsaw.
Predicate factors: person-like subject; biographical/birth relation; place-like object
```

The validation task is to check whether the proposed factor decompositions are linguistically sensible and useful for graph-text semantic fidelity evaluation.

## What you review

For each predicate, you will see:

- the predicate name;
- the dataset/domain;
- one example graph triple;
- one text example;
- the proposed semantic factors.

You do not need to validate the whole paper, the datasets, or the metric formula. Focus only on the predicate decomposition.

## Main question

> Are the proposed factors sufficient and correct for checking whether the relation meaning is preserved in text?

## Annotation fields

Use the template:

```text
annotation/linguist_predicate_review_template.csv
```

Columns:

| Column | Meaning |
|---|---|
| `predicate` | Relation name, e.g. `birthPlace`, `inhibits`, `causes`. |
| `domain` | Dataset/domain: WebNLG, DrugProt, BC5CDR, etc. |
| `example_triple` | Example graph triple. |
| `example_text` | Text that verbalizes or mentions the relation. |
| `proposed_factors` | Proposed decomposition into semantic factors. |
| `verdict` | `yes`, `partly`, `no`, or `unsure`. |
| `missing_or_wrong` | Short note: missing factor, wrong factor, too broad, too narrow. |
| `direction_ok` | `yes`, `no`, or `n/a`. Does the decomposition preserve who acts on whom? |
| `polarity_ok` | `yes`, `no`, or `n/a`. Is activation/inhibition/negation/positive-negative direction correct? |
| `suggested_fix` | A concise corrected factor list if needed. |
| `comment` | Optional free comment. |

## Verdict policy

- `yes`: the factor list is good enough for evaluation.
- `partly`: the core is right, but a factor is missing, unclear, or slightly wrong.
- `no`: the decomposition misrepresents the predicate.
- `unsure`: the example or predicate is ambiguous.

Do not require philosophical completeness. The factors only need to capture the relation meaning well enough to judge graph-text preservation.

## What counts as a useful factor

Good factors usually capture:

- participant roles: person, place, chemical, disease, gene/protein;
- relation type: birth, location, inhibition, treatment, causation;
- direction: subject affects object, source to target, cause to effect;
- polarity: activation vs inhibition, positive vs negative regulation;
- evidence form: whether the text must contain a relation cue such as "born in", "inhibits", "causes".

## Examples

### Good decomposition

| Field | Value |
|---|---|
| `predicate` | `birthPlace` |
| `domain` | WebNLG |
| `example_triple` | `Marie Curie -- birthPlace -- Warsaw` |
| `example_text` | `Marie Curie was born in Warsaw.` |
| `proposed_factors` | `person-like subject; birth/biographical relation; place-like object` |
| `verdict` | `yes` |
| `direction_ok` | `yes` |
| `polarity_ok` | `n/a` |

### Problematic decomposition

| Field | Value |
|---|---|
| `predicate` | `inhibits` |
| `domain` | DrugProt |
| `example_triple` | `Drug A -- inhibits -- Protein B` |
| `example_text` | `Drug A inhibits the activity of Protein B.` |
| `proposed_factors` | `chemical actor; protein target; interaction; positive regulation` |
| `verdict` | `partly` |
| `missing_or_wrong` | `positive regulation is wrong; should be negative regulation/suppression` |
| `direction_ok` | `yes` |
| `polarity_ok` | `no` |
| `suggested_fix` | `chemical actor; protein target; inhibitory interaction; negative regulation; directed effect` |

## Expected output

A completed CSV file with short, direct comments. One or two phrases per problem are enough.
