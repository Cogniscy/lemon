param(
  [int]$PerDataset = 20
)

$ErrorActionPreference = "Stop"

python -m lemon_factor.baselines.mine1_like.prepare `
  --inputs data/processed/webnlg_perturbed.jsonl data/biomedical/perturbed/drugprot_perturbed.jsonl data/biomedical/perturbed/bc5cdr_perturbed.jsonl `
  --out data/mine_probe/lemon_mine_items.jsonl `
  --per-dataset $PerDataset

python -m lemon_factor.baselines.mine1_like.score `
  --items data/mine_probe/lemon_mine_items.jsonl `
  --out reports/mine1_like_lemon_pilot.json `
  --scores-out reports/mine1_like_lemon_pilot_scores.jsonl `
  --mode lexical

python -m lemon_factor.baselines.triple_f1 `
  --inputs data/processed/webnlg_perturbed.jsonl data/biomedical/perturbed/drugprot_perturbed.jsonl data/biomedical/perturbed/bc5cdr_perturbed.jsonl `
  --out reports/triple_f1_baseline.json `
  --scores-out reports/triple_f1_baseline_scores.jsonl `
  --per-dataset $PerDataset
