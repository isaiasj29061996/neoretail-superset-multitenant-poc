param(
    [int[]]$CustomerIds = @()
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location $PSScriptRoot

# No implicit baseline refresh. Preflight resolves only automatic tenants and
# rejects pending source metadata before any data pipeline step is started.
if ($CustomerIds.Count -eq 0) {
    $contextsJson = docker compose exec -T local-engine python -m neoretail_local.customers --active --require-source
    if ($LASTEXITCODE -ne 0) { throw "Automatic tenant resolution failed; no refresh started." }
    $CustomerIds = @($contextsJson | ConvertFrom-Json | ForEach-Object { $_.id_customer })
    if ($CustomerIds.Count -eq 0) { throw "No automatic tenants configured; no refresh started." }
}

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
