param(
  [int]$Limit = 60,
  [string]$Model = "google/gemini-2.0-flash-001",
  [string]$JudgeId = "mine1_like_llm",
  [switch]$RunApi,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"

python -m lemon_factor.baselines.mine1_like.prepare_llm_judge `
  --items data/mine_probe/lemon_mine_items.jsonl `
  --out data/mine_probe/mine1_like_llm_prompts.jsonl `
  --model $Model `
  --judge-id $JudgeId `
  --limit $Limit

if ($RunApi -or $DryRun) {
  $dryFlag = @()
  if ($DryRun) { $dryFlag = @("--dry-run") }
  python -m lemon_factor.baselines.mine1_like.run_openrouter_judge `
    --prompts data/mine_probe/mine1_like_llm_prompts.jsonl `
    --out reports/mine1_like_llm_judgments.jsonl `
    --limit $Limit `
    @dryFlag

  python -m lemon_factor.baselines.mine1_like.score `
    --items data/mine_probe/lemon_mine_items.jsonl `
    --mode llm_saved `
    --judgments reports/mine1_like_llm_judgments.jsonl `
    --out reports/mine1_like_llm_lemon_pilot.json `
    --scores-out reports/mine1_like_llm_lemon_pilot_scores.jsonl
}
else {
  Write-Host "Prepared prompts only. Re-run with -RunApi to call OpenRouter or -DryRun for a no-cost schema test."
}
