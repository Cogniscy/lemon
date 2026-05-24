# LEM-06: Final result tables and analysis text

LEM-06 stabilizes the deterministic results layer. It does not add LLM calls. The patch aggregates LEM-05 scoring outputs, keeps detailed WebNLG and biomedical tables as reproducible artifacts, and uses one compact table in the paper to stay within the SPECOM/LNCS page budget.

## Scope

- Aggregate WebNLG, DrugProt, and BC5CDR perturbation scoring.
- Keep deterministic baselines separate from later LLM reliability work.
- Update the paper narrative around final results rather than patch history.
- Remove development-stage LLM resource tables from the main data section.

## Main outputs

- `reports/scoring_webnlg_summary.json`
- `reports/scoring_biomedical_summary.json`
- `paper/tables/table_webnlg_final.tex`
- `paper/tables/table_biomedical_final.tex`
- `paper/tables/table_scoring_final_compact.tex`
- updated `paper/sections/01_introduction.tex`, `04_data.tex`, `05_experiments.tex`, `06_results.tex`, `08_limitations.tex`, and `09_conclusion.tex`

## Interpretation

The deterministic LEMON score in this patch is a perturbation sensitivity proxy based on fixed factor inventories and operation metadata. It is not a human or LLM semantic judgment. LLM-based reliability checks are reserved for a separate patch.
