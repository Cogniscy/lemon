# Result provenance and availability

Repository paths below are relative to the checkout. Available means inspected
locally; tracked status and source availability are separate concerns.

| Result | Producer | Inputs | Availability / interpretation |
|---|---|---|---|
| Offline example scores and summary | `python -m lemon_factor reproduce-demo --out artifacts/demo` | Packaged cases.json, embedded factor weights and cues | Included in wheel; synthetic lexical coverage |
| Forward WebNLG coverage | `python -m lemon_factor.coverage.run_webnlg_coverage --help` | Prepared GraphText JSONL, decomposition JSON, lexical cues | Original exact invocation and complete upstream data must accompany any replication |
| Perturbation score tables | `python -m lemon_factor.scoring.score_perturbations` | Perturbed JSONL and resources/factors/*.json | Inputs named in local scoring reports; processed corpora are not tracked |
| Ablation | `python -m lemon_factor.scoring.ablate --inputs ... --out ...` | Scoring reports plus the input/inventory paths they name | Prescribed damage model analysis, not independent text evaluation |
| Compact drops/ablation/LLM tables | `python -m lemon_factor.analysis.recompute_paper_aggregates` | Three scoring JSONs, ablation_summary.json, llm_reliability_summary_3judges.json | Commands in REPRODUCIBILITY.md; historical JSONs are local/ignored |
| Vector control | `python scripts/run_embedding_baseline.py --backend ...` | Selected original/perturbed text pairs | New reports record algorithm, versions and hashes; old backend can be ambiguous |
| Diagnostic plot | `python scripts/make_radar_profile.py` | Sensitivity, vector and layer-profile reports | New inputs selectable; defaults preserve historical outputs |
| Expert agreement, 119/140 and coefficients | `python -m lemon_factor.analysis.expert_review` | `annotation/expert_trace_review/ratings.csv`, four reviewers, 35 rows | Included anonymized judgments, hashes and coefficient definitions; ordinal alpha 0.873 |

No missing run configuration has been reconstructed from final table numbers.
Historical local results are useful supporting artifacts, not a complete distributable
reproduction package.

## Data sources

See [source references](reference_sources.md) and acquisition manifests emitted by
the dataset downloaders. WebNLG, DrugProt, BC5CDR and BioRED have separate source
and usage terms. Do not publish raw corpora without checking those terms.
Acquisition and conversion remain explicit research steps.

## Artifact policy

Publish source, package fixtures, tests, inventories, paper source and necessary
illustrative figures. Keep newly generated outputs under ignored `artifacts/`.
Existing reports/*.md and paper tables remain historical references.
Local reports/*.json are not automatically made public: a release bundle should
include only reviewed aggregate reports and their input/configuration manifests.
Raw LLM responses, text corpora and expert submissions require separate review.
This implementation does not upload or publish any data.

## Prepared-input verification, 2026-09-22

`scripts/reproduce_local_research.py` matched all 5,045 historical score rows and
summary metrics from the three saved scoring reports, in both the project environment
and a clean Windows Python 3.11 environment. Manifests in
`artifacts/verified-research-clean311/manifest.json` record input/inventory hashes.
This confirms the prepared-input scoring step, not the upstream data preparation
or the reported human/model judgments.
