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
| `lem21-expert-validation` | Integrate linguistic validation if available. | Expert accept/missing/wrong-factor rates and short discussion. |
| `lem22-final-specom-compaction` | Fit the paper to SPECOM/LNCS limits. | Final 15-page paper draft and changed-file archive. |

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

Future radar extension: add MINE-style node/edge and vector/embedding traces only if all plotted methods share the same perturbation-drop scale and the caption remains explicit that the chart is diagnostic, not a leaderboard.

### 5. Expert validation

Use `docs/LINGUIST_VALIDATION.md` and `annotation/linguist_predicate_review_template.csv`. Report simple rates only:

```text
expert_accept_rate
missing_or_wrong_factor_rate
direction_error_rate
polarity_error_rate
```

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
