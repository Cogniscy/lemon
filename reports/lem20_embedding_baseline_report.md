# LEM-20: Vector-space perturbation baseline and dependency hygiene

## Goal

Add a reproducible vector-space perturbation baseline and document the dependency needed by the radar script. The baseline is intended as a topical/lexical reference signal for controlled perturbations, not as a global comparison against all dense embedding models.

## Implemented files

- `scripts/run_embedding_baseline.py`
- `reports/embedding_baseline_perturbation.json`
- `reports/embedding_baseline_perturbation.md`
- `tests/test_embedding_baseline_report.py`
- `pyproject.toml`
- `README.md`
- `docs/ROADMAP.md`
- `docs/CLAIMS_AND_METRICS_AUDIT.md`

## Baseline backend

Default backend: `char_ngram_vector_cosine`.

The default backend uses an offline character n-gram vector cosine. It uses sklearn TF-IDF when available and a bounded hashed fallback otherwise. This is reproducible without downloading a dense model. It is not a dense semantic embedding.

Optional dense backend:

```bash
python scripts/run_embedding_baseline.py --backend sentence-transformers
```

Use it only when `sentence-transformers` and the model files are available.

## Results

The current materialized report is `reports/embedding_baseline_perturbation.json`.

| Perturbation | Mean cosine | Mean drop |
|---|---:|---:|
| Node deletion | 0.9855 | 0.0145 |
| Edge deletion | 0.9965 | 0.0035 |
| Argument swap | 0.9961 | 0.0039 |
| Polarity flip | 0.9988 | 0.0012 |
| Relation blur | 0.9951 | 0.0049 |

Interpretation: the vector-space baseline remains very similar under most controlled edits. This supports its use as a topical/lexical reference signal. It does not by itself prove anything about modern dense embeddings.

## Future radar note

A future patch may add MINE-style node/edge and vector/embedding traces to the radar. This should be done only if the caption remains explicit that the radar is a normalized perturbation-sensitivity profile, not an accuracy leaderboard.

## Commands run

```bash
python scripts/run_embedding_baseline.py
```

```bash
python -m pytest -q
```

```bash
cd paper
latexmk -pdf -interaction=nonstopmode main.tex
```

## Verification

```text
219 passed
```

`latexmk` was also run from `paper/`; the existing PDF target was already up to date.
