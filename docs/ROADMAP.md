# LEMON-Factor Roadmap

## Current paper scope

The SPECOM paper should stay focused on **graph-text semantic fidelity**. LEMON-Factor assumes that a source graph, relation annotation, or predicate inventory is available. It decomposes predicates into semantic factors and checks whether those factors are preserved in text and recoverable in a reconstructed graph.

Current safe claim:

> LEMON-Factor is a factor-level diagnostic metric for relation-level graph-text alignment.

Current unsafe claim:

> LEMON-Factor is a general text-text semantic similarity metric.

## Near-term patch sequence

| Patch | Goal | Main outputs |
|---|---|---|
| `lem17-positioning-docs` | Fix narrow positioning and onboarding docs. | README renovation, claims audit, linguist validation guide, minimal TeX positioning edits. |
| `lem18-layer-profile` | Make the factor layers explicit. | Compact layer/profile table: entity, role, direction, polarity, evidence, causality. |
| `lem19-radar` | Add a radar/spider figure with verified numbers. | Radar figure and caption using real normalized diagnostic values. |
| `lem20-vector-baseline-deps` | Add a reproducible vector-space perturbation baseline and dependency hygiene. | Offline char-ngram cosine report, optional dense sentence-transformer backend, updated docs/tests. |
| `lem21-radar-mine-vector-traces` | Add MINE-style and Vector cosine traces to the radar. | Updated radar figure/JSON, caption, tests, and claims audit. |
| `lem22-expert-validation-pack` | Prepare a compact expert-review package. | 50-row predicate-factor CSV, expert instructions, generation script, tests. |
| `lem23-linguist-excel-pack` | Make expert review practical in Excel. | Reviewer-facing XLSX form and all linguist instructions collected in `annotation/linguist_review_pack/`. |
| `lem24-paper-audit-layout` | Tighten paper narrative, style, claims, future-work paragraph, and references while keeping the 15-page limit. | Revised TeX sections, updated references, audit report, rebuilt PDF. |
| `lem25-reproducibility-pack` | Document exact local reproduction and submission checks. | `docs/REPRODUCIBILITY.md`, `docs/SUBMISSION_CHECKLIST.md`, report, README links. |

## What remains unchanged for now

- No new universal semantic basis.
- No pragmatics experiment.
- No full LLM semantic parser.
- No energy-based model section.
- No general text-text similarity benchmark.

These are future-work directions. The current paper should remain a controlled graph-text diagnostic study.

## Planned improvements

### 1. Positioning and documentation

- Keep the abstract, introduction, limitations, and conclusion consistent with the graph-text fidelity scope.
- Use `MINE-style` or `MINE-inspired`, not `MINE reproduction`.
- State that LLM judges are complementary recoverability probes, not expert validation.

### 2. Layer/profile table

Add a compact table that maps each factor layer to the failure mode it detects:

| Layer | Detects | Example |
|---|---|---|
| Entity/domain | missing participant type | place vs person |
| Role | subject/object role preservation | argument swap |
| Direction | source-to-target relation | chemical affects protein |
| Polarity | activation/inhibition or positive/negative relation | inhibits vs activates |
| Evidence | textual cue for relation | relation phrase deletion |
| Causality | cause/effect relation | disease causes symptom |

### 3. Radar/spider figure

Use only verified values and label the chart as a normalized diagnostic profile, not an accuracy ranking. If values come from heterogeneous reports, the caption must say so.

### 4. Vector and embedding baselines

After the layer/profile table is stable, compare against vector-space similarity on controlled perturbation pairs. The current reproducible baseline is an offline character n-gram cosine; a dense sentence-transformer backend remains optional when model dependencies are available. The point is not to beat embeddings globally, but to show where vector similarity can remain topically high despite relation-level damage.

Radar extension status: MINE-style node/edge and offline Vector cosine traces are included because they share the perturbation-drop scale. Dense embedding traces remain optional and should be added only after the dense backend is explicitly run and materialized.

### 5. Expert validation

Use `annotation/linguist_review_pack/expert_validation_form.xlsx` for the compact 2--3 day review. The source CSV remains `annotation/expert_validation_sample.csv`. The materialized sample has 50 rows: 36 WebNLG, 12 DrugProt, and 2 BC5CDR examples. Report simple rates only:

```text
expert_accept_rate
partly_accept_rate
missing_factor_rate
wrong_or_extra_factor_rate
direction_issue_rate
polarity_issue_rate
```

Do not claim full expert validation of all inventories unless the complete inventories are reviewed.

## Reproducibility commands

Use separate commands for local verification after code or paper changes:

```bash
python -m pytest -q
```

```bash
cd paper
latexmk -pdf -interaction=nonstopmode main.tex
```


## LEM-19 radar diagnostic profile

Status: implemented as a compact Results figure based on `reports/radar_diagnostic_profile_values.json`. The figure is a diagnostic perturbation-sensitivity profile, not an accuracy leaderboard.

## LEM-20 vector-space perturbation baseline

Status: implemented in `scripts/run_embedding_baseline.py` and `reports/embedding_baseline_perturbation.json`. The default backend is an offline character n-gram vector cosine for reproducibility; dense sentence-transformer cosine can be run explicitly with `--backend sentence-transformers` when the optional model dependency and model files are available.


## LEM-21 radar with MINE-style and Vector cosine traces

Status: implemented as an extension of `reports/radar_diagnostic_profile_values.json` and `paper/figures/figure_radar_diagnostic_profile.*`. The figure now includes LEMON-Factor, MINE-style node/edge, triple match, entity recall, and Vector cosine. Vector cosine refers to the offline character n-gram baseline unless a dense backend report is explicitly generated.


## LEM-22 expert validation pack

Status: prepared as `annotation/expert_validation_sample.csv` with 50 review rows and `docs/EXPERT_VALIDATION_PACK.md` with one-page instructions. A reviewer-facing Excel folder is available at `annotation/linguist_review_pack/`, including `expert_validation_form.xlsx`, `README.md`, `FIELD_GUIDE.md`, and `RETURN_FORMAT.md`. The pack is designed for a realistic 2--3 day review. It should support only compact aggregate rates unless expanded to the full inventory.


## LEM-24 paper audit and layout

Status: implemented. The paper narrative was tightened around the relation-level failure mode, the abstract/introduction/results/conclusion were edited for a more direct scientific voice, the radar caption remains explicitly non-leaderboard, and the references now include recent LLM graph-to-text work. The PDF remains at 15 pages with no undefined references or citations.


## LEM-25 reproducibility and submission-readiness pack

Status: implemented. The default reproduction path is now documented in `docs/REPRODUCIBILITY.md`, and final submission checks are collected in `docs/SUBMISSION_CHECKLIST.md`. Python scripts should be run from the repository root. The default local path regenerates the expert-validation CSV, the offline vector baseline, the radar profile, the pytest suite, and the LNCS PDF. Remote LLM/OpenRouter runs and returned expert annotations remain outside the default path.
