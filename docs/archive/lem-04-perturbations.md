# LEM-04: Perturbations and Scoring Hooks

This patch adds a deterministic perturbation builder for WebNLG, DrugProt, and BC5CDR.
The output keeps the original graph fields and stores perturbation metadata at the top level
and under `metadata.perturbation`.

## Operators

- `node_deletion`: removes one endpoint mention.
- `edge_deletion`: removes one relation cue.
- `argument_swap`: swaps subject and object mentions when both are found.
- `polarity_flip`: flips inhibition/activation, up/down regulation, or causal cues when present.
- `relation_blur`: replaces a specific relation cue with a broad cue.

## Example commands

```powershell
python -m lemon_factor.perturbations.build `
  --input data/biomedical/processed/drugprot_train.jsonl `
  --out data/biomedical/perturbed/drugprot_perturbed.jsonl `
  --limit 500

python -m lemon_factor.perturbations.build `
  --input data/biomedical/processed/bc5cdr_train.jsonl `
  --out data/biomedical/perturbed/bc5cdr_perturbed.jsonl `
  --limit 500

python -m lemon_factor.perturbations.build `
  --input data/processed/webnlg_dev.jsonl `
  --out data/processed/webnlg_perturbed.jsonl `
  --limit 500
```

## Acceptance check

The builder writes a JSON report and a Markdown table next to each output unless explicit
`--report-out` or `--table-out` paths are supplied.
