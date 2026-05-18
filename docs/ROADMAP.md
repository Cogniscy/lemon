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
