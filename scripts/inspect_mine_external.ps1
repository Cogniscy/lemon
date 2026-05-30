param([string]$Checkout = "external/kg-gen")
$ErrorActionPreference = "Stop"
python -m lemon_factor.baselines.mine1_like.inspect_external --checkout $Checkout --out reports/mine_external_inspection.json
