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
    $contextJson = docker compose exec -T local-engine python -m neoretail_local.customers --tenant "$customerId" --require-source
    if ($LASTEXITCODE -ne 0) { throw "Tenant preflight failed; no pipeline started." }
    $context = $contextJson | ConvertFrom-Json
    if (-not $context.execution_active -or $context.id_customer -eq 142) {
        throw "Tenant $customerId is not active for automatic refresh."
    }
    Write-Host "Atualizando ID_CUSTOMER=$customerId" -ForegroundColor Cyan
    & .\run-local-pipeline.ps1 -Step 02A -Customer "$customerId"
    & .\run-local-pipeline.ps1 -Step 02B -Customer "$customerId"
    foreach ($step in @("03A", "03B", "03C", "03D", "04", "05", "06", "07", "08")) {
        & .\run-local-pipeline.ps1 -Step $step -Customer "$customerId"
    }
    docker compose exec -T local-engine python -m neoretail_local.marts --tenant "$customerId"
    if ($LASTEXITCODE -ne 0) { throw "Tenant marts failed; serving was not changed." }
}

$servingIds = @($CustomerIds | ForEach-Object { [string]$_ })
docker compose exec -T local-engine python -m neoretail_local.marts --tenant $servingIds[0] --keep-published-tenants --serving-tenants @servingIds
if ($LASTEXITCODE -ne 0) { throw "Serving publication failed." }
docker compose exec -T -e NEORETAIL_CONSUMPTION_SCHEMA=serving superset python /app/pythonpath/bootstrap_serving.py --apply
if ($LASTEXITCODE -ne 0) { throw "Superset serving migration failed." }
Write-Host "Refresh multitenant concluido." -ForegroundColor Green
