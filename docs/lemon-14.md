# lemon-14 — Paper reframing after bidirectional, MINE-style, and calibration experiments

This patch rewrites the SPECOM/LNCS draft around the final research story produced by lemon-11 through lemon-13.1.

## Main change

The paper is no longer framed as a single graph-to-text coverage metric. It is framed as a bidirectional factor-level semantic alignment framework for graph--text pairs.

## Updated paper story

- Forward LEMON: KG->Text semantic coverage.
- Reverse LEMON: Text->KG semantic recoverability.
- MINE-style baseline: node/edge information retention and fact-level recoverability.
- Perturbation calibration: controlled destructive and preserving noise.

## Main empirical claims

- Expanded Forward LEMON = 0.7915.
- Reverse LEMON = 0.7789.
- Deterministic MINE-style composite = 0.8028.
- Fixed-subset node information = 0.9600.
- Fixed-subset edge information = 0.5400.
- Fixed-subset LLM fact recoverability = 0.5200.
- Relation deletion changes exact entity-label coverage by about -0.0020 but Forward LEMON by about -0.2106.

## Paper edits

- Title and abstract now emphasize bidirectional graph--text semantic alignment.
- Introduction is organized around four research questions.
- Related Work is reorganized by evaluation granularity: reference metrics, source-aware metrics, triple-level factuality, atomic facts, node/edge information, and LEMON factors.
- Method now describes a single bidirectional framework: predicate factorization, Forward LEMON, Reverse LEMON, MINE-style baseline, and calibration.
- Experiments and Results are organized by RQ1--RQ4.
- Limitations now include explicit terminological distinctions to avoid overclaiming: human gold, synthetic LLM adjudication, MINE-style adaptation, deterministic MINE-style score.

## Verification

- `pytest -q`: 158 passed.
- LaTeX draft compiled to PDF successfully.
- PDF rendered to page images and visually checked for gross layout failures.

## Remaining paper work

- Tighten pages if the target page limit becomes stricter.
- Verify all BibTeX metadata before submission.
- Add human validation or move it clearly to future work.
