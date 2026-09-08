$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location $PSScriptRoot

$viewsPath = Join-Path $PSScriptRoot "analytics-db\views"
$sqlFiles = @(Get-ChildItem -Path $viewsPath -Filter "*.sql" | Sort-Object Name)
if ($sqlFiles.Count -eq 0) {
    throw "Nenhuma view SQL encontrada em: $viewsPath"
}

docker compose up -d analytics-db
if ($LASTEXITCODE -ne 0) {
    throw "Nao foi possivel iniciar o PostgreSQL Analytics."
}

foreach ($sqlFile in $sqlFiles) {
    Get-Content -Raw $sqlFile.FullName |
        docker compose exec -T analytics-db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao criar a view: $($sqlFile.Name)"
    }
}

Write-Host "$($sqlFiles.Count) views Gold criadas com sucesso." -ForegroundColor Green
