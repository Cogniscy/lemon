# Reproducibility

## Installed package

After `python -m pip install .`, these commands work outside the checkout:

```bash
python -m lemon_factor demo
python -m lemon_factor demo --format json
python -m lemon_factor reproduce-demo --out artifacts/demo
```

The final command saves the actual scores, summary and input/configuration manifest.
It is a deterministic synthetic demonstration, not reproduction of the paper.
Add `--overwrite` only when replacing those three output files is intended.

## Tests and distribution

From the checkout:

```bash
python -m pip install -e ".[dev,plots]"
python -m pytest -q -m "not artifacts"
python -m pytest -q -m artifacts
python -m build
```

Artifact tests list required historical files and skip only when they are absent.
Their results do not establish completeness of the paper's source data.
Two strict expected failures document unresolved negation and participant-binding
limitations. An unexpected pass requires removing the corresponding xfail.

CI builds wheel and sdist and runs `scripts/smoke_installed.py` with the Python
from an independent wheel installation outside the checkout. The smoke test
checks CLI output, resource inclusion and network-free execution.
The workflow targets Windows/Linux and Python 3.11/3.12.
Local validation and remaining gaps are recorded in [status](IMPLEMENTATION_STATUS.md).

## Recomputing research results

Install only the extras needed by an experiment. The old `.[research]` aggregate
remains available, but is not required for the demo.

The following commands require prepared data; a fresh clone does not include all
processed JSONL files or historical JSON reports. See [provenance](RESULT_PROVENANCE.md)
before running them. New outputs are separated from historical reports.

Example scoring of a prepared DrugProt perturbation file:

```bash
python -m lemon_factor.scoring.score_perturbations --input data/biomedical/perturbed/drugprot_perturbed.jsonl --inventory resources/factors/drugprot.json --out artifacts/scoring_drugprot.json --table-out artifacts/scoring_drugprot.md
```

This computes the **factor damage proxy** from metadata, alongside lexical baselines.

Explicit vector control over a prepared file:

```bash
python scripts/run_embedding_baseline.py --backend hashed-char --limit-per-variant 10 data/biomedical/perturbed/drugprot_perturbed.jsonl
```

Outputs default to `artifacts/embedding_baseline_perturbation.json` and `.md`.
For TF-IDF, install `.[embeddings]` and choose `--backend tfidf-char`.
Dense models require `--backend sentence-transformers` and model availability;
that command can download weights.

Recompute compact tables from historical scoring, ablation and judge reports:

```bash
python -m lemon_factor.analysis.recompute_paper_aggregates --scoring reports/scoring_webnlg.json reports/scoring_drugprot.json reports/scoring_bc5cdr.json --ablation reports/ablation_summary.json --llm reports/llm_reliability_summary_3judges.json --out-dir artifacts/recomputed --table-dir artifacts/recomputed/tables
```

Generate a revised diagnostic profile using those aggregates and a new vector report:

```bash
python scripts/make_radar_profile.py --perturbation artifacts/recomputed/paper_metric_sensitivity_drops.json --embedding artifacts/embedding_baseline_perturbation.json --layer-profile reports/layer_profile_values.json
```

The layer profile is historical context and must be supplied. Plotting uses Agg,
so no graphical desktop or Tk is needed.

## Expert data and manuscript

The 50-row inventory preparation workbook in `annotation/linguist_review_pack/`
is retained. It must not be confused with the paper's 35-row trace review.
Four completed submissions are now included as anonymized judgments in
`annotation/expert_trace_review/ratings.csv`. Recompute all agreement coefficients:

```bash
python -m lemon_factor.analysis.expert_review --ratings annotation/expert_trace_review/ratings.csv --out artifacts/expert-review
```

The output directory must be new. Exact agreement is 119/140; ordinal alpha is
0.873. The historical 0.871 is the interval-rank coefficient. Both are calculated
explicitly and independently checked against the `krippendorff` implementation.
The script uses historical LEMON labels from the forms, not a fresh scorer run.
No replacement or synthetic annotations have been created.

Building the manuscript requires an external LaTeX distribution, LNCS class
and all included figure files:

```bash
cd paper
latexmk -pdf -interaction=nonstopmode main.tex
```

The revised source was built and checked on 2026-09-22 (14 pages, no overfull boxes).
The reviewed output is artifacts/paper/lemon-reviewed.pdf. The tracked historical PDF is preserved.

## Environment records

`constraints/demo-windows-py311.txt` pins the runtime used for local wheel
validation. It is deliberately limited to the demo/runtime, not a claim that all
research experiments or other platforms were reproduced. The CI workflow is configured
for fresh resolution; remote execution is pending. The deterministic scoring/plot
environment below has been verified, while acquisition and model dependencies have not.

## Verified prepared-data replay (2026-09-22)

On Windows CPython 3.11, install deterministic scoring/plot dependencies with:

```bash
python -m pip install -c constraints/deterministic-windows-py311.txt ".[plots]"
python scripts/reproduce_local_research.py --reports reports/scoring_webnlg.json reports/scoring_drugprot.json reports/scoring_bc5cdr.json --out artifacts/research-replay
```

The output directory must be new or empty. The script reads the recorded input,
inventory and sample count from each historical report, recomputes all scores,
compares every row and summary, and writes an input-hash manifest and ablations.
A mismatch fails the command. The verified local replay matched all 5,045 rows.
This does not reproduce upstream acquisition, LLM calls or human annotations.
The required local input reports and prepared corpora are not in a fresh clone.

The source snapshot without ignored files passed on Windows Python 3.11 and 3.12:
230 passed, 3 historical-artifact skips, 2 documented expected failures.
The revised manuscript was built and visually checked at the affected tables:
14 pages, no overfull boxes or undefined references. Reviewed PDF:
`artifacts/paper/lemon-reviewed.pdf` (local output; the tracked historical PDF is preserved).
