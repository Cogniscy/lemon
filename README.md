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
- `docs/lemon-03.md` — WebNLG factor inventory plan and commands.
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

## lemon-03: WebNLG factor inventory

Build an inventory of predicates, node labels, categories, contexts, and candidate factors from the stratified WebNLG train split:

```bash
python -m lemon_factor.factors.inventory_cli \
  data/processed/webnlg_train.jsonl \
  --out data/interim/webnlg_factor_inventory.json \
  --summary data/reports/webnlg_factor_inventory_summary.json
```

Export a compact markdown table for the paper:

```bash
python -m lemon_factor.analysis.inventory_stats \
  data/interim/webnlg_factor_inventory.json \
  --out paper/tables/table_webnlg_inventory.md
```

The output is a train-side inventory. Candidate factors extracted from predicate names are not final semantic factors; they are evidence for the next factor-schema stage.

## lemon-04: Seed semantic factor schema

Build deterministic seed semantic factors and predicate decompositions from the WebNLG factor inventory:

```bash
python -m lemon_factor.factors.seed_builder \
  data/interim/webnlg_factor_inventory.json \
  --schema-out data/interim/factor_schema_seed.json \
  --decompositions-out data/interim/webnlg_predicate_decompositions_seed.json \
  --top-k 50
```

Export expert-review CSV:

```bash
python -m lemon_factor.factors.review_export \
  data/interim/webnlg_predicate_decompositions_seed.json \
  --out data/annotation/predicate_decomposition_review.csv
```

Export paper tables:

```bash
python -m lemon_factor.analysis.factor_schema_tables \
  --schema data/interim/factor_schema_seed.json \
  --decompositions data/interim/webnlg_predicate_decompositions_seed.json \
  --schema-out paper/tables/table_factor_schema_seed.md \
  --decompositions-out paper/tables/table_predicate_decompositions_seed.md
```

This stage maps lexical predicate evidence such as `birthPlace → birth, place` into controlled semantic factors such as `biographical_relation + person + place`.

## lemon-05: optional OpenRouter LLM candidate generation

The deterministic pipeline works without an LLM. To generate optional LLM-assisted predicate decomposition candidates, set an OpenRouter key and run:

```powershell
$env:OPENROUTER_API_KEY="..."
python -m lemon_factor.llm.decompose_predicates `
  data/interim/webnlg_factor_inventory.json `
  --factor-schema data/interim/factor_schema_seed.json `
  --models configs/llm_models.yaml `
  --out data/interim/llm_predicate_decomposition_candidates.jsonl `
  --raw-out data/interim/llm_raw_responses.jsonl `
  --limit 50
```

Dry-run mode requires no key and writes prompts/payloads only:

```powershell
python -m lemon_factor.llm.decompose_predicates `
  data/interim/webnlg_factor_inventory.json `
  --factor-schema data/interim/factor_schema_seed.json `
  --models configs/llm_models.yaml `
  --limit 10 `
  --dry-run
```

Evaluate candidates against the seed reference:

```powershell
python -m lemon_factor.llm.evaluate_decompositions `
  data/interim/llm_predicate_decomposition_candidates.jsonl `
  data/interim/webnlg_predicate_decompositions_seed.json `
  --out data/reports/llm_decomposition_eval.json `
  --table paper/tables/table_llm_decomposition_eval.md `
  --review-out data/annotation/llm_decomposition_review.csv
```

LLM outputs are candidate decompositions only. They must pass schema validation and should be reviewed before being treated as evidence.


### LLM debug vs final model configs

For iterative debugging, keep LLM runs small:

```powershell
python -m lemon_factor.llm.decompose_predicates `
  data/interim/webnlg_factor_inventory.json `
  --factor-schema data/interim/factor_schema_seed.json `
  --models configs/llm_models.yaml `
  --limit 10 `
  --dry-run
```

Model configs:

```text
configs/llm_models.yaml        # default debug: one model
configs/llm_models_debug.yaml  # explicit one-model debug config
configs/llm_models_sanity.yaml # two-model sanity comparison
configs/llm_models_full.yaml   # full final comparison
```

