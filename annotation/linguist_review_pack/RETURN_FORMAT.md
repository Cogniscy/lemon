# Return format

Return one file:

```text
expert_validation_form.xlsx
```

The completed file should preserve the original sheets:

- `Review`
- `Instructions`
- `Legend`
- `Summary`

The main content should be in the yellow columns of the `Review` sheet.

Accepted dropdown values:

```text
verdict: yes | partly | no | unclear
direction_or_role_ok: yes | partly | no | not_applicable | unclear
polarity_ok: yes | partly | no | not_applicable | unclear
```

Free-text columns may be left empty:

```text
missing_factors
wrong_or_extra_factors
suggested_fix
comment
```

Partial completion is acceptable. Leave unfinished rows empty rather than guessing.
