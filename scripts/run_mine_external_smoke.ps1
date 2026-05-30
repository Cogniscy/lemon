param(
  [string]$ExternalDir = "external/kg-gen"
)

$ErrorActionPreference = "Stop"

if (!(Test-Path $ExternalDir)) {
  git clone https://github.com/stair-lab/kg-gen $ExternalDir
}

Write-Host "KGGen repository is available at $ExternalDir"
Write-Host "Next inspect experiments/MINE/README or scripts in that checkout."
Write-Host "LEM-16A does not vendor KGGen code; it only provides a local MINE-1-compatible baseline."
