# LEMON-Factor

LEMON-Factor is a SPECOM-oriented research prototype for **factor-level graph-text semantic fidelity**. It evaluates whether a text preserves the semantic commitments of graph predicates and whether a reconstructed graph can recover those commitments from text.

The current paper is deliberately narrow: it is about **graph-text alignment when an explicit source graph or relation inventory is available**. It is not a general text-text similarity system and it does not claim to replace semantic embeddings, AMR metrics, or expert human validation.

## Current scope

```text
source graph / relation annotation + text
        -> unified GraphText records
        -> predicate factor inventory
        -> forward KG->Text factor coverage
        -> reverse Text->KG recoverability diagnostics
        -> perturbation, ablation, and MINE-style comparisons
```

A predicate is treated as a small bundle of typed semantic factors. For example, `birthPlace` contains a person-like subject, a biographical relation, and a place-like object; biomedical predicates may encode chemical/protein roles, directed effects, polarity, causality, and evidence cues.

## What the method does

- Decomposes graph predicates into weighted semantic factors.
- Scores how well predicate factors are expressed in text.
- Scores how well source predicate factors survive in a reconstructed graph.
- Gives partial credit when entities survive but relation meaning is weakened or lost.
- Produces an auditable trace: missing role, missing relation cue, wrong direction, missing polarity, weak evidence, etc.
- Compares this factor view with exact entity/triple signals and a MINE-style node/edge baseline.

## What it does not claim

- It is not a universal theory of meaning.
- It is not a general-purpose text-text semantic similarity metric.
- It is not a full text-to-KG extractor.
- It is not a reproduction of the original KGGen/MINE benchmark.
- It does not currently handle pragmatics such as irony, implicature, or presupposition.
- It does not replace expert validation of predicate factor inventories.

## Repository layout

```text
src/lemon_factor/        Core package: schema, factors, metrics, datasets, baselines
paper/                   SPECOM/LNCS paper draft, tables, figures, references
docs/                    Roadmap, claims audit, annotation instructions, milestone notes
annotation/              Lightweight expert-review templates
reports/                 Generated metric summaries and experiment reports
configs/                 LLM model/adjudicator configs
scripts/                 Utility scripts
tests/                   Pytest test suite
```

Key documentation:

- `docs/ROADMAP.md` - current near-term roadmap.
- `docs/REPRODUCIBILITY.md` - exact local commands, expected outputs, and known warnings.
- `docs/SUBMISSION_CHECKLIST.md` - paper/package checks before SPECOM submission.
- `docs/CLAIMS_AND_METRICS_AUDIT.md` - safe wording for claims and metric caveats.
- `docs/LINGUIST_VALIDATION.md` - compact task description for expert predicate validation.
- `docs/annotation_guidelines.md` - older, broader annotation notes.
- `docs/reference_sources.md` - external datasets and baseline references.

## Quick start

Install in editable mode with development and research dependencies:

```bash
python -m pip install -e ".[dev,research]"
```

Run the test suite:

```bash
python -m pytest -q
```

Regenerate the vector baseline and radar profile from the repository root:

```bash
python scripts/run_embedding_baseline.py
```

```bash
python scripts/make_radar_profile.py
```

Build the paper:

```bash
cd paper
```

```bash
latexmk -pdf -interaction=nonstopmode main.tex
```

For the complete command sequence, expected outputs, and known warnings, see `docs/REPRODUCIBILITY.md`. For final paper/package checks, see `docs/SUBMISSION_CHECKLIST.md`.

## Reproducing the current paper artifacts

Most paper-ready results are already materialized in `reports/` and `paper/tables/`. The current paper uses these generated artifacts rather than requiring every upstream dataset conversion to be rerun.

Important report files:

```text
reports/scoring_webnlg.json
reports/scoring_drugprot.json
reports/scoring_bc5cdr.json
reports/paper_metric_sensitivity_drops.json
reports/paper_ablation_gain.json
reports/paper_llm_reliability_compact.json
reports/llm_reliability_summary_3judges.json
reports/metric_radar_comparison.json
reports/radar_diagnostic_profile_values.json
reports/embedding_baseline_perturbation.json
reports/mine1_like_lemon_pilot.json
reports/triple_f1_baseline.json
```

Important paper files:

```text
paper/main.tex
paper/sections/*.tex
paper/tables/*.tex
paper/figures/*.tex
```

## Current main findings

The current draft supports a restricted graph-text fidelity claim:

- Forward LEMON-Factor on WebNLG: `0.7915`.
- Reverse LEMON-Factor on WebNLG: `0.7789`.
- Relation-evidence deletion barely changes exact entity-label coverage (`-0.0020`) but reduces Forward LEMON-Factor by `-0.2106`.
- Node information is easier to recover than edge information in the MINE-style comparison.
- Controlled perturbations show that LEMON-Factor reacts only to dimensions represented in the factor inventory; for example, polarity sensitivity is expected only where polarity is encoded.
- LLM judges are used as an exploratory recoverability probe, not as gold validation.
- The offline vector-space perturbation baseline keeps cosine similarity very high under most controlled edits; it is a topical/lexical reference signal, not a complete dense-embedding comparison.

## Expert validation

A compact expert-validation pack is available for a 2--3 day review. The easiest reviewer-facing version is the Excel folder:

```text
annotation/linguist_review_pack/
annotation/linguist_review_pack/expert_validation_form.xlsx
```

The workbook contains 50 predicate-factor rows: 36 WebNLG, 12 DrugProt, and 2 BC5CDR examples. The expert only fills the yellow columns and checks whether the proposed factors are correct, sufficient, and role/direction/polarity-safe. The general protocol is documented in `docs/EXPERT_VALIDATION_PACK.md`. The source CSV remains available at `annotation/expert_validation_sample.csv`; the older minimal template remains available at `annotation/linguist_predicate_review_template.csv`.

## Near-term development sequence

Completed stabilization steps:

1. Narrow paper positioning and documentation.
2. Compact layer/profile table.
3. Radar/spider chart based on perturbation-drop values.
4. Offline vector-space perturbation baseline.
5. Radar extension with MINE-style and Vector cosine traces.
6. Expert-validation workbook prepared for a 2--3 day review.
7. Paper narrative/style audit while preserving the 15-page limit.
8. Reproducibility and submission-readiness documentation.

Remaining before submission:

1. Final author/affiliation and acknowledgement metadata.
2. Final PDF/source package check.
3. Optional integration of compact expert rates if the linguist review returns in time.

Future work may generalize this into an LLM-assisted layered semantic graph metric for text-text comparison, but the current paper should remain a controlled graph-text fidelity study.
