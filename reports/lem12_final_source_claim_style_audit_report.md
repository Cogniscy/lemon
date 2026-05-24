# LEM-12 final source/claim/style audit

## Scope

This patch performs the final source, claim, and style audit after the LLM reliability integration. It does not add new experiments.

## Main fixes

- Synchronized the abstract, introduction, experiments, results, limitations, and conclusion with the added RQ6 LLM reliability probe.
- Added explicit biomedical corpus citations for DrugProt and BC5CDR.
- Added G-Eval as the source for structured LLM evaluation and kept MT-Bench/Chatbot Arena as the source for LLM-judge bias limitations.
- Clarified that LLM factor judging is an exploratory diagnostic probe, not human validation.
- Clarified that pairwise LLM agreement is computed over overlapping factor judgments.
- Removed the large related-work positioning table and replaced it with a compact paragraph to keep the paper within the 15-page LNCS limit.
- Removed unused bibliography entries for FrameNet, PropBank, VerbNet, and unused LLM-judge survey entries from the manual bibliography.
- Shortened long model identifiers in the paper text to avoid line overflow; exact identifiers remain in the reproducibility reports.

## Source audit

- WebNLG: citations retained for WebNLG Challenge, WebNLG+, and GEM.
- DrugProt: cited as BioCreative VII chemical--gene/protein relation resource with 13 relation types and 24,526 manually annotated relations.
- BC5CDR: cited as BioCreative V corpus with 1500 PubMed articles and 3116 chemical--disease interactions.
- FactSpotter: retained as whole-triple graph-to-text factuality predecessor.
- KGGen/MINE: retained as inspiration for the local node/edge retention baseline, not as a reproduced benchmark.
- LLM judging: G-Eval and MT-Bench/Chatbot Arena support the usefulness and limitations of model-based judging.

## Build verification

- LaTeX build: passed.
- PDF pages: 15.
- Render check: 15 pages rendered successfully.
- Warnings: only minor overfull/underfull boxes remain; no undefined citations or references.

## Remaining limitations

- No human expert validation.
- Deterministic perturbations remain template-like.
- Reverse graph reconstruction is still lexical and not a full text-to-KG extractor.
- LLM reliability is exploratory and should not be described as expert adjudication.
