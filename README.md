# LEMON-Factor

Pilot repository for **LEMON-Factor: Factorized Semantic Decomposition for Graph–Text Meaning Preservation Evaluation**.

The project is designed as a SPECOM-oriented research prototype. It does **not** put text-to-KG extraction at the center. Instead, it uses datasets with explicit graphs/relations and evaluates whether graph and text preserve the same meaning.

## Core idea

```text
text + explicit graph
      ↓
unified GraphText format
      ↓
term/relation factor decompositions learned on train
      ↓
LEMON-Factor semantic coverage on dev
      ↓
comparison with exact/embedding/MINE-style recoverability
```

## Main documents

- `docs/ROADMAP.md` — full implementation and paper roadmap.
- `docs/lemon-01.md` — detailed first milestone plan.
- `docs/lemon-02.md` — WebNLG parquet conversion plan.
- `docs/lemon-02.1.md` — stratified WebNLG pilot sampling plan.
- `docs/reference_sources.md` — external datasets and baseline references.
- `docs/annotation_guidelines.md` — expert review templates and labeling policy.

## Current code skeleton

- `src/lemon_factor/schema/graphtext.py` — unified graph/text Pydantic schema.
- `src/lemon_factor/factors/schema.py` — semantic factor decomposition schema.
- `src/lemon_factor/metrics/factor.py` — factor similarity and coverage.
- `src/lemon_factor/mine/retrieve.py` — MINE-compatible retrieval and 2-hop expansion skeleton.
- `src/lemon_factor/datasets/unified_io.py` — JSONL read/write helpers.

## Run tests

```bash
python -m pytest -q
```


## lemon-02: WebNLG parquet conversion

Recent `datasets` versions cannot load `GEM/web_nlg` through the legacy dataset script. Use the parquet conversion instead. The project loader does this internally.

Install research dependencies:

```bash
python -m pip install -e ".[dev,research]"
```

Inspect the WebNLG parquet schema:

```bash
python scripts/inspect_webnlg.py
```

Convert a smoke-test subset to unified GraphText JSONL:

```bash
python -m lemon_factor.datasets.convert_webnlg --language en --n-train 100 --n-dev 50 --out-dir data/processed
```

For experiments, prefer deterministic category-stratified sampling:

```bash
python -m lemon_factor.datasets.convert_webnlg \
  --language en \
  --n-train 200 \
  --n-dev 100 \
  --stratify-category \
  --seed 42 \
  --out-dir data/processed
```

Compute dataset statistics:

```bash
python -m lemon_factor.analysis.dataset_stats data/processed/webnlg_train.jsonl data/processed/webnlg_dev.jsonl --out data/reports/webnlg_stats.json
```

Run tests:

```bash
python -m pytest
```

The stratified WebNLG path is used to avoid evaluating LEMON-Factor on only the first categories returned by the parquet files.
