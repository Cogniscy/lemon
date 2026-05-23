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


## lemon-06: synthetic LLM adjudication

Generate adjudication prompts without API calls:

```powershell
python -m lemon_factor.llm.adjudicate_decompositions `
  --seed data/interim/webnlg_predicate_decompositions_seed.json `
  --llm data/interim/llm_predicate_decomposition_candidates.jsonl `
  --inventory data/interim/webnlg_factor_inventory.json `
  --models configs/llm_adjudicator.yaml `
  --limit 20 `
  --dry-run
```

Live run with OpenRouter:

```powershell
$env:OPENROUTER_API_KEY="..."
python -m lemon_factor.llm.adjudicate_decompositions `
  --seed data/interim/webnlg_predicate_decompositions_seed.json `
  --llm data/interim/llm_predicate_decomposition_candidates.jsonl `
  --inventory data/interim/webnlg_factor_inventory.json `
  --models configs/llm_adjudicator.yaml `
  --out data/interim/webnlg_predicate_decompositions_synthetic_adjudicated.json `
  --raw-out data/interim/llm_synthetic_adjudication_raw.jsonl `
  --review-out data/annotation/synthetic_adjudication_review.csv `
  --stats-out data/reports/synthetic_adjudication_stats.json `
  --table paper/tables/table_synthetic_adjudication_stats.md `
  --limit 30
```

The result is a synthetic temporary reference, not a human expert gold label.

### lemon-06.1: check adjudicator model availability

Before live synthetic adjudication, run a model preflight check:

```powershell
python -m lemon_factor.llm.model_check `
  --models configs/llm_adjudicator_debug.yaml `
  --out data/reports/openrouter_adjudicator_debug_check.json
```

Use `configs/llm_adjudicator.yaml` for one-model debugging and `configs/llm_adjudicator_full.yaml` only for final runs.

## lemon-07: LEMON-Factor graph-text coverage

Run the deterministic WebNLG coverage baseline:

```powershell
python -m lemon_factor.coverage.run_webnlg_coverage `
  data/processed/webnlg_dev.jsonl `
  --decompositions data/interim/webnlg_predicate_decompositions_synthetic_adjudicated.json `
  --lexical-cues data/interim/webnlg_lexical_cues_seed.json `
  --out data/reports/webnlg_lemon_factor_coverage.json `
  --details data/reports/webnlg_lemon_factor_coverage_details.jsonl `
  --table paper/tables/table_webnlg_lemon_factor_coverage.md
```

The report includes exact label coverage, predicate cue coverage,
LEMON-Factor weighted coverage, and missing decomposition rate. The details JSONL
contains edge-level factor diagnostics.


## lemon-08: error-driven coverage expansion

After the first WebNLG coverage run, analyze missing decompositions, expand predicate decompositions and lexical cues, rerun coverage, and produce before/after tables.

```powershell
python -m lemon_factor.coverage.missing_analysis `
  data/reports/webnlg_lemon_factor_coverage_details.jsonl `
  --examples data/processed/webnlg_dev.jsonl `
  --out data/reports/webnlg_missing_predicates.json `
  --table paper/tables/table_webnlg_missing_predicates.md

python -m lemon_factor.factors.expand_decompositions `
  --missing data/reports/webnlg_missing_predicates.json `
  --base data/interim/webnlg_predicate_decompositions_synthetic_adjudicated.json `
  --inventory data/interim/webnlg_factor_inventory.json `
  --out data/interim/webnlg_predicate_decompositions_expanded.json

python -m lemon_factor.coverage.expand_lexical_cues `
  --missing data/reports/webnlg_missing_predicates.json `
  --base-cues data/interim/webnlg_lexical_cues_seed.json `
  --out data/interim/webnlg_lexical_cues_expanded.json

python -m lemon_factor.coverage.run_coverage_delta `
  data/processed/webnlg_dev.jsonl `
  --before data/reports/webnlg_lemon_factor_coverage.json `
  --expanded-decompositions data/interim/webnlg_predicate_decompositions_expanded.json `
  --expanded-lexical-cues data/interim/webnlg_lexical_cues_expanded.json `
  --out data/reports/webnlg_lemon_factor_coverage_expanded.json `
  --details data/reports/webnlg_lemon_factor_coverage_expanded_details.jsonl `
  --table paper/tables/table_webnlg_coverage_delta.md

python -m lemon_factor.coverage.error_analysis `
  data/reports/webnlg_lemon_factor_coverage_expanded_details.jsonl `
  --out data/reports/webnlg_coverage_error_analysis.json `
  --table paper/tables/table_webnlg_coverage_error_types.md
```

## lemon-09: paper skeleton and baseline comparison

Build a lightweight comparison table that places LEMON-Factor next to surface lexical controls:

```powershell
python -m lemon_factor.analysis.baseline_comparison `
  data/processed/webnlg_dev.jsonl `
  --baseline-report data/reports/webnlg_lemon_factor_coverage.json `
  --expanded-report data/reports/webnlg_lemon_factor_coverage_expanded.json `
  --out data/reports/webnlg_baseline_comparison.json `
  --table paper/tables/table_webnlg_baseline_comparison.md
```

The table compares exact entity-label coverage, predicate cue coverage, graph-text token Jaccard/cosine, initial LEMON-Factor, and expanded LEMON-Factor. Token baselines are lexical controls, not semantic metrics.

Paper draft files are under:

```text
paper/main.tex
paper/sections/*.tex
paper/references.bib
```

The draft is LNCS-oriented but not yet submission-ready. It is a structured writing scaffold for SPECOM.


### Build the first paper draft

```powershell
cd paper
latexmk -pdf -interaction=nonstopmode main.tex
```

The lemon-10 draft uses the requested author list: Tomilov A.A., Gineva D. (ITMO), and Tirskih D. (ITMO). Tomilov affiliation is currently a placeholder and should be confirmed before submission.

## lemon-11: Bidirectional LEMON and MINE-style node/edge baseline

Reconstruct a deterministic text-to-KG graph from WebNLG text:

```bash
python -m lemon_factor.reverse.reconstruct_graph \
  data/processed/webnlg_dev.jsonl \
  --lexical-cues data/interim/webnlg_lexical_cues_expanded.json \
  --mode lexical \
  --out data/interim/webnlg_reconstructed_graphs_lexical.jsonl \
  --report data/reports/webnlg_reconstruction_lexical.json
```

Run reverse LEMON-Factor:

```bash
python -m lemon_factor.reverse.run_reverse_lemon \
  data/processed/webnlg_dev.jsonl \
  --reconstructed data/interim/webnlg_reconstructed_graphs_lexical.jsonl \
  --decompositions data/interim/webnlg_predicate_decompositions_expanded.json \
  --out data/reports/webnlg_reverse_lemon.json \
  --details data/reports/webnlg_reverse_lemon_details.jsonl \
  --table paper/tables/table_webnlg_reverse_lemon.md
```

Run the deterministic MINE-style node/edge baseline:

```bash
python -m lemon_factor.mine_nodes_edges.run_mine_style \
  data/processed/webnlg_dev.jsonl \
  --reconstructed data/interim/webnlg_reconstructed_graphs_lexical.jsonl \
  --out data/reports/webnlg_mine_style.json \
  --scores data/reports/webnlg_mine_style_scores.jsonl \
  --table paper/tables/table_webnlg_mine_style.md \
  --top-k 2 \
  --hops 2
```

Build the bidirectional comparison:

```bash
python -m lemon_factor.analysis.bidirectional_comparison \
  --forward data/reports/webnlg_lemon_factor_coverage_expanded.json \
  --reverse data/reports/webnlg_reverse_lemon.json \
  --mine-style data/reports/webnlg_mine_style.json \
  --baseline data/reports/webnlg_baseline_comparison.json \
  --out data/reports/webnlg_bidirectional_comparison.json \
  --table paper/tables/table_webnlg_bidirectional_comparison.md
```

This stage treats MINE as **Measure of Information in Nodes and Edges** and implements a WebNLG-specific deterministic adaptation. It is not a full KGGen reproduction and does not yet include an LLM judge.

## lemon-12: LLM-judged MINE-style recoverability

`lemon-12` keeps the deterministic MINE-style node/edge score from `lemon-11` and adds an optional LLM judge over retrieved subgraphs.

Dry-run prompts without an API call:

```bash
python -m lemon_factor.mine_nodes_edges.run_mine_style \
  data/processed/webnlg_dev.jsonl \
  --reconstructed data/interim/webnlg_reconstructed_graphs_lexical.jsonl \
  --judge llm \
  --models configs/llm_adjudicator_debug.yaml \
  --prompts-out data/interim/mine_style_judge_prompts.jsonl \
  --dry-run \
  --limit 10 \
  --out data/reports/webnlg_mine_style_llm.json \
  --scores data/reports/webnlg_mine_style_llm_scores.jsonl \
  --table paper/tables/table_webnlg_mine_style_llm.md
```

Live LLM-judged run:

```bash
python -m lemon_factor.mine_nodes_edges.run_mine_style \
  data/processed/webnlg_dev.jsonl \
  --reconstructed data/interim/webnlg_reconstructed_graphs_lexical.jsonl \
  --judge llm \
  --models configs/llm_adjudicator_debug.yaml \
  --out data/reports/webnlg_mine_style_llm.json \
  --scores data/reports/webnlg_mine_style_llm_scores.jsonl \
  --raw-out data/reports/webnlg_mine_style_llm_raw.jsonl \
  --table paper/tables/table_webnlg_mine_style_llm.md \
  --top-k 2 \
  --hops 2 \
  --limit 50
```

Updated comparison with the LLM-judged MINE-style row:

```bash
python -m lemon_factor.analysis.bidirectional_comparison \
  --forward data/reports/webnlg_lemon_factor_coverage_expanded.json \
  --reverse data/reports/webnlg_reverse_lemon.json \
  --mine-style data/reports/webnlg_mine_style.json \
  --mine-style-llm data/reports/webnlg_mine_style_llm.json \
  --baseline data/reports/webnlg_baseline_comparison.json \
  --out data/reports/webnlg_bidirectional_comparison_llm.json \
  --table paper/tables/table_webnlg_bidirectional_comparison_llm.md
```

This is still a WebNLG adaptation of KGGen's MINE idea, not a full benchmark reproduction.


## lemon-12.1: Stable LLM-judged MINE-style run

`lemon-12.1` stabilizes the LLM-judged MINE-style run by using compact prompts, bounded JSON schema fields, retry-on-invalid-JSON, and fixed-subset comparison.

Lock a deterministic subset:

```bash
python -m lemon_factor.mine_nodes_edges.run_mine_style   data/processed/webnlg_dev.jsonl   --reconstructed data/interim/webnlg_reconstructed_graphs_lexical.jsonl   --judge deterministic   --out data/reports/webnlg_mine_style_subset_det.json   --scores data/reports/webnlg_mine_style_subset_det_scores.jsonl   --table paper/tables/table_webnlg_mine_style_subset_det.md   --subset-out data/interim/mine_style_eval_subset.json   --limit 50   --top-k 2   --hops 2
```

Run the LLM judge on the same subset:

```bash
python -m lemon_factor.mine_nodes_edges.run_mine_style   data/processed/webnlg_dev.jsonl   --reconstructed data/interim/webnlg_reconstructed_graphs_lexical.jsonl   --judge llm   --models configs/llm_adjudicator_debug.yaml   --subset-in data/interim/mine_style_eval_subset.json   --out data/reports/webnlg_mine_style_llm_stable.json   --scores data/reports/webnlg_mine_style_llm_stable_scores.jsonl   --raw-out data/reports/webnlg_mine_style_llm_stable_raw.jsonl   --table paper/tables/table_webnlg_mine_style_llm_stable.md   --compact-context   --max-context-nodes 6   --max-context-edges 6   --reason-max-words 20   --max-tokens 250   --retry-invalid-json   --top-k 2   --hops 2
```

The stable report includes requested, valid, and failed judgments; parse success rate; retry attempts and successes; judge agreement with deterministic scoring; and deterministic score on the same subset.

## lemon-12.2: MINE-style score semantics cleanup

`lemon-12.2` separates deterministic composite node/edge scoring from LLM-judged binary fact recoverability. The stable report now includes explicit fields such as `composite_node_edge_score`, `deterministic_fact_recoverability`, `llm_fact_recoverability`, and deterministic subset diagnostics.

Generate the updated bidirectional comparison and fixed-subset MINE table:

```bash
python -m lemon_factor.analysis.bidirectional_comparison   --forward data/reports/webnlg_lemon_factor_coverage_expanded.json   --reverse data/reports/webnlg_reverse_lemon.json   --mine-style data/reports/webnlg_mine_style.json   --mine-style-llm data/reports/webnlg_mine_style_llm_stable.json   --baseline data/reports/webnlg_baseline_comparison.json   --out data/reports/webnlg_bidirectional_comparison_llm_stable.json   --table paper/tables/table_webnlg_bidirectional_comparison_llm_stable.md   --mine-subset-table paper/tables/table_webnlg_mine_style_subset_comparison.md
```

This prevents comparing the deterministic partial-credit node/edge composite score directly with the stricter LLM binary fact-recoverability score.



## lemon-13 calibration

Controlled perturbation calibration checks whether metrics fall under meaning-destroying noise and remain stable under meaning-preserving noise. All injected noise artifacts and manifests are saved under `data/perturbed/lemon13/`.

```powershell
python -m lemon_factor.calibration.run_calibration `
  data/processed/webnlg_dev.jsonl `
  --reconstructed data/interim/webnlg_reconstructed_graphs_lexical.jsonl `
  --decompositions data/interim/webnlg_predicate_decompositions_expanded.json `
  --lexical-cues data/interim/webnlg_lexical_cues_expanded.json `
  --noise-types delete_relation_phrase swap_object swap_predicate entity_alias predicate_paraphrase drop_edge drop_node graph_swap_predicate `
  --noise-levels 0.0 0.1 0.25 0.5 `
  --perturbation-dir data/perturbed/lemon13 `
  --out data/reports/webnlg_calibration_scores.json `
  --details data/reports/webnlg_calibration_details.jsonl `
  --table paper/tables/table_webnlg_calibration_summary.md `
  --by-noise-table paper/tables/table_webnlg_calibration_by_noise.md `
  --text-side-table paper/tables/table_webnlg_calibration_text_side.md `
  --graph-side-table paper/tables/table_webnlg_calibration_graph_side.md `
  --relation-deletion-table paper/tables/table_webnlg_relation_deletion_sanity.md
```

### Paper draft after lemon-14

The current paper draft is framed as a bidirectional factor-level semantic alignment framework. It integrates Forward LEMON, Reverse LEMON, MINE-style node/edge comparison, and controlled perturbation calibration. Build from `paper/main.tex`.


## lemon-15.1 Biomedical dataset converters

Biomedical cross-domain validation starts with converter-only support for BC5CDR, ChemProt, and BioRED. Raw data should be placed under `data/biomedical/raw/` and should not be committed. BC5CDR additionally supports `--source hf-parquet`; the older `--source bigbio` remains as a legacy alias but no longer relies on `trust_remote_code`.

```powershell
python -m lemon_factor.datasets.convert_bc5cdr `
  --source hf-parquet `
  --out-dir data/biomedical/processed `
  --manifest data/biomedical/manifests/bc5cdr_manifest.json `
  --limit 200

python -m lemon_factor.datasets.convert_bc5cdr `
  --source local `
  --raw-dir data/biomedical/raw/bc5cdr `
  --out-dir data/biomedical/processed `
  --manifest data/biomedical/manifests/bc5cdr_manifest.json

python -m lemon_factor.datasets.convert_chemprot `
  --raw-dir data/biomedical/raw/chemprot `
  --out-dir data/biomedical/processed `
  --manifest data/biomedical/manifests/chemprot_manifest.json `
  --keep-relations CPR:3 CPR:4 CPR:5 CPR:6 CPR:9

python -m lemon_factor.datasets.convert_biored `
  --raw-dir data/biomedical/raw/biored `
  --out-dir data/biomedical/processed `
  --manifest data/biomedical/manifests/biored_manifest.json
```

After conversion, build dataset statistics:

```powershell
python -m lemon_factor.analysis.biomedical_dataset_stats `
  data/biomedical/processed/bc5cdr_train.jsonl `
  --out data/biomedical/reports/biomedical_dataset_stats.json `
  --table paper/tables/table_biomedical_dataset_stats.md
```

## lemon-15.1.2 Biomedical acquisition layer

`lemon-15.1.2` adds a safer raw-data acquisition layer for biomedical validation. BC5CDR and BioRED can now be downloaded from public GitHub repositories; DrugProt is available as an open Zenodo-backed alternative to ChemProt; ChemProt remains local/manual because common loaders expect a local `ChemProt_Corpus.zip`.

Check source status:

```powershell
python -m lemon_factor.datasets.biomedical_sources_check `
  --out data/biomedical/reports/biomedical_sources_check.json `
  --table paper/tables/table_biomedical_sources_check.md
```

BC5CDR direct conversion:

```powershell
python -m lemon_factor.datasets.convert_bc5cdr `
  --source direct `
  --download-dir data/biomedical/raw/bc5cdr `
  --out-dir data/biomedical/processed `
  --manifest data/biomedical/manifests/bc5cdr_manifest.json `
  --limit 200
```

BioRED direct conversion:

```powershell
python -m lemon_factor.datasets.convert_biored `
  --source direct `
  --download-dir data/biomedical/raw/biored `
  --out-dir data/biomedical/processed `
  --manifest data/biomedical/manifests/biored_manifest.json `
  --limit 200
```

DrugProt direct conversion:

```powershell
python -m lemon_factor.datasets.convert_drugprot `
  --source direct `
  --download-dir data/biomedical/raw/drugprot `
  --out-dir data/biomedical/processed `
  --manifest data/biomedical/manifests/drugprot_manifest.json `
  --limit 200
```

ChemProt remains supported in local mode only:

```powershell
python -m lemon_factor.datasets.convert_chemprot `
  --raw-dir data/biomedical/raw/chemprot `
  --out-dir data/biomedical/processed `
  --manifest data/biomedical/manifests/chemprot_manifest.json `
  --keep-relations CPR:3 CPR:4 CPR:5 CPR:6 CPR:9
```
