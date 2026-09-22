# lemon-10 — paper consolidation and first full PDF draft

## Goal

Consolidate the code/results pipeline into a first SPECOM/LNCS-style paper draft. This stage does not introduce a new metric implementation. It turns the current artifacts into a readable research draft with authors, section structure, references, tables, limitations, and reproducible result claims.

## Inputs

- `data/reports/webnlg_lemon_factor_coverage.json`
- `data/reports/webnlg_lemon_factor_coverage_expanded.json`
- `data/reports/webnlg_baseline_comparison.json`
- `data/reports/llm_decomposition_eval.json`
- `data/reports/synthetic_adjudication_stats.json`
- `docs/research/research_brief_integration.md`
- `LEMON-Factor Related Work and Introduction — Research Brief.pdf` from Perplexity Deep Research

## Outputs

- `paper/main.tex` — consolidated LNCS-style draft.
- `paper/sections/*.tex` — full text sections.
- `paper/references.bib` — expanded bibliography.
- `paper/build/lemon_factor_draft.pdf` — first compiled draft.
- `docs/lemon-10.md` — stage notes.

## Authorship

Current draft authors:

- Tomilov A.A. — affiliation placeholder: Independent researcher, affiliation to be confirmed.
- Gineva D. — ITMO University.
- Tirskih D. — ITMO University.

The Tomilov affiliation is intentionally marked as a placeholder because it was not specified together with the author list.

## Main changes

1. Replaced anonymous paper metadata with the requested author list.
2. Expanded Introduction, Related Work, Method, Data, Experiments, Results, Error Analysis, Limitations, and Conclusion.
3. Added in-paper tables for:
   - dataset statistics;
   - LLM decomposition sanity evaluation;
   - synthetic adjudication diagnostics;
   - coverage before/after expansion;
   - baseline comparison.
4. Integrated related-work positioning from the research brief:
   - WebNLG and RDF-to-text evaluation;
   - PARENT, FactSpotter, Data-QuestEval, AlignScore;
   - FActScore/VERISCORE;
   - Smatch/S²match/Smatch++;
   - FrameNet/PropBank/VerbNet;
   - LLM-as-a-judge limitations.
5. Compiled a first PDF draft.

## Limitations explicitly preserved

- Synthetic LLM adjudication is not human expert validation.
- Expanded decompositions and cues are deterministic baselines, not gold labels.
- The current scorer is lexical and can miss paraphrases or implicit relations.
- Results are a pilot on a 100-example WebNLG development subset.

## Acceptance criteria

- `pytest -q` passes.
- `latexmk -pdf paper/main.tex` compiles a readable PDF.
- PDF contains the requested author names.
- Paper tables contain current WebNLG pilot results.
- The draft avoids unsupported superiority claims.
