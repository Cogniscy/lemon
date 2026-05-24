param(
    [string]$Items = "data/reliability/llm_probe_items.jsonl",
    [string]$Judgments = "reports/llm_judgments/*.jsonl",
    [string]$Out = "reports/llm_reliability_summary.json",
    [string]$ExamplesOut = "reports/llm_reliability_disagreements.md",
    [switch]$IncludeMock
)

$ErrorActionPreference = "Stop"
$argsList = @(
    "-m", "lemon_factor.reliability.summarize_llm_probe",
    "--items", $Items,
    "--judgments", $Judgments,
    "--out", $Out,
    "--examples-out", $ExamplesOut
)
if ($IncludeMock) { $argsList += "--include-mock" }
python @argsList
