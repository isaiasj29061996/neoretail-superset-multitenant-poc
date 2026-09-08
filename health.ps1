param([int]$TimeoutSeconds = 120)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location $PSScriptRoot
. "$PSScriptRoot\scripts\container-health.ps1"

try {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker nao foi encontrado."
    }

    Wait-NeoRetailHealthy "superset-db" $TimeoutSeconds
    Wait-NeoRetailHealthy "analytics-db" $TimeoutSeconds
    Wait-NeoRetailHealthy "redis" $TimeoutSeconds
    Wait-NeoRetailOneShot "superset-init" $TimeoutSeconds
    Wait-NeoRetailHealthy "superset" $TimeoutSeconds
    Wait-NeoRetailHealthy "local-engine" $TimeoutSeconds
    Wait-NeoRetailHealthy "embedded-app" $TimeoutSeconds

    $services = @(
        "superset-db", "analytics-db", "redis", "superset-init",
        "superset", "local-engine", "embedded-app"
    )
    $services | ForEach-Object { Get-NeoRetailContainerState $_ } |
        Format-Table Service, State, Health, ExitCode -AutoSize

    foreach ($endpoint in @(
        @{ Name = "Embedded"; Url = "http://localhost:3000/health" },
        @{ Name = "Superset"; Url = "http://localhost:8088/health" },
        @{ Name = "Jupyter"; Url = "http://localhost:8888/api" }
    )) {
        $response = Invoke-WebRequest -Uri $endpoint.Url -UseBasicParsing -TimeoutSec 15
        if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 400) {
            throw "$($endpoint.Name) respondeu HTTP $($response.StatusCode)."
        }
        Write-Host "OK  $($endpoint.Name): HTTP $($response.StatusCode)" -ForegroundColor Green
    }

    Write-Host "Health check V9 Multi-tenant aprovado." -ForegroundColor Green
    exit 0
} catch {
    Write-Host "Health check V9 Multi-tenant falhou: $($_.Exception.Message)" -ForegroundColor Red
    & docker compose ps -a
    exit 1
}
