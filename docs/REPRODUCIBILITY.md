# Reproducibility guide

This guide records the shortest reliable path for reproducing the current SPECOM paper artifacts. It is written for a fresh local checkout after the generated reports and data files have already been included in the repository.

The current paper is a graph-text diagnostic study. The commands below reproduce the materialized paper artifacts; they do not rerun every historical data-conversion or LLM experiment.

## Environment

Use Python 3.11 or newer.

From the repository root, install the package with development and research dependencies:

```bash
python -m pip install -e ".[dev,research]"
```

The research dependency group includes the libraries needed by the radar and vector-space baseline scripts:

```text
matplotlib
scikit-learn
numpy
pandas
sentence-transformers
```

The default vector baseline does not download a dense model. The `sentence-transformers` backend is optional and should only be used when the model files are available.

For the paper build, install a LaTeX distribution with `latexmk` and the LNCS class.

## Repository-root convention

Run Python scripts from the repository root. For example:

```bash
python scripts/make_radar_profile.py
```

Do not run that command from `paper/`; relative paths are resolved from the repository root.

## Minimal verification

Run the test suite:

```bash
python -m pytest -q
```

Expected result in the current repository state:

```text
all tests pass
```

The exact count may change as tests are added. In the LEM-25 local check it was `225 passed`.

## Regenerate the expert-validation CSV

The reviewer-facing Excel workbook is stored under `annotation/linguist_review_pack/`. The source CSV can be regenerated with:

```bash
python scripts/build_expert_validation_pack.py
```

Expected output:

```text
annotation/expert_validation_sample.csv
```

The generated sample should contain 50 review rows: 36 WebNLG, 12 DrugProt, and 2 BC5CDR examples.

## Regenerate the vector-space perturbation baseline

Run:

```bash
python scripts/run_embedding_baseline.py
```

Expected outputs:

```text
reports/embedding_baseline_perturbation.json
reports/embedding_baseline_perturbation.md
```

The default backend is `char_ngram_vector_cosine`, an offline character n-gram vector cosine. It is a reproducible lexical/topical control, not a dense semantic embedding benchmark.

Optional dense backend:

```bash
python scripts/run_embedding_baseline.py --backend sentence-transformers
```

Only use the dense backend when `sentence-transformers` and the selected model files are available. Do not mix dense and offline-vector results without naming the backend in the report.

## Regenerate the radar profile

Run the vector baseline first, then:

```bash
python scripts/make_radar_profile.py
```

Expected outputs:

```text
reports/radar_diagnostic_profile_values.json
paper/figures/figure_radar_diagnostic_profile.pdf
paper/figures/figure_radar_diagnostic_profile.png
```

The radar is a perturbation-sensitivity profile. Values are mean drops under controlled edits. They are not absolute accuracy scores and not a global leaderboard.

## Build the paper

From the repository root:

```bash
cd paper
```

```bash
latexmk -pdf -interaction=nonstopmode main.tex
```

Expected output:

```text
paper/main.pdf
```

The current SPECOM/LNCS draft is expected to remain within 15 pages. After references or labels change, `latexmk` may run `pdflatex` more than once; that is normal.

## Full local check

A compact end-to-end local check is:

```bash
python scripts/build_expert_validation_pack.py
```

```bash
python scripts/run_embedding_baseline.py
```

```bash
python scripts/make_radar_profile.py
```

```bash
python -m pytest -q
```

```bash
cd paper
```

```bash
latexmk -pdf -interaction=nonstopmode main.tex
```

## Paper-ready generated files

The paper reads compact generated artifacts from `reports/`, `paper/tables/`, and `paper/figures/`. The most important files are:

```text
reports/scoring_webnlg.json
reports/scoring_drugprot.json
reports/scoring_bc5cdr.json
reports/paper_metric_sensitivity_drops.json
reports/paper_ablation_gain.json
reports/paper_llm_reliability_compact.json
reports/llm_reliability_summary_3judges.json
reports/radar_diagnostic_profile_values.json
reports/embedding_baseline_perturbation.json
paper/figures/figure_radar_diagnostic_profile.pdf
paper/tables/table_layer_profile.tex
paper/tables/table_perturbation_sensitivity_drop.tex
paper/tables/table_ablation_gain.tex
paper/tables/table_llm_reliability.tex
```

## Known warnings

The LaTeX build may report minor LNCS layout warnings, mostly overfull or underfull boxes from compact tables, formulas, and reference entries. These warnings are acceptable only if the rendered PDF has no clipped text, missing figures, broken references, or undefined citations.

A clean submission build should satisfy:

```text
no undefined citations
no undefined references
paper/main.pdf opens correctly
paper/main.pdf has 15 pages or fewer
```

## What is not reproduced by the default commands

The default commands do not rerun paid or remote LLM calls. The LLM reliability probe is reported from materialized files. OpenRouter-dependent experiments require configured credentials and should be treated as optional.

The default commands also do not claim expert validation results. The expert workbook is a prepared review pack; validation rates should be reported only after the returned workbook is summarized.
