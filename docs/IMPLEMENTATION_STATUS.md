# Implementation and verification status

Updated 2026-09-23.

## Implemented

- Installable wheel/sdist, packaged resources, dependency extras and offline demo.
- Reproduction command with scores, summary, configuration and input hashes.
- Versioned factor_damage_proxy reports and compatible readers for historical reports.
- Explicit vector backends, without silent algorithm fallback.
- CI workflow for Windows/Linux and Python 3.11/3.12.
- Updated manuscript terminology, documentation, provenance map and archived development notes.
- Prepared-data research replay that fails if any historical score row or summary differs.
- Ablation now respects the sample count recorded by its source scoring report.

## Verified locally

- Original baseline: 221 passed, 4 failed.
- Source snapshot containing tracked and intended new files, without ignored local data:
  Windows Python 3.11 and 3.12 each produced 230 passed, 3 historical-artifact skips,
  2 documented expected failures before the two new replay regression tests.
- Smaller CI-only patch applied to the original repository state:
  232 passed, 3 artifact tests deselected, 2 expected failures on Windows Python 3.11.
- Final wheel built and installed in an independent environment outside the source tree.
  CLI, packaged resources, network-free demo and generated outputs passed smoke checks.
- Research replay matched all 5,045 score rows and summaries for WebNLG (500),
  DrugProt (2,100), and BC5CDR (2,445), including a clean Python 3.11 environment.
- Pinned deterministic scoring/plot environment:
  constraints/deterministic-windows-py311.txt.
- Revised paper with the expert-review correction built with MiKTeX: 15 pages, no overfull boxes or undefined references.
  Tables were visually inspected before the latest expert-review text update.
  PDF: artifacts/paper/lemon-reviewed.pdf. The tracked historical PDF is preserved.

## Local research outputs

- artifacts/verified-research-20260922/
- artifacts/verified-research-clean311/

Each replay contains scoring reports, ablations and a manifest with SHA-256 values.
These use existing prepared inputs. They do not re-download corpora, reproduce
data preparation, invoke LLMs, or recalculate expert agreement.

- Final full test run: 239 passed, 2 documented expected failures.
- Clean release snapshot: 236 passed, 3 artifact tests deselected, 2 expected failures.
- Rebuilt wheel and sdist include LICENSE and expert-review code. The wheel passed
  installation and offline smoke checks in an independent environment.
- The 15-page reviewed PDF includes the RSF project acknowledgment.

## Expert review

Four completed source forms from the supplied traces directory were normalized to
anonymized ratings; one empty template was excluded. The original files are unchanged.
Included: annotation/expert_trace_review/{ratings.csv,summary.json,manifest.json}.
Exact agreement: 119/140. Ordinal alpha: 0.8726722592; interval-rank alpha:
0.8710995016. Both independently match the krippendorff package to 1e-12.
The manuscript now reports ordinal alpha 0.873 and explains the pilot's limits.

## Remote CI blocker

The user approved the separate 33-file CI-only branch and subsequent merge into
the default branch (master). The approved request is below the review size limit,
but GitHub returned HTTP 403: Resource not accessible by integration.
Local SSH authentication also fails, and HTTPS has no working credentials.
No branch, commit, pull request or workflow run has been created remotely.
Contents and Workflows write access, or working local Git authentication, is needed.
The earlier full-tree request exceeded the automatic review size limit; the
separately approved reduced request is blocked by authentication instead.
Retry on 2026-09-23 confirmed both blockers.
The complete implementation is prepared on local branch improvement/reproducible-repository.
Details: CI_REVIEW.md. The remote master branch remains unchanged.

## Still requiring input or further verification

- Working GitHub write access; Linux and remote Actions results remain unverified.
- Apache-2.0 applied following the maintainer instruction to proceed. Funding
  acknowledgment: Russian Science Foundation, project 26-11-00193. The specific
  grant agreement and institutional rights arrangements were not legally reviewed.
- Full upstream dataset preparation and model-run reproduction; constraints cover
  verified deterministic scoring/plots only, not dense models or acquisition.
- Known lexical negation and participant-binding false positives remain documented;
  correcting those requires separate evidence-layer research.
