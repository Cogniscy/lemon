# LEM-21: Radar with MINE-style and Vector cosine traces

## Goal

Extend the diagnostic radar profile with two additional traces while preserving the interpretation of the figure as a perturbation-sensitivity profile, not an accuracy leaderboard.

Added traces:

- `MINE-style`: the local node/edge perturbation baseline from `reports/paper_metric_sensitivity_drops.json`.
- `Vector cosine`: the offline character n-gram vector baseline from `reports/embedding_baseline_perturbation.json`.

## Implemented files

- `scripts/make_radar_profile.py`
- `reports/radar_diagnostic_profile_values.json`
- `paper/figures/figure_radar_diagnostic_profile.pdf`
- `paper/figures/figure_radar_diagnostic_profile.png`
- `paper/sections/06_results.tex`
- `tests/test_radar_profile_values.py`
- `docs/CLAIMS_AND_METRICS_AUDIT.md`
- `docs/ROADMAP.md`

## Radar traces

All values use the same perturbation-drop interpretation: larger values mean stronger response to the induced perturbation.

| Trace | Source | Interpretation |
|---|---|---|
| LEMON-Factor | `reports/paper_metric_sensitivity_drops.json` | Factor-level diagnostic response. |
| MINE-style | `reports/paper_metric_sensitivity_drops.json` | Local node/edge perturbation response. |
| Triple match | `reports/paper_metric_sensitivity_drops.json` | Coarse relation/fact detector. |
| Entity recall | `reports/paper_metric_sensitivity_drops.json` | Entity-level preservation signal. |
| Vector cosine | `reports/embedding_baseline_perturbation.json` | Offline char-ngram vector-space response. |

## Values

| Perturbation | LEMON-Factor | MINE-style | Triple match | Entity recall | Vector cosine |
|---|---:|---:|---:|---:|---:|
| Node deletion | 0.3524 | 0.6575 | 0.6745 | 0.3259 | 0.0145 |
| Edge deletion | 0.2808 | 0.6367 | 0.6547 | 0.2154 | 0.0035 |
| Argument swap | 0.4127 | 0.5207 | 0.5399 | 0.2143 | 0.0039 |
| Polarity flip | 0.4138 | 0.5264 | 0.5463 | 0.2154 | 0.0012 |
| Relation blur | 0.2808 | 0.5495 | 0.5676 | 0.2159 | 0.0049 |

## Safe interpretation

The expanded radar shows that MINE-style and triple matching behave as stronger coarse perturbation detectors, while Vector cosine remains near zero under most controlled edits. LEMON-Factor is not always the harshest scalar response; its intended role is the factor-level trace that attributes the response to roles, polarity, direction, or evidence when encoded in the inventory.

## Do not claim

- Do not present the radar as an accuracy leaderboard.
- Do not call Vector cosine a dense embedding unless the dense backend was explicitly run.
- Do not claim global superiority over embeddings from this figure.
- Do not claim universal polarity handling; polarity remains inventory-dependent.

## Commands run

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
