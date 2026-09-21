param(
    [string]$Only = ""
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location $PSScriptRoot

# Windows PowerShell 5 otherwise encodes text piped to native commands with
# the active console code page. Force UTF-8 so SQL literals and comments reach
# psql unchanged.
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = $OutputEncoding

$sqlPaths = @(
    Join-Path $PSScriptRoot "analytics-db\views"
    Join-Path $PSScriptRoot "analytics-db\marts"
)
$sqlFiles = @($sqlPaths | ForEach-Object {
    if (Test-Path $_) {
        Get-ChildItem -Path $_ -Filter "*.sql" | Sort-Object Name
    }
})

if (-not [string]::IsNullOrWhiteSpace($Only)) {
    $sqlFiles = @($sqlFiles | Where-Object { $_.Name -like $Only })
}

if ($sqlFiles.Count -eq 0) {
    throw "Nenhuma view ou mart SQL encontrado para o filtro informado."
}

docker compose up -d analytics-db
if ($LASTEXITCODE -ne 0) {
    throw "Nao foi possivel iniciar o PostgreSQL Analytics."
}

$totalWatch = [System.Diagnostics.Stopwatch]::StartNew()
$timings = @()

foreach ($sqlFile in $sqlFiles) {
    Write-Host "Aplicando $($sqlFile.Name)..." -ForegroundColor Cyan
    $watch = [System.Diagnostics.Stopwatch]::StartNew()

    Get-Content -Raw -Encoding UTF8 $sqlFile.FullName |
        docker compose exec -T analytics-db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'

    $watch.Stop()
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao criar o objeto Gold: $($sqlFile.Name)"
    }

    $elapsed = [math]::Round($watch.Elapsed.TotalSeconds, 2)
    $timings += [PSCustomObject]@{
        Arquivo = $sqlFile.Name
        Segundos = $elapsed
    }
    Write-Host "  concluido em $elapsed s" -ForegroundColor DarkGray
}

$totalWatch.Stop()

Write-Host ""
Write-Host "Tempo por arquivo:" -ForegroundColor Yellow
$timings | Sort-Object Segundos -Descending | Format-Table -AutoSize

$totalSeconds = [math]::Round($totalWatch.Elapsed.TotalSeconds, 2)
Write-Host "$($sqlFiles.Count) arquivos de views/marts Gold aplicados em $totalSeconds s." -ForegroundColor Green
