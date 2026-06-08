# Claims and Metrics Audit

This file lists the claims that are safe for the SPECOM paper and the caveats that should be kept visible while writing. The goal is to avoid overstating the contribution.

## Safe positioning

LEMON is a **source-driven, factor-level diagnostic metric for graph-text semantic fidelity**. It assumes that an explicit source graph, relation annotation, or predicate inventory is available. It is best framed as a restricted instance of layered semantic comparison, not as a general text-text semantic similarity system.

## Claim audit table

| Claim | Status | Evidence / files | Safe wording | Risk if overstated |
|---|---|---|---|---|
| LEMON opens predicate labels into semantic factors. | Supported by method and inventories. | `resources/factors/*`, `reports/factor_inventory_*.json`, `paper/sections/03_method.tex` | "Predicate labels are represented as weighted factor bundles." | Do not claim the factors are universal semantic primitives. |
| Forward and reverse scoring use the same factor schema. | Supported on WebNLG. | `reports/scoring_webnlg.json`, `paper/tables/table_webnlg_final.tex`, `paper/tables/table_webnlg_reverse_lemon.md` | "The same factor representation supports KG->Text coverage and controlled Text->KG recoverability diagnostics." | Do not call the reverse pipeline a full text-to-KG extractor. |
| Forward and Reverse LEMON are close on WebNLG. | Supported. | Forward `0.7915`; Reverse `0.7789`; see paper results. | "The small gap suggests coherence of the factor schema in both directions." | Do not interpret this as state-of-the-art graph reconstruction. |
| Relation deletion exposes the weakness of entity-only coverage. | Strongly supported. | `paper/tables/table_webnlg_relation_deletion_sanity.md`, `paper/sections/06_results.tex` | "Entity-label coverage changes by only -0.0020 while Forward LEMON drops by -0.2106." | Keep the perturbation setting explicit; this is a controlled sanity check. |
| LEMON detects polarity. | Conditionally supported. | Biomedical inventories and perturbation reports. | "LEMON reacts to polarity perturbations when polarity is encoded in the factor inventory." | Do not say it generally detects polarity in all datasets; WebNLG polarity is not encoded. |
| LEMON transfers across domains. | Partially supported. | WebNLG, DrugProt, BC5CDR reports. | "The same inventory format is applied to open-domain and biomedical graph-text data." | Do not claim universal cross-domain validity. |
| MINE-style baseline is included. | Supported as an adapted baseline. | `reports/mine1_like_lemon_pilot.json`, `reports/mine_external_inspection.*` | "MINE-style" or "MINE-inspired node/edge baseline." | Do not claim a reproduction of the KGGen/MINE benchmark. |
| LLM judges validate the metric. | Not supported. | `reports/llm_reliability_summary_3judges.json`, `reports/paper_llm_reliability_compact.json` | "LLM judges provide a complementary recoverability signal." | Do not present LLM judgments as expert validation or gold labels. |
| Diagnostic profile figure shows the niche of the method. | Usable with caveat. | `reports/radar_diagnostic_profile_values.json`, `paper/figures/figure_radar_diagnostic_profile.*` | "Normalized perturbation-sensitivity profile, not absolute accuracy." | Do not present the figure as a leaderboard; Vector cosine is an offline char-ngram baseline unless a dense backend is explicitly run. |
| Expert validation is done. | Not currently supported. | N/A | "Expert validation is planned / required in future work." | Do not imply human-validated inventories until the review is complete. |
| Vector-space baseline is included. | Supported for the offline char-ngram backend. | `reports/embedding_baseline_perturbation.json`, `scripts/run_embedding_baseline.py` | "The offline vector-space baseline is a topical/lexical reference under controlled perturbations." | Do not treat it as a complete dense embedding benchmark or claim global superiority over embeddings. |
| Pragmatic layer is handled. | Not supported. | N/A | "Pragmatics is outside the current scope." | Do not claim coverage of irony, implicature, presupposition, or stance. |

## Metric interpretation notes

### LEMON score

LEMON is a partial-credit semantic coverage score over predicate factors. It is most informative as an audit trail and profile, not only as a scalar.

### Perturbation drops

The perturbation reports use mean drop under controlled synthetic damage. Larger drop means higher sensitivity to the perturbation. These are construct-validity checks, not natural paraphrase robustness tests.

### MINE-style values

The MINE-style values in this repository adapt the node/edge information idea to graph-text pairs. They should be reported as local diagnostic baselines.

### LLM reliability probe

The LLM probe compares deterministic perturbation labels with model-based factor recoverability. Moderate agreement is expected because the two signals answer different questions:

- deterministic labels record intended damage;
- model judges estimate residual semantic recoverability from context.

### Radar values

The current diagnostic-profile JSON explicitly notes that values are normalized perturbation drops. The figure should be used to illustrate a niche, not to claim a global ranking of metrics.

### Layer/profile values

`reports/layer_profile_values.json` remains supporting context for the current diagnostic-profile figure. Its values are diagnostic properties and perturbation drops, not absolute accuracy scores. The safe wording is:

> The diagnostic-profile figure visualizes the niche of LEMON under controlled perturbations.

Avoid:

> The diagnostic-profile figure proves that LEMON is globally more accurate than baseline systems.

The strongest layer claim currently supported is that role factors drive the largest ablation gain. Polarity should be reported only as inventory-dependent.

## Recommended paper wording

Use:

> LEMON is a factor-level diagnostic layer for graph-text semantic fidelity.

Avoid:

> LEMON is a general semantic similarity metric.

Use:

> The same inventory format is applied to WebNLG, DrugProt, and BC5CDR.

Avoid:

> The method proves universal cross-domain semantic transfer.

Use:

> LLM judges provide a complementary signal of recoverability.

Avoid:

> LLM judges validate the gold semantics of the metric.

Use:

> The reverse experiment is a controlled pseudo-extraction diagnostic.

Avoid:

> The reverse experiment evaluates a full text-to-KG extractor.

### Radar diagnostic profile figure

`reports/radar_diagnostic_profile_values.json` and `paper/figures/figure_radar_diagnostic_profile.*` instantiate the diagnostic-profile figure used in the Results section. The values are mean drops under controlled perturbations, taken from `reports/paper_metric_sensitivity_drops.json` and documented against `reports/layer_profile_values.json`.

Safe wording:

> The diagnostic-profile figure visualizes sensitivity to controlled semantic perturbations. Larger values mean stronger scalar response to induced damage, not higher task accuracy.

Avoid:

> The diagnostic-profile figure proves that LEMON is globally more accurate than entity, triple, or embedding metrics.

The figure can compare LEMON, MINE-style node/edge, triple matching, entity recall, and Vector cosine because all plotted values use the same perturbation-drop scale. It still should not be treated as a general leaderboard: triple matching and MINE-style scoring are coarse detectors, Vector cosine is an offline character n-gram baseline unless a dense backend is explicitly materialized, while LEMON is intended to provide an auditable factor-level explanation of the response.

### Vector-space perturbation baseline

`reports/embedding_baseline_perturbation.json` stores an offline vector-space perturbation check. The default backend is a character n-gram vector cosine, not a dense sentence embedding. Dense sentence-transformer cosine can be run explicitly with `scripts/run_embedding_baseline.py --backend sentence-transformers` when the optional model dependency and model files are available.

Safe wording:

> The vector-space baseline remains highly similar under many controlled perturbations, which makes it a useful topical/lexical reference signal rather than a factor-level diagnostic.

Avoid:

> LEMON universally outperforms embedding models.

Current diagnostic-profile extension:

> MINE-style node/edge and Vector cosine traces are included only because all plotted values use the same perturbation-drop scale. The caption must continue to state that the figure is a diagnostic profile, not an accuracy leaderboard. Dense embedding traces should be added only after an explicit dense backend run.

### Expert validation pack

`annotation/expert_validation_sample.csv` is a compact 50-row sample for reviewing predicate-factor decompositions across WebNLG, DrugProt, and BC5CDR. A reviewer-facing Excel form is collected in `annotation/linguist_review_pack/expert_validation_form.xlsx` together with short instructions. It is intended as a feasible 2--3 day review package.

Safe wording:

> We prepared a compact expert-validation protocol for predicate-factor inventories and, if completed, report aggregate accept/missing/wrong-factor and direction/polarity issue rates.

Avoid:

> The full factor inventory is expert-validated.

The sample strengthens readiness for human validation but does not by itself provide validation results.



### LEM-24 paper style and submission-readiness audit

The paper text was revised to keep the narrative centered on a single failure mode: entity names can survive while predicate meaning is lost. The safe scope remains unchanged: LEMON is a graph-text diagnostic layer for relation-level fidelity, not a general text-text similarity metric.

Safe additions:

> Future work should validate predicate inventories with domain experts and connect the factor trace to stronger paraphrase, dense embedding, entailment, QA, and text-to-KG evidence models.

Avoid:

> The current paper already reports expert validation or dense embedding results.

The bibliography now includes recent LLM graph-to-text work as future-facing context, without changing the empirical claims.

## LEM-28 factor-inventory and scalar-sensitivity clarification

The current paper now treats predicate factors and weights as auditable diagnostic resources rather than expert-certified semantic constants. Safe wording:

> The inventories are manually specified diagnostic resources built from predicate labels, argument roles, domain constraints, entity types, and lexical evidence cues. Weights are normalized salience priors and remain subject to expert validation.

Unsafe wording:

> The weights are linguistically validated gold parameters.

The worked-example figure in `paper/figures/figure_factor_scoring_examples.*` is illustrative. It uses current inventory weights to show how a coarse mismatch can be decomposed into different semantic causes. It should not be used as a separate benchmark result.

The ablation table should be interpreted as internal component analysis. It does not rank LEMON against MINE-style or triple matching; it shows which factor groups contribute to LEMON's own diagnostic sensitivity.

## LEM-34 final compaction audit

- The main paper no longer uses the heatmap/diagnostic-profile figure as a printed result; the generated files remain reproducibility artifacts in the repository.
- The perturbation argument is carried by the compact sensitivity table. This table reports normalized score loss and must not be read as a global ranking across metrics.
- Error analysis is merged into the limitations section. The retained error sources are inventory incompleteness and relation recoverability.
- The biomedical transfer claim is restricted to diagnostic stress testing of relation roles, direction, polarity, causality, and evidence in scientific biomedical text. It does not claim a new biomedical relation extraction system or clinical deployment.
