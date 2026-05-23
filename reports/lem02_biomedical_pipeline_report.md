# LEM-02 report: biomedical pipeline fix

## Result

LEM-02 passed.  DrugProt examples now contain non-empty text and can be used as
a second-domain biomedical transfer check.  BC5CDR conversion remains valid and
now has the same quality-gate reporting path.

## Generated biomedical subset

| Dataset | Split | Examples | Text chars avg | Predicate types | Edges |
|---|---|---:|---:|---:|---:|
| DrugProt | train | 500 | 1729.5 | 12 | 3588 |
| BC5CDR | train | 500 | 1305.4 | 1 | 985 |
| BC5CDR | dev | 500 | 1294.1 | 1 | 961 |

## Test result

```text
python -m pytest -q
179 passed in 0.50s
```

## Quality gates

```text
DrugProt quality: passed
BC5CDR quality: passed
```

## Notes

- DrugProt direct conversion reuses existing local raw files before trying to
  access Zenodo.
- BC5CDR direct conversion reuses existing local PubTator/BioC files before
  trying to download the GitHub mirror.
- This patch does not make any claim about biomedical SOTA performance.  It only
  validates input data for later LEMON-Factor evaluation.
