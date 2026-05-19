# LEMON-Factor Roadmap

## Scope

This roadmap turns the current LEMON idea into a SPECOM-oriented research prototype. The project does not optimize a text-to-KG extractor. It evaluates **graph–text meaning preservation** when explicit graphs, triples, or relation annotations are available.

The planned contribution is an interpretable metric layer:

```text
text + explicit graph
      ↓
unified GraphText representation
      ↓
train-only factor dictionary and decompositions
      ↓
LEMON-Factor semantic coverage on dev
      ↓
comparison with exact matching, embedding similarity, and MINE-style recoverability
```

## Research claims to test

1. Complex terms and relations can be represented as weighted, role-aware semantic factor decompositions.
2. Factor-based similarity can separate equivalent, near, related, and different graph/text concepts better than exact matching and raw embedding cosine.
3. LEMON-Factor is complementary to MINE: MINE tests whether a fact can be inferred from a retrieved subgraph; LEMON-Factor tests which semantic components and roles are preserved.
4. The method is useful for both clean KG/text benchmarks and biomedical relation datasets.

## Roadmap overview

| Stage | Name | Main output | Paper contribution |
|---|---|---|---|
| lemon-01 | Repository, data contract, pilot planning | Reproducible repo, GraphText schema, roadmap, first tests | Reproducibility and data representation sections |
| lemon-02 | Dataset ingestion | WebNLG/BioRED/MINE loaders and pilot splits | Dataset table and experimental setup |
| lemon-02.1 | Stratified WebNLG pilot | Category-balanced WebNLG train/dev JSONL | Less biased WebNLG pilot and stronger dataset table |
| lemon-03 | Factor schema and inventory | Seed factor schema, train term/predicate inventory | Method: factor inventory |
| lemon-04 | Factor decompositions | Initial factor dictionary and expert review templates | Method examples and annotation protocol |
| lemon-05 | Similarity metrics | exact, token, embedding, factor, role-factor scorers | Metric definitions |
| lemon-06 | Pair benchmark | Expert-labeled equivalent/near/related/different pairs | Experiment 1 |
| lemon-07 | Graph-text coverage | LEMON-Factor graph/text coverage evaluator | Experiment 2 |
| lemon-08 | MINE-compatible baseline | top-k retrieval, 2-hop expansion, judge protocol | Experiment 3 baseline |
| lemon-09 | Results and disagreement analysis | tables, error cases, MINE vs LEMON comparison | Results and error analysis |
| lemon-10 | SPECOM paper writing | LNCS draft, figures, tables, reproducibility notes | Submission-ready paper draft |

## Target datasets

### WebNLG

Used as a clean graph-to-text benchmark with explicit DBpedia triples and text verbalizations. It supports controlled graph/text comparison without making extraction the central task.

### BioRED

Used as the biomedical branch. It provides PubMed abstracts with biomedical entity and document-level relation annotations. It tests whether the factor approach is viable beyond open-domain RDF triples.

### MINE / KGGen evaluation data

Used to reproduce a MINE-compatible fact recoverability baseline: fact embedding, node retrieval, 2-hop expansion, and binary inferability judgment.

## Unified GraphText representation

Every dataset is converted into the same JSONL object shape:

```json
{
  "id": "...",
  "dataset": "webnlg|biored|mine",
  "split": "train|dev|test|pilot",
  "language": "en|ru|...",
  "text": "...",
  "nodes": [
    {"id": "n1", "label": "...", "type": "..."}
  ],
  "edges": [
    {"subj": "n1", "pred": "...", "obj": "n2", "evidence": "..."}
  ],
  "facts": [
    {"id": "f1", "text": "...", "source": "gold|manual|derived|mine"}
  ]
}
```

## Evaluation blocks

### Experiment 1: term/relation similarity

Compare exact, token, embedding, factor, and role-aware factor similarity on expert-labeled pairs:

- equivalent
- near
- related
- different

### Experiment 2: graph-text meaning coverage

Use gold graphs and texts. Measure how much source-side semantics are covered by candidate graph-side semantics.

### Experiment 3: MINE-style recoverability

Run a MINE-compatible pipeline:

1. Embed facts.
2. Embed graph nodes.
3. Retrieve top-k nodes.
4. Expand retrieved nodes to a 2-hop subgraph.
5. Judge whether the fact is inferable from the subgraph.
6. Score recovered facts divided by all facts.

## Expected paper tables

1. Dataset statistics.
2. Pair similarity results.
3. Graph-text coverage results.
4. MINE vs LEMON-Factor disagreement matrix.
5. Error analysis categories.

## Expert review points

1. Factor decompositions: missing/extra factors, wrong roles, poor weights.
2. Pair labels: equivalent / near / related / different.
3. MINE judge validation: whether a fact is inferable from the retrieved subgraph.
4. Error categories: retrieval failure, judge failure, missing factor, too generic factor, wrong role, numeric/unit mismatch.

## Minimal publishable result

The first publishable claim should stay modest:

> Pilot results suggest that role-aware factorized semantic decomposition is an interpretable complement to MINE-style fact recoverability for graph–text meaning preservation evaluation.

Avoid claiming that LEMON-Factor is a general theory of meaning or a replacement for MINE.


## Milestone lemon-02 — WebNLG parquet ingestion

**Goal:** establish the first real dataset pipeline by converting WebNLG parquet rows into the unified GraphText JSONL format.

**Code deliverables:**
- `datasets/webnlg_loader.py` for parquet loading through `refs/convert/parquet`;
- `datasets/convert_webnlg.py` for record conversion;
- `datasets/normalization.py` for stable IDs, label cleaning, and triple parsing;
- `analysis/dataset_stats.py` for dataset statistics;
- offline tests for the converter.

**Paper deliverables:**
- first dataset statistics table row;
- reproducibility note for Hugging Face parquet loading;
- conversion protocol paragraph for the Data section.

**Exit criteria:** WebNLG pilot train/dev JSONL files are produced, validated by Pydantic, summarized by the stats module, and covered by tests.


## Milestone lemon-02.1 — Stratified WebNLG pilot sampling

**Goal:** replace first-row-only WebNLG pilot sampling with deterministic category-stratified sampling for experiments.

**Code deliverables:**
- `datasets/sampling.py` with `take_first` and `stratified_sample`;
- `convert_webnlg.py` CLI flags `--stratify-category`, `--seed`, and `--min-per-category`;
- expanded dataset statistics with category ratios and edge-count distribution;
- offline tests for sampler, converter selection, and stats.

**Paper deliverables:**
- stronger WebNLG pilot description;
- reproducible sampling protocol;
- less biased Dataset Statistics table.

**Exit criteria:** tests pass and `--stratify-category` creates train/dev files with multiple categories when the source split contains them.

## Milestone lemon-03 — WebNLG factor inventory

**Goal:** extract train-side predicate, node-label, category, and candidate-factor inventory from the stratified WebNLG pilot.

**Code deliverables:**
- `factors/candidates.py` for predicate-name candidate factors;
- `factors/inventory.py` for aggregate train-side inventory;
- `factors/inventory_cli.py` for CLI execution;
- `analysis/inventory_stats.py` for paper-table export.

**Paper deliverables:**
- first predicate inventory table;
- evidence that factorization starts from explicit graph predicates rather than raw text alone.

**Exit criteria:** tests pass and WebNLG train inventory plus compact markdown table are generated.

## Milestone lemon-04 — Seed semantic factor schema and decompositions

**Goal:** map shallow candidate factors into a controlled semantic factor schema and build the first role-aware predicate decompositions.

**Code deliverables:**
- `factors/decomposition.py` for Pydantic schemas and validation;
- `factors/seed_schema.py` for default seed factors;
- `factors/seed_builder.py` for deterministic predicate decomposition rules;
- `factors/review_export.py` for expert-review CSV;
- `analysis/factor_schema_tables.py` for paper tables.

**Paper deliverables:**
- semantic factor schema table;
- predicate-decomposition examples;
- expert-review protocol for correcting factors and weights.

**Exit criteria:** tests pass, seed schema/decomposition JSON files validate, review CSV and paper tables are generated.

## lemon-05 — Optional LLM candidate generator

Goal: add a model-agnostic OpenRouter-backed candidate generator for predicate decompositions. The deterministic `lemon-04` seed schema remains the reference. LLM output is evaluated by parse success, schema validity, factor F1, role accuracy, weight MAE, and expert acceptance.

Code artifacts:

```text
src/lemon_factor/llm/openrouter_client.py
src/lemon_factor/llm/schema.py
src/lemon_factor/llm/prompting.py
src/lemon_factor/llm/decompose_predicates.py
src/lemon_factor/llm/evaluate_decompositions.py
configs/llm_models.yaml
```

Paper contribution: demonstrate that factor decompositions can be proposed by any LLM under a fixed schema/prompt protocol, while quality remains measurable and model-independent.


## LLM debug model policy

For work before final result collection, use the one-model debug config in `configs/llm_models.yaml`. Full multi-model runs should use `configs/llm_models_full.yaml` and be reserved for final tables.

## lemon-06 — Synthetic LLM adjudication reference

Create a temporary adjudicated predicate-decomposition reference by combining seed decompositions, LLM candidates, inventory evidence, and a stronger LLM adjudicator. The output is explicitly marked as synthetic and is used only until human expert validation is available.

Artifacts:

- `src/lemon_factor/llm/adjudicate_decompositions.py`
- `src/lemon_factor/llm/adjudication_schema.py`
- `src/lemon_factor/factors/disagreement.py`
- `data/interim/webnlg_predicate_decompositions_synthetic_adjudicated.json`
- `data/annotation/synthetic_adjudication_review.csv`
- `paper/tables/table_synthetic_adjudication_stats.md`


## lemon-06.1 — Model preflight for synthetic adjudication

Adds OpenRouter model catalog checks and separate debug/full adjudicator configs. This prevents empty synthetic references caused by stale or unavailable model IDs before moving to LEMON-Factor coverage.


## lemon-06.2 — Synthetic adjudication quality fixes

Status: implemented. This patch prevents missing confidence from being displayed as false `0.00`, adds LLM candidate coverage diagnostics, and warns when synthetic adjudication includes predicates without LLM candidates. It makes the synthetic reference safer to use in `lemon-07`, while keeping it explicitly marked as non-human.

## lemon-07 — LEMON-Factor graph-text coverage

Status: implemented.

Purpose: compute the first deterministic graph-text semantic coverage score on
WebNLG dev using explicit graph edges and predicate decompositions. The stage
exports corpus-level scores, edge-level diagnostics, and a paper-ready markdown
table.


## lemon-08 — Decomposition coverage expansion and error analysis

Use the first WebNLG coverage results to find missing predicates, expand predicate decompositions and lexical cues, rerun coverage, and export before/after and error-analysis tables for the paper. This stage demonstrates the diagnostic loop of LEMON-Factor: coverage → missing predicates → dictionary expansion → improved coverage → categorized residual errors.

## Milestone lemon-09 — Paper skeleton and baseline comparison

**Goal:** connect the implemented metric pipeline to the SPECOM paper draft and add explicit baseline comparison tables.

**Code deliverables:**
- `baselines/text_similarity.py` for lightweight lexical graph-text baselines;
- `analysis/baseline_comparison.py` for comparing exact labels, predicate cues, token similarity, and LEMON-Factor reports;
- offline tests for the baseline module and CLI.

**Paper deliverables:**
- populated `paper/main.tex` and section drafts;
- `paper/references.bib` with initial citations;
- `paper/tables/table_webnlg_baseline_comparison.md`;
- integration notes for the research brief.

**Exit criteria:** tests pass, baseline comparison JSON/table are generated, and the paper skeleton clearly distinguishes lexical baselines, LEMON-Factor, and synthetic LLM adjudication limitations.
