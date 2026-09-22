# LEM-01: Scope and Claims Freeze

## Goal

Freeze the paper scope before adding more experiments. The final submission should read as one coherent method paper, not as a sequence of development attempts.

## Fixed scope

The paper studies predicate-factor evaluation for graph--text semantic alignment. It does not build a new biomedical relation extraction system. WebNLG is the main graph-to-text setting. DrugProt and BC5CDR are second-domain transfer checks. MINE-style scoring is a baseline for node and edge recoverability, not a full KGGen/MINE reproduction unless the official pipeline is used.

## Fixed evidence package

The final paper must contain:

1. WebNLG forward and reverse results.
2. DrugProt and BC5CDR biomedical transfer results.
3. Entity, relation, and MINE-style baselines.
4. A compact ablation study.
5. A multi-model reliability study for synthetic factor resources.
6. A two-panel method figure.

## Writing policy

- Prefer concrete claims over broad claims.
- State what was measured and under which assumptions.
- Use "diagnostic framework" until human expert validation exists.
- Treat LLM outputs as synthetic resources.
- Keep the main paper focused on final results; development history belongs in repository reports.

## Files created in this patch

- `paper/contracts/lem01_claim_checklist.md`
- `paper/contracts/lem01_contribution_contract.md`
- `paper/contracts/lem01_result_contract.md`
- `paper/contracts/lem01_page_budget.md`
- `reports/lem01_scope_freeze_report.md`

## Files edited in this patch

- `paper/main.tex`
- `paper/sections/01_introduction.tex`
- `paper/sections/08_limitations.tex`
- `paper/sections/09_conclusion.tex`
