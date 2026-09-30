param(
    [ValidateRange(0.01, 1.0)]
    [double]$SampleFraction = 0.35,
    [string]$Customer = "142",
    [switch]$RebuildInfra,
    [switch]$SkipTests,
    [ValidateRange(20, 500)]
    [int]$MinFreeDiskGB = 80
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location $PSScriptRoot

function Write-Stage([string]$Text) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor DarkCyan
    Write-Host $Text -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor DarkCyan
}

function Assert-LastExit([string]$Name) {
    if ($LASTEXITCODE -ne 0) {
        throw "$Name falhou (codigo $LASTEXITCODE)."
    }
}

function Show-Disk([string]$Label) {
    $drive = Get-PSDrive C
    $freeGb = [math]::Round($drive.Free / 1GB, 2)
    Write-Host "$Label - C: $freeGb GB livres" -ForegroundColor DarkGray
    return $freeGb
}

function Run-PipelineStep(
    [string]$Step,
    [string[]]$ExtraArgs = @()
) {
    Write-Stage "Pipeline $Step"
    $args = @(
        "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", (Join-Path $PSScriptRoot "run-local-pipeline.ps1"),
        "-Step", $Step,
        "-Customer", $Customer
    ) + $ExtraArgs
    & powershell.exe @args
    Assert-LastExit "Etapa $Step"
    [void](Show-Disk "Depois do $Step")
}

Write-Stage "Pre-flight AMBEV 35%"
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker nao encontrado."
}
& docker info *> $null
Assert-LastExit "Docker Engine"

if (-not (Test-Path ".env")) {
    throw ".env ausente."
}
$envText = Get-Content ".env" -Raw
if ($envText -notmatch '(?im)^AZURE_STORAGE_CONNECTION_STRING\s*=\s*\S+') {
    throw "AZURE_STORAGE_CONNECTION_STRING ausente no .env."
}

$freeGb = Show-Disk "Inicio"
if ($freeGb -lt $MinFreeDiskGB) {
    throw "Espaco livre insuficiente: $freeGb GB. Minimo configurado: $MinFreeDiskGB GB."
}

Write-Stage "Infraestrutura Docker / Superset"
$startArgs = @(
    "-NoProfile", "-ExecutionPolicy", "Bypass",
    "-File", (Join-Path $PSScriptRoot "start.ps1")
)
if ($RebuildInfra) { $startArgs += "-Rebuild" }
& powershell.exe @startArgs
Assert-LastExit "Inicializacao da infraestrutura"

if (-not $SkipTests) {
    Write-Stage "Testes criticos antes da carga"
    docker compose exec -T local-engine pytest -q `
        /workspace/local-engine/tests/test_candidate_sampling.py `
        /workspace/local-engine/tests/test_postgres_serving.py
    Assert-LastExit "Testes criticos"
}

# Rodamos as etapas explicitamente para preservar os caminhos especiais da AMBEV:
# 03D -> partitioned_validation
# 06  -> gold_serving com janelas locais de serving
Run-PipelineStep "00"
Run-PipelineStep "01"
Run-PipelineStep "02A"

$sampleText = $SampleFraction.ToString([System.Globalization.CultureInfo]::InvariantCulture)
Run-PipelineStep "02B" @(
    "-Family", "customer_daily",
    "-SampleFraction", $sampleText,
    "-PruneRawCache"
)

Run-PipelineStep "03A"
Run-PipelineStep "03B"
Run-PipelineStep "03C"
Run-PipelineStep "03D"
Run-PipelineStep "04"
Run-PipelineStep "05"
Run-PipelineStep "06"
Run-PipelineStep "07"
Run-PipelineStep "08"

Write-Stage "Views e marts de serving do Superset"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File `
    (Join-Path $PSScriptRoot "create-superset-kpi-views.ps1")
Assert-LastExit "Criacao das views/marts"

Write-Stage "Dashboards do Superset"
$bootstraps = @(
    "bootstrap_overview.py",
    "bootstrap_overview_quantity.py",
    "bootstrap_panorama.py",
    "bootstrap_osa_industry.py",
    "bootstrap_osa_industry_certified.py",
    "bootstrap_stock_optimization.py",
    "bootstrap_export.py",
    "bootstrap_embedded.py"
)
foreach ($bootstrap in $bootstraps) {
    Write-Host "Executando $bootstrap..." -ForegroundColor Yellow
    docker compose exec -T superset `
        /app/.venv/bin/python "/app/pythonpath/$bootstrap"
    Assert-LastExit $bootstrap
}

Write-Stage "Health check final"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File `
    (Join-Path $PSScriptRoot "health.ps1") -TimeoutSeconds 60
Assert-LastExit "Health check"

$finalFree = Show-Disk "Fim"
Write-Host ""
Write-Host "AMBEV concluida com amostra aproximada de $([math]::Round($SampleFraction * 100, 2))%." -ForegroundColor Green
Write-Host "C: $finalFree GB livres." -ForegroundColor Green
Write-Host "Superset Admin:     http://localhost:8088" -ForegroundColor Green
Write-Host "NeoRetail Embedded: http://localhost:3000" -ForegroundColor Green
