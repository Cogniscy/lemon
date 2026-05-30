# Field guide

## Input columns — do not edit

| Column | Meaning |
|---|---|
| `id` | Row identifier. |
| `domain` | Dataset/domain: WebNLG, DrugProt, or BC5CDR. |
| `predicate` | Graph predicate being reviewed. |
| `review_priority` | Sampling tag used by the project. |
| `example_triple` | Example graph triple: subject, predicate, object. |
| `example_text` | Text where the predicate may be expressed. |
| `proposed_factors` | Proposed factor decomposition. Each factor includes a role and a weight. |

## Editable columns — fill these

| Column | How to fill |
|---|---|
| `verdict` | Use `yes`, `partly`, `no`, or `unclear`. |
| `missing_factors` | Write semantic factors that should be added. Leave empty if none. |
| `wrong_or_extra_factors` | Write factors that are wrong, misleading, or excessive. Leave empty if none. |
| `direction_or_role_ok` | Use `yes`, `partly`, `no`, `not_applicable`, or `unclear`. Checks whether subject/object roles and direction are correct. |
| `polarity_ok` | Use `yes`, `partly`, `no`, `not_applicable`, or `unclear`. Checks activation/inhibition/negative/causal polarity when relevant. |
| `suggested_fix` | Optional short corrected version of the factorization. |
| `comment` | Optional explanation. Keep it short. |

## Review principle

The factorization should be sufficient to distinguish the predicate from close predicates, but it should not over-specify irrelevant details.

Example acceptable factorization:

```text
predicate: birthPlace
proposed_factors: person-like subject; biographical relation; place-like object
verdict: yes
direction_or_role_ok: yes
polarity_ok: not_applicable
```

Example correction:

```text
predicate: chemical_inhibits_gene_or_protein
problem: proposed factor says activation
wrong_or_extra_factors: activation is wrong; should be inhibition / negative regulation
suggested_fix: chemical actor; gene/protein target; inhibition; negative regulation; direction
```

## Do not evaluate

Do not spend time on:

- LEMON formulas;
- radar charts;
- MINE or embedding baselines;
- model quality;
- exact numerical weights, unless the weight notation reveals a clearly wrong factor.
