# LEM-01 Claim Checklist

This file fixes the claim boundary for the SPECOM version of the LEMON-Factor paper. It is a writing contract: a claim may appear in the paper only if it is covered by a table, a figure, a reproducible report, or a clear limitation statement.

## Core thesis

LEMON-Factor is a diagnostic framework for graph--text semantic alignment. It treats relation predicates as structured meaning units, decomposes them into weighted semantic factors, and evaluates whether these factors are expressed in text and recoverable from text.

## Claims allowed in the main text

1. **Predicate labels are not atomic meaning units.** A predicate such as `birthPlace`, `inhibits`, or `chemical_induced_disease` carries participant roles, entity-type expectations, directionality, and relation-specific meaning.
2. **Factor-level evaluation is more diagnostic than entity overlap.** It can expose cases where the same entities are present but the relation meaning is omitted, blurred, reversed, or weakened.
3. **The framework is bidirectional.** The same factor representation supports a forward check from graph to text and a reverse check from text to graph.
4. **The current WebNLG results are a pilot, not a final benchmark claim.** They show construct validity and diagnostic behavior under controlled perturbations.
5. **DrugProt and BC5CDR are biomedical transfer tests.** They test whether the factor schema can be instantiated outside WebNLG; they are not used to claim a state-of-the-art biomedical relation extractor.
6. **LLM-based decomposition and judging are synthetic resources.** They provide reliability evidence when used with independent producers and judges, but they do not replace human expert validation.
7. **MINE-style scores are baselines for node/edge recoverability.** Unless the official KGGen/MINE implementation is used, the paper must say "MINE-inspired" or "MINE-style", not "MINE reproduction".

## Claims requiring caution

| Claim | Required support before use | Safer wording |
|---|---|---|
| LEMON-Factor is a metric | Human or strong benchmark validation | LEMON-Factor is a diagnostic framework |
| LEMON-Factor generalizes across domains | WebNLG + DrugProt + BC5CDR results | The experiments provide initial cross-domain evidence |
| LEMON-Factor outperforms existing metrics | Direct comparison on the same data | LEMON-Factor detects errors that coarser baselines hide |
| LLM judges emulate experts | Expert agreement study | LLM judges provide synthetic, model-based evidence |
| MINE is reproduced | Official KGGen/MINE pipeline | MINE-style node/edge recall baseline |
| Biomedical results are SOTA | Official DrugProt/BC5CDR test evaluation | Biomedical transfer diagnostic |

## Claims not allowed

- LEMON-Factor is human-validated.
- LEMON-Factor is a universal semantic taxonomy.
- LEMON-Factor replaces established WebNLG, DrugProt, or BC5CDR metrics.
- The method reaches state-of-the-art biomedical relation extraction performance.
- Synthetic LLM adjudication is equivalent to expert annotation.
- The current factor inventory is complete.
- A lexical pseudo-extractor is a full text-to-KG system.

## Required limitation language

The final paper should include the following idea in plain form:

> The factor inventories and instance-level coverage judgments used in this study are synthetic and model-assisted. They should be read as a reproducible diagnostic resource, not as human expert gold. The results test whether factor-level scoring behaves as expected under controlled conditions; they do not establish expert-level semantic validity.

## Evidence mapping

| Claim | Required artifact |
|---|---|
| Entity overlap misses relation damage | WebNLG relation-deletion and relation-blur table |
| Factor groups matter | Ablation table: full vs label-only vs factor-group removals |
| Bidirectionality is feasible | Forward/Reverse LEMON table |
| Node recovery differs from edge recovery | MINE-style node/edge table |
| Biomedical transfer is plausible | DrugProt + BC5CDR transfer table |
| LLM adjudication is stable enough for a pilot | Multi-model reliability table |
