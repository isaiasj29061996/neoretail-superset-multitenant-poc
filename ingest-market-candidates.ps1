param(
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
    "python", "-m", "neoretail_local.market", "--max-files", "$MaxFiles", "--customer", $Customer
)
if ($InventoryOnly) { $arguments += "--inventory-only" }

& docker @arguments
if ($LASTEXITCODE -ne 0) { throw "Ingestao Bronze de mercado falhou." }

Write-Host "Parquets de mercado mantidos na Bronze; nenhuma Gold foi liberada." -ForegroundColor Green
