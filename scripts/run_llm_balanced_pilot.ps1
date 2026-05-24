param(
    [string]$Prompts = "data/reliability/llm_probe_prompts.jsonl",
    [string]$Out = "reports/llm_judgments/gemini_flash_balanced.jsonl",
    [string]$RawOut = "reports/llm_judgments/gemini_flash_balanced_raw.jsonl",
    [string]$ReportDir = "reports/llm_judgments",
    [string]$Model = "google/gemini-2.0-flash-001",
    [string]$JudgeId = "gemini_flash_balanced",
    [int]$PerDataset = 15,
    [int]$Timeout = 45,
    [int]$MaxRetries = 3,
    [int]$Seed = 13,
    [switch]$NoShuffle,
    [switch]$Fresh
)

$ErrorActionPreference = "Stop"

if (-not $env:OPENROUTER_API_KEY) {
    throw "OPENROUTER_API_KEY is not set."
}

New-Item -ItemType Directory -Force -Path (Split-Path $Out) | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $RawOut) | Out-Null
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

if ($Fresh) {
    Remove-Item -Force -ErrorAction SilentlyContinue $Out
    Remove-Item -Force -ErrorAction SilentlyContinue $RawOut
    Remove-Item -Force -ErrorAction SilentlyContinue "$ReportDir/gemini_flash_balanced_*.json"
}

$shuffleArgs = @()
if (-not $NoShuffle) { $shuffleArgs += "--shuffle" }

$datasets = @("webnlg", "drugprot", "bc5cdr")
foreach ($dataset in $datasets) {
    $reportOut = Join-Path $ReportDir "gemini_flash_balanced_$dataset`_report.json"
    Write-Host "Running $dataset ($PerDataset items) -> $Out"
    python -m lemon_factor.reliability.run_openrouter_judge `
        --prompts $Prompts `
        --out $Out `
        --model $Model `
        --judge-id $JudgeId `
        --prompt-style no_rationale `
        --response-format json_schema `
        --fallback-response-format json_object `
        --require-parameters `
        --dataset $dataset `
        --limit $PerDataset `
        --timeout $Timeout `
        --max-retries $MaxRetries `
        --seed $Seed `
        @shuffleArgs `
        --raw-out $RawOut `
        --report-out $reportOut
}

Write-Host "Done. Summarize with:"
Write-Host "python -m lemon_factor.reliability.summarize_llm_probe --items data/reliability/llm_probe_items.jsonl --judgments reports/llm_judgments/*.jsonl --out reports/llm_reliability_summary.json --examples-out reports/llm_reliability_disagreements.md"
