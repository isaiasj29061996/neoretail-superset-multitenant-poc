param(
    [string]$Customer = "142",
    [switch]$SkipSilver,
    [switch]$SkipValidation
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Run-Step([string]$Step) {
    Write-Host ""
    Write-Host "=== Pipeline $Step / customer $Customer ===" -ForegroundColor Cyan
    & (Join-Path $PSScriptRoot "run-local-pipeline.ps1") -Step $Step -Customer $Customer
    if ($LASTEXITCODE -ne 0) {
        throw "Pipeline $Step falhou com exit code $LASTEXITCODE"
    }
}

function Run-Superset([string]$Script) {
    Write-Host ""
    Write-Host "=== Superset: $Script ===" -ForegroundColor Cyan
    docker compose exec -T superset /app/.venv/bin/python "/app/pythonpath/$Script"
    if ($LASTEXITCODE -ne 0) {
        throw "$Script falhou com exit code $LASTEXITCODE"
    }
}

$branch = (git branch --show-current).Trim()
if ($branch -ne "feat/osa-industry-certification") {
    throw "Execute este script na branch feat/osa-industry-certification. Branch atual: $branch"
}

Write-Host "=== Testes estaticos OSA ===" -ForegroundColor Cyan
docker run --rm `
    -v "${PWD}:/repo" `
    -w /repo `
    neoretail-v9-multitenant-local-engine `
    python -m pytest `
        local-engine/tests/test_osa_industry_certified_contracts.py `
        local-engine/tests/test_power_query_runtime.py -q
if ($LASTEXITCODE -ne 0) {
    throw "Testes OSA falharam."
}

if (-not $SkipSilver) {
    Run-Step "03B"
    Run-Step "03D"
}

Run-Step "06"

Write-Host ""
Write-Host "=== Serving OSA certificado ===" -ForegroundColor Cyan
& (Join-Path $PSScriptRoot "create-superset-kpi-views.ps1") `
    -Only "45_osa_certified_semantic.sql"
if ($LASTEXITCODE -ne 0) {
    throw "Serving OSA certificado falhou com exit code $LASTEXITCODE"
}
& (Join-Path $PSScriptRoot "create-superset-kpi-views.ps1") `
    -Only "46_osa_monthly_retail.sql"
if ($LASTEXITCODE -ne 0) {
    throw "Serving OSA mensal por rede falhou com exit code $LASTEXITCODE"
}

Run-Superset "bootstrap_osa_industry_certified.py"
Run-Superset "bootstrap_embedded.py"

if (-not $SkipValidation) {
    Run-Superset "validate_osa_industry_certified.py"
}

Write-Host ""
Write-Host "OSA certificada publicada para homologacao." -ForegroundColor Green
Write-Host "Slug: neoretail-v9-osa-industria-certified" -ForegroundColor Green
Write-Host "A pagina OSA antiga foi preservada para comparacao lado a lado." -ForegroundColor Green
