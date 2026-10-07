param(
    [ValidateSet(
        "all", "00", "01", "02", "02A", "02B",
        "03", "03A", "03B", "03C", "03D",
        "04", "05", "06", "07", "08"
    )]
    [string]$Step = "all",
    [ValidateSet(
        "all", "customer_daily", "etl_calc_v1", "etl_calc_v2", "fato_diaria",
        "fato_historico", "fato_ivd_tvd", "fato_nivel_atividade",
        "fato_preco", "mensal_causa_osa", "semanal"
    )]
    [string]$Family = "all",
    [ValidateRange(0, 10000)]
    [int]$MaxFiles = 0,
    [ValidateRange(0.01, 1.0)]
    [double]$SampleFraction = 1.0,
    [switch]$PruneRawCache,
    [switch]$InventoryOnly,
    [switch]$CustomerOnlyDimensions,
    [Parameter(Mandatory = $false)]
    [string]$Customer = "142"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if ($CustomerOnlyDimensions -and $Step -notin @("02", "02A")) {
    throw "-CustomerOnlyDimensions exige -Step 02 ou 02A; nenhuma etapa foi iniciada."
}

if (-not (Test-Path ".env")) { throw ".env ausente. Execute .\start.ps1 primeiro." }
$envText = Get-Content ".env" -Raw
if ($envText -notmatch '(?im)^AZURE_STORAGE_CONNECTION_STRING\s*=\s*\S+') {
    throw "Preencha AZURE_STORAGE_CONNECTION_STRING no .env antes do pipeline."
}

if ($MaxFiles -gt 0 -and $SampleFraction -lt 1.0) {
    throw "Use -MaxFiles ou -SampleFraction, nao os dois ao mesmo tempo."
}

docker compose up -d local-engine analytics-db
if ($LASTEXITCODE -ne 0) { throw "Nao foi possivel preparar o engine local." }

if ($Step -eq "02B") {
    $sampleText = $SampleFraction.ToString([System.Globalization.CultureInfo]::InvariantCulture)
    $arguments = @(
        "compose", "exec", "-T", "local-engine",
        "python", "-m", "neoretail_local.candidates",
        "--family", $Family,
        "--max-files", "$MaxFiles",
        "--sample-fraction", $sampleText,
        "--customer", $Customer
    )
    if ($PruneRawCache) { $arguments += "--prune-raw-cache" }
    if ($InventoryOnly) { $arguments += "--inventory-only" }
    & docker @arguments
} elseif ($Step -in @("02", "02A") -and $CustomerOnlyDimensions) {
    docker compose exec -T -e NEORETAIL_DIMENSIONS_CUSTOMER_ONLY=true local-engine python -m neoretail_local.pipeline --step 02 --customer $Customer
} elseif ($Step -eq "03D" -and $Customer -in @("142", "AMBEV", "290", "LACTALIS")) {
    docker compose exec -T local-engine python -m neoretail_local.partitioned_validation --customer $Customer
} elseif ($Step -eq "06" -and $Customer -in @("142", "AMBEV", "290", "LACTALIS")) {
    docker compose exec -T local-engine python -m neoretail_local.gold_serving --customer $Customer
} else {
    $pipelineStep = if ($Step -eq "02A") { "02" } else { $Step }
    docker compose exec -T local-engine python -m neoretail_local.pipeline --step $pipelineStep --customer $Customer
}
if ($LASTEXITCODE -ne 0) { throw "Pipeline local falhou na etapa $Step." }

Write-Host "Pipeline local concluido. Consulte generated\local_pipeline_summary.json e o schema gold." -ForegroundColor Green
