param(
  [string[]]$Scoring = @(
    "reports/scoring_webnlg.json",
    "reports/scoring_drugprot.json",
    "reports/scoring_bc5cdr.json"
  ),
  [string]$Ablation = "reports/ablation_summary.json",
  [string]$Llm = "reports/llm_reliability_summary_3judges.json",
  [string]$OutDir = "reports",
  [string]$TableDir = "paper/tables"
)

python -m lemon_factor.analysis.recompute_paper_aggregates `
  --scoring $Scoring `
  --ablation $Ablation `
  --llm $Llm `
  --out-dir $OutDir `
  --table-dir $TableDir
