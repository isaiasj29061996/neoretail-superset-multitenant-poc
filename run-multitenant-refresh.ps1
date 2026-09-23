param(
    [int[]]$CustomerIds = @(142)
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location $PSScriptRoot

foreach ($customerId in $CustomerIds) {
    Write-Host "Atualizando ID_CUSTOMER=$customerId" -ForegroundColor Cyan
    & .\run-local-pipeline.ps1 -Step 02A -Customer "$customerId"
    & .\run-local-pipeline.ps1 -Step 02B -Customer "$customerId"
    foreach ($step in @("03A", "03B", "03C", "03D", "04", "05", "06", "07", "08")) {
        & .\run-local-pipeline.ps1 -Step $step -Customer "$customerId"
    }
}

& .\create-superset-kpi-views.ps1
Write-Host "Refresh multitenant concluido." -ForegroundColor Green
