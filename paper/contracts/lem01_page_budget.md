# LEM-01 Page Budget

Target: 14--15 LNCS pages including references, tables, and figures. The venue constraint is 10--15 pages, so the paper should not rely on appendices for its main evidence.

| Section | Target pages | Notes |
|---|---:|---|
| Abstract + keywords | 0.3 | No unsupported dataset claims |
| Introduction | 1.2 | Thesis, gap, contributions |
| Related work | 1.7 | Keep to graph-to-text metrics, biomedical RE metrics, LLM-as-judge |
| Method | 2.0 | Formalism + Figure 1 |
| Data and resources | 1.4 | WebNLG, DrugProt, BC5CDR, factor inventories |
| Experiments | 1.6 | Baselines, perturbations, ablation, reliability design |
| Results | 2.8 | Main tables only |
| Discussion / error analysis | 1.0 | Interpret the diagnostic signal |
| Limitations | 0.9 | LLM adjudication, pseudo-extraction, biomedical scope |
| Conclusion | 0.4 | Short and restrained |
| References | 1.2 | Use compact, high-value citations |

## Compression rules

- Merge dataset statistics into one table.
- Merge DrugProt and BC5CDR results into one biomedical table.
- Put only the strongest ablation table in the main text.
- Move detailed prompts and raw reliability outputs to the repository.
- Do not show the development history of the factor inventory in the main text.
