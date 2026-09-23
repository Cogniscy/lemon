# LEMON

LEMON evaluates lexical evidence for the semantic factors of an explicit graph edge.
It is a research prototype for graph–text diagnostics: scores come with a factor trace.

For the fact `Alex Morgan --birthPlace--> Cedar Bay`, the packaged example scores
“Alex Morgan was born in Cedar Bay” at 1.0 and “Alex Morgan visited Cedar Bay” at 0.55.
It also shows why negation and an unrelated person's birthplace can be false positives.

## Install and try

From a checkout, use Python 3.11 or newer. CI is configured for Python 3.11 and 3.12
on Windows and Linux; see [validation status](docs/IMPLEMENTATION_STATUS.md) for checks actually run.

```bash
python -m venv .venv
```

Activate on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or on Linux/macOS:

```bash
source .venv/bin/activate
```

```bash
python -m pip install .
python -m lemon_factor demo
python -m lemon_factor demo --format json
```

Installation may download dependencies. The installed demo needs no network, model,
API key, dataset or LaTeX, and works from any directory. It does not write files.

## Reproduce a small example

```bash
python -m lemon_factor reproduce-demo --out artifacts/demo
```

This writes `scores.json`, `summary.md` and `manifest.json`, including configuration
and the SHA-256 of the packaged input. Existing outputs require `--overwrite`.
The inputs are original synthetic examples, not a benchmark or a sample of expert annotations.

## What the scores mean

- **Lexical factor coverage** runs on text, names and relation cues. It does not resolve
  negation, reliably bind relation cues to participants, or establish semantic entailment.
- **Factor damage proxy** uses the generator's intended-damage metadata. Its perturbation
  response and ablations describe the prescribed damage model, not independent error detection.
  Older reports call this value `lemon_full`; new reports use `factor_damage_proxy`.
- **Vector cosine** is a separate control. Choose `hashed-char`, `tfidf-char` or
  `sentence-transformers` explicitly. Historical `char_ngram_vector_cosine`
  does not identify which of the former implementation's two algorithms ran.

The [pilot expert review](annotation/expert_trace_review/README.md) includes anonymized
judgments and a reproducible calculation: 119/140 exact matches, ordinal alpha 0.873.
The earlier [50-row inventory preparation workbook](annotation/linguist_review_pack/expert_validation_form.xlsx)
is separate from this 35-row review.
Agreement uses historical LEMON labels supplied to reviewers, not a new scorer run.

## Development and research

```bash
python -m pip install -e ".[dev,plots]"
python -m pytest -q -m "not artifacts"
python -m build
```

Optional extras: `data` (dataset tools), `plots`, `embeddings` (TF-IDF and dense
models), and `research` (the previous combined dependency group).

[Reproducibility](docs/REPRODUCIBILITY.md) separates installed-package examples from
experiments requiring external datasets or historical local reports.
[Result provenance](docs/RESULT_PROVENANCE.md) maps published numbers to inputs and commands.

## Repository

- `src/lemon_factor/`: schemas, lexical coverage, perturbations, baselines and CLI.
- `tests/`: unit fixtures, known-limit tests and optional historical artifact checks.
- `resources/`: research factor inventories; demo resources are included in the package.
- `paper/`: manuscript and historical tables.
- `artifacts/`: new local outputs (ignored by Git).
- [Architecture](docs/ARCHITECTURE.md), [report migration](docs/REPORT_FORMATS.md),
  [historical development notes](docs/archive/README.md).

Citation metadata is in [CITATION.cff](CITATION.cff); the manuscript remains a draft.
Original software is licensed under [Apache-2.0](LICENSE). This covers source code,
scripts, tests and build configuration. Third-party dependencies and datasets retain
their own terms; the software license does not assign publication rights to the manuscript
or license the expert submissions.

## Acknowledgments

The research was financially supported by the Russian Science Foundation (project 26-11-00193).
