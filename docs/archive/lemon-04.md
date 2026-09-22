# lemon-04 — Seed semantic factor schema and predicate decompositions

## Goal

Create the first deterministic semantic factor schema and seed decompositions for top WebNLG predicates. This stage turns the shallow candidate tokens produced in `lemon-03` into a controlled, role-aware semantic representation.

## Research contribution

`lemon-04` is the first implementation of the LEMON-Factor semantic layer:

```text
predicate inventory
  → controlled semantic factors
  → role-aware predicate decompositions
  → expert-review table
```

The key distinction is:

- **candidate factors** are lexical pieces from predicate names, e.g. `birthPlace → birth, place`;
- **semantic factors** are controlled directions, e.g. `biographical_relation`, `person`, `place`;
- **predicate decompositions** connect predicates to weighted semantic factors and roles.

This supports the paper claim that graph/text comparison should not be limited to string overlap or raw embeddings. A predicate can be compared through preserved roles and semantic components.

## Inputs

Expected input from `lemon-03`:

```text
data/interim/webnlg_factor_inventory.json
```

If needed, recreate it:

```bash
python -m lemon_factor.factors.inventory_cli \
  data/processed/webnlg_train.jsonl \
  --out data/interim/webnlg_factor_inventory.json \
  --summary data/reports/webnlg_factor_inventory_summary.json
```

## Outputs

```text
data/interim/factor_schema_seed.json
data/interim/webnlg_predicate_decompositions_seed.json
data/annotation/predicate_decomposition_review.csv
paper/tables/table_factor_schema_seed.md
paper/tables/table_predicate_decompositions_seed.md
```

## Code added

```text
src/lemon_factor/factors/decomposition.py
src/lemon_factor/factors/seed_schema.py
src/lemon_factor/factors/seed_builder.py
src/lemon_factor/factors/review_export.py
src/lemon_factor/analysis/factor_schema_tables.py
```

## Main commands

Build seed schema and decompositions:

```bash
python -m lemon_factor.factors.seed_builder \
  data/interim/webnlg_factor_inventory.json \
  --schema-out data/interim/factor_schema_seed.json \
  --decompositions-out data/interim/webnlg_predicate_decompositions_seed.json \
  --top-k 50
```

Export expert-review CSV:

```bash
python -m lemon_factor.factors.review_export \
  data/interim/webnlg_predicate_decompositions_seed.json \
  --out data/annotation/predicate_decomposition_review.csv
```

Export paper tables:

```bash
python -m lemon_factor.analysis.factor_schema_tables \
  --schema data/interim/factor_schema_seed.json \
  --decompositions data/interim/webnlg_predicate_decompositions_seed.json \
  --schema-out paper/tables/table_factor_schema_seed.md \
  --decompositions-out paper/tables/table_predicate_decompositions_seed.md
```

Run tests:

```bash
python -m pytest
```

## Seed factor schema

The first schema contains universal/domain factors and abstract relation factors, including:

```text
entity
person
place
organization
creative_work
event
time
quantity
measurement
language
identifier
entity_relation
biographical_relation
location_relation
part_whole_relation
membership_relation
political_relation
creative_relation
organizational_relation
astronomical_relation
sports_relation
transport_relation
language_relation
identifier_relation
```

Each factor defines allowed roles such as:

```text
subject_domain
object_domain
predicate_meaning
modifier
value_domain
background
```

## Predicate decomposition format

Example:

```json
{
  "predicate": "birthPlace",
  "components": [
    {"factor": "biographical_relation", "role": "predicate_meaning", "weight": 0.5},
    {"factor": "person", "role": "subject_domain", "weight": 0.2},
    {"factor": "place", "role": "object_domain", "weight": 0.3}
  ],
  "source": "seed_rule",
  "confidence": 0.82
}
```

Weights are validated and must sum to `1.0`. Components are also validated against the schema: an unknown factor id or a disallowed role is rejected.

## Rule coverage

The seed builder maps top predicates using deterministic rules:

| Predicate evidence | Relation factor |
|---|---|
| `birth*`, `death*`, `nationality`, `occupation` | `biographical_relation` |
| `location`, `country`, `city`, `capital`, `region` | `location_relation` or `political_relation` |
| `isPartOf`, `part` | `part_whole_relation` |
| `leader`, `mayor`, `chief`, `leaderTitle` | `political_relation` |
| `club`, `team`, `affiliation`, `associatedBand` | `membership_relation` or `creative_relation` |
| `creator`, `author`, `artist`, `musical`, `genre` | `creative_relation` |
| `orbitalPeriod`, `epoch` | `astronomical_relation` |
| `runway*`, `elevation*`, `length`, `feet` | `transport_relation` |
| `language` | `language_relation` |
| `identifier`, `icao` | `identifier_relation` |
| unknown | `entity_relation` fallback |

## Expert review

The review CSV is designed for manual validation. Required expert columns:

```text
expert_label
missing_factor
wrong_factor
weight_comment
notes
```

Expert labels should use:

```text
accept
minor_fix
major_fix
reject
```

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Schema is still hand-built | It is explicitly named `seed`; later steps add expert review and optional LLM candidates |
| Predicate rules overfit WebNLG | BioRED is planned as external biomedical validation |
| Candidate tokens are mistaken for real meaning | Candidate tokens are stored only as evidence, not as final semantic factors |
| Weights are arbitrary | Weights are initial priors and exported for expert correction |
| Decompositions are wrong for ambiguous predicates | Store category evidence, contexts, and confidence |

## Acceptance criteria

The stage is complete when:

1. `python -m pytest` passes.
2. `factor_schema_seed.json` is created.
3. `webnlg_predicate_decompositions_seed.json` is created.
4. All decompositions validate against the schema.
5. Expert-review CSV is created.
6. Markdown tables for the paper are created.
7. Documentation clearly distinguishes candidate factors from semantic factors.

## Next stage

`lemon-05` should add an optional OpenRouter-backed LLM candidate generator. It should not replace this deterministic seed schema. LLM outputs must be treated as candidate decompositions for expert review.
