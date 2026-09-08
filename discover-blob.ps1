param([switch]$Rebuild)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker nao foi encontrado. Abra o Docker Desktop e tente novamente."
}
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    throw "O .env foi criado. Preencha AZURE_STORAGE_CONNECTION_STRING e execute novamente."
}
$envText = Get-Content ".env" -Raw
if ($envText -notmatch '(?im)^AZURE_STORAGE_CONNECTION_STRING\s*=\s*\S+') {
    throw "AZURE_STORAGE_CONNECTION_STRING precisa ser preenchida no .env."
}
New-Item -ItemType Directory -Force -Path ".\generated" | Out-Null
$arguments = @("compose", "--profile", "blob", "run", "--rm")
if ($Rebuild) { $arguments += "--build" }
$arguments += "blob-profiler"
Write-Host "Inventariando Parquets do Azure Blob sem usar PBIX..." -ForegroundColor Cyan
& docker @arguments
if ($LASTEXITCODE -ne 0) { throw "Profiling do Blob falhou (codigo $LASTEXITCODE)." }
Write-Host "Inventario criado em .\generated\blob_inventory.csv e blob_schemas.json." -ForegroundColor Green
