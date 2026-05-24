# LEM-04 Perturbation Report

Implemented a shared perturbation builder for WebNLG, DrugProt, and BC5CDR.

## Generated pilot outputs

- `data/biomedical/perturbed/drugprot_perturbed.jsonl`
- `data/biomedical/perturbed/bc5cdr_perturbed.jsonl`
- `data/processed/webnlg_perturbed.jsonl`

## Validation

- Unit tests pass.
- Generated perturbation reports pass schema validation.
- The source graph is preserved in each perturbed record.

## Notes

Polarity flips are active mainly for biomedical data. WebNLG has no stable universal polarity
field, so polarity-flip records are retained for interface consistency but may be unchanged.
