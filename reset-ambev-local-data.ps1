param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location $PSScriptRoot

if (-not $Force) {
    throw "Este comando apaga somente o lake/raw-cache local e o PostgreSQL Analytics local. Rode novamente com -Force para confirmar. O Azure e a metadata do Superset nao sao apagados."
}

Write-Host "Parando servicos que usam os dados locais..." -ForegroundColor Yellow
docker compose stop embedded-app superset local-engine analytics-db | Out-Host
if ($LASTEXITCODE -ne 0) { throw "Falha ao parar os servicos." }

$project = "neoretail-v9-multitenant"
$targets = @("local_lake", "analytics_data")
$removed = @()

foreach ($logical in $targets) {
    $volume = docker volume ls `
        --filter "label=com.docker.compose.project=$project" `
        --filter "label=com.docker.compose.volume=$logical" `
        --format "{{.Name}}" | Select-Object -First 1

    if ($volume) {
        Write-Host "Removendo volume local $logical ($volume)..." -ForegroundColor Yellow
        docker volume rm $volume | Out-Host
        if ($LASTEXITCODE -ne 0) { throw "Nao foi possivel remover o volume $volume." }
        $removed += $volume
    } else {
        Write-Host "Volume $logical nao encontrado; seguindo." -ForegroundColor DarkYellow
    }
}

Write-Host "Recriando somente PostgreSQL Analytics e engine local vazios..." -ForegroundColor Cyan
docker compose up -d analytics-db local-engine | Out-Host
if ($LASTEXITCODE -ne 0) { throw "Falha ao recriar analytics-db/local-engine." }

Write-Host "Reset local AMBEV concluido." -ForegroundColor Green
Write-Host "Volumes removidos: $($removed -join ', ')" -ForegroundColor Green
Write-Host "Preservados: Azure Blob, superset_metadata, Redis e arquivos do repositorio." -ForegroundColor Green
Write-Host "Proximo passo: 02A e depois 02B com -SampleFraction 0.35 -PruneRawCache." -ForegroundColor Cyan
