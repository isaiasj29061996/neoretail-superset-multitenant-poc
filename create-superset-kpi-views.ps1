$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location $PSScriptRoot

$sqlPaths = @(
    Join-Path $PSScriptRoot "analytics-db\views"
    Join-Path $PSScriptRoot "analytics-db\marts"
)
$sqlFiles = @($sqlPaths | ForEach-Object {
    if (Test-Path $_) {
        Get-ChildItem -Path $_ -Filter "*.sql" | Sort-Object Name
    }
})
if ($sqlFiles.Count -eq 0) {
    throw "Nenhuma view ou mart SQL encontrado."
}

docker compose up -d analytics-db
if ($LASTEXITCODE -ne 0) {
    throw "Nao foi possivel iniciar o PostgreSQL Analytics."
}

foreach ($sqlFile in $sqlFiles) {
    Get-Content -Raw $sqlFile.FullName |
        docker compose exec -T analytics-db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao criar o objeto Gold: $($sqlFile.Name)"
    }
}

Write-Host "$($sqlFiles.Count) arquivos de views/marts Gold aplicados com sucesso." -ForegroundColor Green
