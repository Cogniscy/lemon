# lemon-13 — Controlled perturbation calibration

## Goal

`lemon-13` tests whether graph--text metrics behave as expected under controlled noise. The stage is motivated by behavioral testing: invariance tests should remain stable under meaning-preserving changes, while directional expectation tests should change in the expected direction. It also follows stress-testing work for text-generation metrics, where synthetic errors are inserted and metrics are checked for commensurate score drops.

## Noise definition

A noise operator is a deterministic perturbation of either `(gold graph, text)` or the reconstructed graph used in the reverse Text→KG setting. Each perturbation has:

- `noise_type`
- `noise_level`
- `noise_target`: `text` or `reconstructed_graph`
- `expected_direction`: `down` or `stable`
- a JSONL manifest that records exactly what changed.

Meaning-destroying operators should reduce semantic scores. Meaning-preserving operators should keep scores approximately stable.

## Implemented operators

Text operators:

- `delete_relation_phrase`: removes predicate lexical evidence from text.
- `swap_object`: replaces an object mention with an object from another example.
- `swap_predicate`: replaces a relation phrase with a wrong relation phrase.
- `entity_alias`: rewrites an entity mention to a shorter alias-like form.
- `predicate_paraphrase`: replaces a relation cue with a deterministic paraphrase.
- `punctuation_case_noise`: lowercases and removes selected punctuation.

Reconstructed-graph operators:

- `drop_edge`: removes reconstructed edges.
- `drop_node`: removes reconstructed nodes and incident edges.
- `graph_swap_predicate`: changes reconstructed edge predicates.
- `hallucinate_edge`: adds low-confidence non-gold edges.

## Saved artifacts

All noise injection results are saved separately under `data/perturbed/lemon13/`:

- perturbed GraphText JSONL files for text noise;
- perturbed reconstructed graph JSONL files;
- `*_manifest.jsonl` files with operation-level audit records;
- row-level calibration details in `data/reports/webnlg_calibration_details.jsonl`.

## Metrics

The calibration report includes:

- Forward LEMON-Factor;
- Reverse LEMON-Factor;
- MINE-style composite node/edge score;
- MINE-style fact recoverability;
- exact label coverage;
- predicate cue coverage.

For each metric and noise type, the code reports:

- sensitivity slope;
- Spearman correlation between noise level and score;
- monotonicity violation count;
- preserving-noise stability delta.

## Commands

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

## Current pilot result

The pilot calibration shows zero monotonicity violations for the configured noise grid. Reverse LEMON and MINE-style edge/fact scores are strongly sensitive to destructive graph noise. Forward LEMON reacts to destructive text noise such as relation phrase deletion and object swaps, while exact label overlap remains almost unchanged under relation phrase deletion, which supports the diagnostic value of factor-level scoring.

## Limitations

The perturbations are deterministic and template-like. They are designed for controlled calibration rather than natural paraphrase generation. LLM-generated paraphrases are intentionally left for a later stage because they would make the perturbation semantics harder to audit.

## lemon-13.1 cleanup

`lemon-13.1` separates calibration summaries by perturbation side. Text-side destructive noise is most relevant for Forward LEMON, exact-label coverage, and predicate-cue coverage. Graph-side destructive noise is most relevant for Reverse LEMON and MINE-style node/edge recoverability. The main summary table is now a direction-aware targeted table rather than a single global average over unrelated noise targets.

The report also adds `perturbation_quality` flags:

- `clean`: controlled operator with a clear expected semantic effect;
- `weak_template`: approximate meaning-preserving template that may leak lexical artifacts;
- `precision_only`: operator mainly intended for precision/relevance stress tests.

This prevents overinterpreting weak predicate paraphrases and alias rewrites as fully validated meaning-preserving transformations.
