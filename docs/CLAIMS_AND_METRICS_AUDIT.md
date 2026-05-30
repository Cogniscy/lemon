# Claims and Metrics Audit

This file lists the claims that are safe for the SPECOM paper and the caveats that should be kept visible while writing. The goal is to avoid overstating the contribution.

## Safe positioning

LEMON-Factor is a **source-driven, factor-level diagnostic metric for graph-text semantic fidelity**. It assumes that an explicit source graph, relation annotation, or predicate inventory is available. It is best framed as a restricted instance of layered semantic comparison, not as a general text-text semantic similarity system.

## Claim audit table

| Claim | Status | Evidence / files | Safe wording | Risk if overstated |
|---|---|---|---|---|
| LEMON-Factor opens predicate labels into semantic factors. | Supported by method and inventories. | `resources/factors/*`, `reports/factor_inventory_*.json`, `paper/sections/03_method.tex` | "Predicate labels are represented as weighted factor bundles." | Do not claim the factors are universal semantic primitives. |
| Forward and reverse scoring use the same factor schema. | Supported on WebNLG. | `reports/scoring_webnlg.json`, `paper/tables/table_webnlg_final.tex`, `paper/tables/table_webnlg_reverse_lemon.md` | "The same factor representation supports KG->Text coverage and controlled Text->KG recoverability diagnostics." | Do not call the reverse pipeline a full text-to-KG extractor. |
| Forward and Reverse LEMON-Factor are close on WebNLG. | Supported. | Forward `0.7915`; Reverse `0.7789`; see paper results. | "The small gap suggests coherence of the factor schema in both directions." | Do not interpret this as state-of-the-art graph reconstruction. |
| Relation deletion exposes the weakness of entity-only coverage. | Strongly supported. | `paper/tables/table_webnlg_relation_deletion_sanity.md`, `paper/sections/06_results.tex` | "Entity-label coverage changes by only -0.0020 while Forward LEMON-Factor drops by -0.2106." | Keep the perturbation setting explicit; this is a controlled sanity check. |
| LEMON-Factor detects polarity. | Conditionally supported. | Biomedical inventories and perturbation reports. | "LEMON-Factor reacts to polarity perturbations when polarity is encoded in the factor inventory." | Do not say it generally detects polarity in all datasets; WebNLG polarity is not encoded. |
| LEMON-Factor transfers across domains. | Partially supported. | WebNLG, DrugProt, BC5CDR reports. | "The same inventory format is applied to open-domain and biomedical graph-text data." | Do not claim universal cross-domain validity. |
| MINE-style baseline is included. | Supported as an adapted baseline. | `reports/mine1_like_lemon_pilot.json`, `reports/mine_external_inspection.*` | "MINE-style" or "MINE-inspired node/edge baseline." | Do not claim a reproduction of the KGGen/MINE benchmark. |
| LLM judges validate the metric. | Not supported. | `reports/llm_reliability_summary_3judges.json`, `reports/paper_llm_reliability_compact.json` | "LLM judges provide a complementary recoverability signal." | Do not present LLM judgments as expert validation or gold labels. |
| Radar/spider chart shows the niche of the method. | Usable with caveat. | `reports/metric_radar_comparison.json` | "Normalized diagnostic profile, not absolute accuracy." | Do not compare heterogeneous axes as if they were a single benchmark score. |
| Expert validation is done. | Not currently supported. | N/A | "Expert validation is planned / required in future work." | Do not imply human-validated inventories until the review is complete. |
| Embedding baseline is complete. | Not currently supported in paper scope. | N/A | "Embedding baseline is future work / next experiment." | Do not claim empirical superiority over embeddings yet. |
| Pragmatic layer is handled. | Not supported. | N/A | "Pragmatics is outside the current scope." | Do not claim coverage of irony, implicature, presupposition, or stance. |

## Metric interpretation notes

### LEMON-Factor score

LEMON-Factor is a partial-credit semantic coverage score over predicate factors. It is most informative as an audit trail and profile, not only as a scalar.

### Perturbation drops

The perturbation reports use mean drop under controlled synthetic damage. Larger drop means higher sensitivity to the perturbation. These are construct-validity checks, not natural paraphrase robustness tests.

### MINE-style values

The MINE-style values in this repository adapt the node/edge information idea to graph-text pairs. They should be reported as local diagnostic baselines.

### LLM reliability probe

The LLM probe compares deterministic perturbation labels with model-based factor recoverability. Moderate agreement is expected because the two signals answer different questions:

- deterministic labels record intended damage;
- model judges estimate residual semantic recoverability from context.

### Radar values

The current radar JSON explicitly notes that values are normalized diagnostic properties. The figure should be used to illustrate a niche, not to claim a global ranking of metrics.

### Layer/profile values

`reports/layer_profile_values.json` is the source for the next radar/spider figure. Its values are diagnostic properties and perturbation drops, not absolute accuracy scores. The safe wording is:

> The radar figure visualizes the diagnostic niche of LEMON-Factor under controlled perturbations.

Avoid:

> The radar figure proves that LEMON-Factor is globally more accurate than baseline systems.

The strongest layer claim currently supported is that role factors drive the largest ablation gain. Polarity should be reported only as inventory-dependent.

## Recommended paper wording

Use:

> LEMON-Factor is a factor-level diagnostic layer for graph-text semantic fidelity.

Avoid:

> LEMON-Factor is a general semantic similarity metric.

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

`reports/radar_diagnostic_profile_values.json` and `paper/figures/figure_radar_diagnostic_profile.*` instantiate the radar figure used in the Results section. The values are mean drops under controlled perturbations, taken from `reports/paper_metric_sensitivity_drops.json` and documented against `reports/layer_profile_values.json`.

Safe wording:

> The radar profile visualizes diagnostic sensitivity to controlled semantic perturbations. Larger values mean stronger response to induced damage, not higher task accuracy.

Avoid:

> The radar profile proves that LEMON-Factor is globally more accurate than entity, triple, or embedding metrics.

The figure can compare LEMON-Factor, entity recall, and triple matching because all plotted values use the same perturbation-drop scale. It still should not be treated as a general leaderboard: triple matching is a coarse detector, while LEMON-Factor is intended to provide an auditable factor-level explanation of the response.

### Vector-space perturbation baseline

`reports/embedding_baseline_perturbation.json` stores an offline vector-space perturbation check. The default backend is a character n-gram vector cosine, not a dense sentence embedding. Dense sentence-transformer cosine can be run explicitly with `scripts/run_embedding_baseline.py --backend sentence-transformers` when the optional model dependency and model files are available.

Safe wording:

> The vector-space baseline remains highly similar under many controlled perturbations, which makes it a useful topical/lexical reference signal rather than a factor-level diagnostic.

Avoid:

> LEMON-Factor universally outperforms embedding models.

Future radar extension:

> MINE-style node/edge and vector/embedding traces may be added to the radar only if all plotted values use the same perturbation-drop scale and the caption states that the figure is a diagnostic profile, not an accuracy leaderboard.
