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

# docker compose stop nao solta volumes: containers parados continuam anexados.
# Remove somente os containers que montam os dois volumes que queremos limpar.
# A metadata do Superset (superset-db/superset_metadata) permanece intacta.
Write-Host "Removendo containers que ainda seguram local_lake/analytics_data..." -ForegroundColor Yellow
docker compose rm -f local-engine analytics-db | Out-Host
if ($LASTEXITCODE -ne 0) { throw "Falha ao remover os containers local-engine/analytics-db." }

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

        # Diagnostico util caso algum container inesperado ainda esteja anexado.
        $holders = @(docker ps -a --filter "volume=$volume" --format "{{.ID}} {{.Names}}")
        if ($holders.Count -gt 0) {
            Write-Host "Containers ainda anexados ao volume:" -ForegroundColor DarkYellow
            $holders | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkYellow }
            throw "O volume $volume ainda esta em uso. Remova os containers listados antes de continuar."
        }

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
Write-Host "Observacao: no Windows/WSL2 o espaco pode ser liberado dentro do Docker sem aparecer imediatamente no C:." -ForegroundColor DarkYellow
