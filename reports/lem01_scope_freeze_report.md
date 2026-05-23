# LEM-01 Scope and Claims Freeze Report

## Status

Completed.

## Changes made

### Paper text

- Rewrote the abstract to frame LEMON-Factor as a bidirectional factor-level diagnostic framework.
- Rewrote the introduction for clearer academic English and a tighter claim boundary.
- Rewrote the limitations section to distinguish bootstrap resources, synthetic LLM adjudication, MINE-style scoring, and domain-transfer claims.
- Rewrote the conclusion to avoid broad claims and keep future work concrete.

### Contracts added

- `paper/contracts/lem01_claim_checklist.md`
- `paper/contracts/lem01_contribution_contract.md`
- `paper/contracts/lem01_result_contract.md`
- `paper/contracts/lem01_page_budget.md`
- `docs/lem-01-scope-claims-freeze.md`

## Claim boundary fixed

Allowed claims:

- LEMON-Factor is a diagnostic framework.
- Predicate labels can be decomposed into semantic factors.
- The same factor representation supports forward and reverse graph--text checks.
- WebNLG results support a pilot construct-validity claim.
- DrugProt and BC5CDR will be treated as transfer diagnostics, not as biomedical SOTA claims.
- LLM adjudication is synthetic reliability evidence, not human expert validation.

Disallowed claims:

- human-validated metric;
- universal factor taxonomy;
- state-of-the-art biomedical relation extraction;
- full KGGen/MINE reproduction without the official pipeline;
- expert-equivalent LLM judging.

## Validation

### Unit tests

Command:

```bash
python -m pytest -q
```

Result:

```text
176 passed in 1.11s
```

### LaTeX build

Command:

```bash
cd paper && latexmk -pdf -interaction=nonstopmode main.tex
```

Result:

```text
Output written on main.pdf (14 pages, 364015 bytes).
Latexmk: All targets (main.pdf) are up-to-date
```

Known warnings remain non-blocking: a small number of overfull/underfull hbox warnings. No LaTeX build failure was observed.

## Next patch

LEM-02 should fix the biomedical data pipeline and regenerate DrugProt/BC5CDR dataset statistics.
