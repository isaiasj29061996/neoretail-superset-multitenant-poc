param(
    [ValidateSet(
        "all", "etl_calc_v1", "etl_calc_v2", "fato_diaria",
        "fato_historico", "fato_ivd_tvd", "fato_nivel_atividade",
        "fato_preco", "mensal_causa_osa", "semanal"
    )]
    [string]$Family = "all",
    [ValidateRange(0, 10000)]
    [int]$MaxFiles = 0,
    [switch]$InventoryOnly,
    [string]$Customer = "259"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".env")) {
    throw ".env ausente. Execute .\start.ps1 primeiro."
}
$envText = Get-Content ".env" -Raw
if ($envText -notmatch '(?im)^AZURE_STORAGE_CONNECTION_STRING\s*=\s*\S+') {
    throw "Preencha AZURE_STORAGE_CONNECTION_STRING no .env antes da ingestao."
}

docker compose up -d local-engine analytics-db
if ($LASTEXITCODE -ne 0) { throw "Nao foi possivel preparar o engine local." }

$arguments = @(
    "compose", "exec", "-T", "local-engine",
    "python", "-m", "neoretail_local.candidates",
    "--family", $Family, "--max-files", "$MaxFiles", "--customer", $Customer
)
if ($InventoryOnly) { $arguments += "--inventory-only" }

& docker @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Ingestao de fatos candidatos falhou para a familia $Family."
}

Write-Host "Fatos mantidos na Bronze como candidatos; nenhuma Gold foi liberada." -ForegroundColor Green
