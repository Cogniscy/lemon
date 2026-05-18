# lemon-01: Repository, Data Contract, and Pilot Planning

## Stage goal

Create a reproducible research repository that can support the later LEMON-Factor experiments and SPECOM paper. The stage should produce a stable project structure, unified data schema, implementation roadmap, first tested metric primitives, and clear documentation for what comes next.

The purpose of lemon-01 is not to download all datasets or run the full experiment. It is to remove ambiguity before implementation starts.

## Definition of done

lemon-01 is complete when:

1. The repository has a stable source/data/docs/paper layout.
2. A Pydantic `GraphTextExample` schema exists and validates graph node/edge references.
3. A Pydantic semantic factor decomposition schema exists.
4. Minimal factor similarity and asymmetric coverage functions exist.
5. A deterministic MINE-compatible retrieval skeleton exists: vector top-k and 2-hop subgraph expansion.
6. Roadmap, first-stage plan, references, and annotation guidelines are documented.
7. Unit tests pass with `python -m pytest -q`.
8. The project can be zipped and handed off as a reproducible artifact.

## Stage tasks

### 1. Initialize project layout

Create:

```text
src/lemon_factor/
  schema/
  datasets/
  factors/
  metrics/
  mine/
  analysis/
docs/
experiments/
annotation/
reports/
paper/
tests/
```

Code output:

- `pyproject.toml`
- `README.md`
- package `src/lemon_factor`

Paper output:

- reproducibility assumptions for the future Methods / Reproducibility subsection.

### 2. Define unified GraphText schema

Write:

```text
src/lemon_factor/schema/graphtext.py
```

The schema must support:

- dataset id and split;
- natural-language text;
- graph nodes;
- graph edges;
- fact objects used by MINE/LEMON;
- metadata for dataset-specific fields.

Validation required:

- every edge subject/object must refer to an existing node;
- every fact edge reference must point to an existing edge.

Tests:

- valid graph passes;
- invalid edge reference fails;
- invalid fact edge reference fails.

Paper contribution:

- the future Data Representation subsection can use this schema as the exact experimental contract.

### 3. Define semantic factor schemas

Write:

```text
src/lemon_factor/factors/schema.py
```

Models:

- `SemanticFactor`
- `FactorComponent`
- `FactorDecomposition`

Fields must include:

- factor id;
- role;
- weight;
- depth;
- source;
- confidence.

Validation required:

- non-empty decompositions;
- weights in `[0, 1]`;
- total positive factor mass.

Paper contribution:

- formal basis for the LEMON-Factor Method section.

### 4. Implement minimal factor metrics

Write:

```text
src/lemon_factor/metrics/factor.py
```

Functions:

- `factor_overlap_weight(left, right, role_aware=False)`
- `factor_sim(left, right, role_aware=False)`
- `asymmetric_cover(source, candidate, role_aware=False)`

Expected behavior:

- equivalent decompositions score high;
- partial overlap scores between 0 and 1;
- role-aware matching penalizes incorrect role alignment;
- asymmetric coverage can differ from symmetric similarity.

Paper contribution:

- early implementation of the metric formulas.

### 5. Implement exact/token baselines

Write:

```text
src/lemon_factor/metrics/exact.py
```

Functions:

- `normalize_surface`
- `exact_match`
- `token_jaccard`

Paper contribution:

- simple baselines for Experiment 1.

### 6. Implement unified JSONL IO

Write:

```text
src/lemon_factor/datasets/unified_io.py
```

Functions:

- `read_jsonl`
- `write_jsonl`

Paper contribution:

- makes dataset statistics reproducible and prevents undocumented ad hoc formats.

### 7. Implement MINE-compatible retrieval skeleton

Write:

```text
src/lemon_factor/mine/retrieve.py
```

Functions:

- `cosine`
- `top_k_nodes`
- `expand_subgraph`

Constraints:

- do not implement the LLM judge yet;
- keep retrieval deterministic and testable;
- implement 2-hop graph expansion because later MINE reproduction depends on it.

Paper contribution:

- future Experiment 3 baseline can reuse this module.

### 8. Write documentation

Write:

- `docs/ROADMAP.md`
- `docs/lemon-01.md`
- `docs/reference_sources.md`
- `docs/annotation_guidelines.md`

Paper contribution:

- roadmap maps directly to paper sections and experimental artifacts.

### 9. Add tests and run them

Tests required:

```text
tests/test_graphtext_schema.py
tests/test_factor_metrics.py
tests/test_unified_io.py
tests/test_mine_retrieve.py
```

Run:

```bash
python -m pytest -q
```

Paper contribution:

- reproducibility confidence before experiments begin.

## Risks and mitigations

### Risk 1: Dataset leakage between train and dev

Problem:

- factor dictionary learned from dev would inflate LEMON-Factor scores.

Mitigation:

- all factor dictionary construction must use train only;
- dev files must be read-only during scoring;
- metadata should record dictionary version and source split.

Code action:

- later converters should preserve split;
- factor dictionary files should include `source_split: train`.

### Risk 2: Factor dictionary becomes subjective

Problem:

- reviewers may see factor decompositions as hand-crafted and arbitrary.

Mitigation:

- keep factor schema small;
- store expert review decisions;
- report agreement/confidence;
- run ablations: exact, embedding, factor, role-factor.

Code action:

- keep `annotation/factor_review_template.csv`;
- write scripts that can rerun metrics with and without expert changes.

### Risk 3: MINE implementation deviates from canonical protocol

Problem:

- MINE comparison becomes invalid if retrieval or expansion is different.

Mitigation:

- implement separate `mine/` module;
- document embedding model, top-k, hop radius, judge prompt;
- keep a human validation sample.

Code action:

- `mine/retrieve.py` already fixes 2-hop expansion behavior;
- later add `mine/judge.py` with prompt snapshot and temperature 0.

### Risk 4: WebNLG and BioRED are too different

Problem:

- a unified metric may look unstable across open-domain RDF and biomedical relations.

Mitigation:

- report per-dataset results separately;
- use dataset-specific factor levels: universal, scientific, biomedical, dataset;
- avoid claiming universal generalization from pilot results.

Code action:

- `SemanticFactor.level` includes `universal`, `scientific`, `biomedical`, `dataset`.

### Risk 5: Embedding baseline outperforms factor similarity

Problem:

- LEMON-Factor may not improve aggregate scores in the pilot.

Mitigation:

- focus also on interpretability and disagreement analysis;
- show error cases where factor decomposition explains partial preservation;
- use role-aware comparisons where embeddings are weakest.

Code action:

- store per-case scores, not only averages;
- build `reports/error_cases.csv` in later stages.

### Risk 6: First stage over-engineers before data ingestion

Problem:

- too much code before seeing real datasets can lead to wrong abstractions.

Mitigation:

- keep schemas minimal;
- use metadata fields for dataset-specific information;
- postpone embeddings and LLM judge until later stages.

## Files created in lemon-01

```text
README.md
pyproject.toml
docs/ROADMAP.md
docs/lemon-01.md
docs/reference_sources.md
docs/annotation_guidelines.md
src/lemon_factor/schema/graphtext.py
src/lemon_factor/factors/schema.py
src/lemon_factor/metrics/factor.py
src/lemon_factor/metrics/exact.py
src/lemon_factor/datasets/unified_io.py
src/lemon_factor/mine/retrieve.py
tests/test_graphtext_schema.py
tests/test_factor_metrics.py
tests/test_unified_io.py
tests/test_mine_retrieve.py
```

## Next stage: lemon-02

lemon-02 should implement actual dataset ingestion:

1. Download/parse WebNLG.
2. Download/parse BioRED.
3. Load or normalize MINE pilot facts.
4. Convert all to unified JSONL.
5. Create fixed pilot train/dev subsets.
6. Generate first dataset statistics table for the paper.
