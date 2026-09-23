# LEM-05: Baseline scoring over controlled perturbations

LEM-05 adds deterministic local baselines for the perturbation files produced in LEM-04. The goal is to create reproducible comparison numbers before the later LLM-adjudicated factor scoring step.

## Added metrics

- `entity_recall`: recall of source graph endpoint labels in the perturbed text.
- `entity_jaccard`: overlap between endpoint labels present in the original and perturbed text.
- `label_match`: coarse predicate-label or lexical-cue match.
- `triple_match`: binary subject + predicate + object match.
- `mine_style`: harmonic mean of node recall and edge/triple recall.
- `lemon_label_only`: label-only LEMON proxy.
- `lemon_full`: deterministic factor proxy using the fixed inventory and perturbation metadata.

`lemon_full` is not an LLM judgment. It is a deterministic proxy for controlled perturbation scoring and ablation.

## Main commands

```powershell
python -m lemon_factor.scoring.score_perturbations `
  --input data/processed/webnlg_perturbed.jsonl `
  --inventory resources/factors/webnlg.json `
  --dataset webnlg `
  --out reports/scoring_webnlg.json `
  --table-out paper/tables/table_webnlg_final.tex

python -m lemon_factor.scoring.score_perturbations `
  --input data/biomedical/perturbed/drugprot_perturbed.jsonl `
  --inventory resources/factors/drugprot.json `
  --dataset drugprot `
  --out reports/scoring_drugprot.json `
  --table-out reports/scoring_drugprot.md

python -m lemon_factor.scoring.score_perturbations `
  --input data/biomedical/perturbed/bc5cdr_perturbed.jsonl `
  --inventory resources/factors/bc5cdr.json `
  --dataset bc5cdr `
  --out reports/scoring_bc5cdr.json `
  --table-out reports/scoring_bc5cdr.md

python -m lemon_factor.scoring.aggregate `
  --inputs reports/scoring_drugprot.json reports/scoring_bc5cdr.json `
  --out reports/scoring_biomedical_summary.json `
  --table-out paper/tables/table_biomedical_final.tex
```

## Paper output

The paper uses a compact table, `paper/tables/table_scoring_final_compact.tex`, to stay within the 15-page limit. Full per-dataset tables remain available as generated artifacts.
