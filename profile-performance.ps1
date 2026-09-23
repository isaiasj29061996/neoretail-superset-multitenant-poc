param(
    [switch]$ColdCache,
    [string]$Dashboard = "",
    [string]$Chart = "",
    [int]$RowLimitCap = 20000
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location $PSScriptRoot

if ($RowLimitCap -lt 1) {
    throw "RowLimitCap precisa ser maior que zero."
}

docker compose up -d analytics-db redis superset
if ($LASTEXITCODE -ne 0) {
    throw "Nao foi possivel iniciar a stack necessaria para o benchmark."
}

if ($ColdCache) {
    Write-Host "Limpando somente o DATA_CACHE do Superset (Redis DB 2)..." -ForegroundColor Yellow
    docker compose exec -T redis redis-cli -n 2 FLUSHDB
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao limpar o cache de dados."
    }
}

function Show-ComposeStats {
    param([string[]]$Services)
    foreach ($service in $Services) {
        docker compose stats --no-stream $service
    }
}

Write-Host ""
Write-Host "Snapshot antes do teste:" -ForegroundColor Cyan
Show-ComposeStats @("superset", "analytics-db", "redis", "embedded-app")

$arguments = @(
    "compose", "exec", "-T",
    "-e", "PROFILE_ROW_LIMIT_CAP=$RowLimitCap"
)
if (-not [string]::IsNullOrWhiteSpace($Dashboard)) {
    $arguments += @("-e", "PROFILE_DASHBOARD_SLUG=$Dashboard")
}
if (-not [string]::IsNullOrWhiteSpace($Chart)) {
    $arguments += @("-e", "PROFILE_CHART_MATCH=$Chart")
}
$arguments += @(
    "superset",
    "/app/.venv/bin/python",
    "/app/pythonpath/profile_dashboard_performance.py"
)

Write-Host ""
Write-Host "Executando profiler..." -ForegroundColor Cyan
& docker @arguments
if ($LASTEXITCODE -ne 0) {
    throw "O profiler encontrou uma falha. Veja a saida acima."
}

Write-Host ""
Write-Host "Snapshot depois do teste:" -ForegroundColor Cyan
Show-ComposeStats @("superset", "analytics-db", "redis", "embedded-app")

Write-Host ""
Write-Host "Relatorio salvo em generated/performance_profile.json" -ForegroundColor Green
