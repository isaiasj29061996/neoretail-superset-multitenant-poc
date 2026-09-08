param(
    [switch]$Rebuild,
    [int]$HealthTimeoutSeconds = 300
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location $PSScriptRoot
. "$PSScriptRoot\scripts\container-health.ps1"

function Write-Step([int]$Number, [string]$Text) {
    Write-Host ""
    Write-Host "[$Number/7] $Text" -ForegroundColor Cyan
}

function Invoke-Docker([string]$Step, [string[]]$Arguments) {
    & docker @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Step falhou (codigo $LASTEXITCODE)." }
}

try {
    Write-Step 1 "Pre-flight e configuracao local"
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker nao foi encontrado. Abra o Docker Desktop e tente novamente."
    }
    & docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Desktop nao esta pronto. Aguarde o engine iniciar."
    }
    if (-not (Test-Path ".env")) {
        Copy-Item ".env.example" ".env"
        Write-Host "Criado .env. O start local funciona sem Blob; o pipeline exige a connection string." -ForegroundColor Yellow
    }
    New-Item -ItemType Directory -Force -Path ".\generated", ".\certs" | Out-Null

    Write-Step 2 "Validacao do Compose e build"
    Invoke-Docker "Validacao do Compose" @("compose", "config", "--quiet")
    if ($Rebuild) {
        Invoke-Docker "Build das imagens" @(
            "compose", "build", "superset-init", "superset", "local-engine", "embedded-app"
        )
    } else {
        Write-Host "Use -Rebuild quando precisar reconstruir as imagens." -ForegroundColor DarkGray
    }

    Write-Step 3 "Infraestrutura: Metadata, Analytics e Redis"
    Invoke-Docker "Inicializacao dos bancos" @(
        "compose", "up", "-d", "--remove-orphans", "superset-db", "analytics-db", "redis"
    )
    Wait-NeoRetailHealthy "superset-db" $HealthTimeoutSeconds
    Wait-NeoRetailHealthy "analytics-db" $HealthTimeoutSeconds
    Wait-NeoRetailHealthy "redis" $HealthTimeoutSeconds

    Write-Step 4 "Bootstrap do Superset e conexao Analytics"
    Invoke-Docker "Inicializacao do superset-init" @(
        "compose", "up", "-d", "--no-deps", "superset-init"
    )
    Wait-NeoRetailOneShot "superset-init" $HealthTimeoutSeconds

    Write-Step 5 "Superset e PySpark local"
    Invoke-Docker "Inicializacao dos servicos analiticos" @(
        "compose", "up", "-d", "--no-deps", "superset", "local-engine"
    )
    Wait-NeoRetailHealthy "superset" $HealthTimeoutSeconds
    Wait-NeoRetailHealthy "local-engine" $HealthTimeoutSeconds

    Write-Step 6 "Portal NeoRetail Embedded"
    Invoke-Docker "Inicializacao do Embedded" @(
        "compose", "up", "-d", "--no-deps", "embedded-app"
    )
    Wait-NeoRetailHealthy "embedded-app" $HealthTimeoutSeconds

    Write-Step 7 "Health check final"
    & "$PSScriptRoot\health.ps1" -TimeoutSeconds 30
    if ($LASTEXITCODE -ne 0) { throw "Health check final falhou." }

    Write-Host ""
    Write-Host "V9 Multi-tenant iniciada e saudavel." -ForegroundColor Green
    Write-Host "NeoRetail Embedded:   http://localhost:3000" -ForegroundColor Green
    Write-Host "Superset Admin:       http://localhost:8088" -ForegroundColor Green
    Write-Host "PySpark/Jupyter:      http://localhost:8888" -ForegroundColor Green
    Write-Host "PostgreSQL Analytics: localhost:5433" -ForegroundColor Green
    Write-Host "Refresh dos clientes: .\run-multitenant-refresh.ps1" -ForegroundColor Cyan
} catch {
    Write-Host ""
    Write-Host "A inicializacao da V9 falhou: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Estado atual dos containers:" -ForegroundColor Yellow
    & docker compose ps -a
    exit 1
}
