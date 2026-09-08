$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

docker compose exec -T local-engine python -m neoretail_local.smoke
if ($LASTEXITCODE -ne 0) { throw "PySpark local ou PostgreSQL Analytics falhou no smoke test." }

docker compose exec -T analytics-db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1 AS ok;"'
if ($LASTEXITCODE -ne 0) { throw "PostgreSQL Analytics nao respondeu ao SELECT 1." }

Write-Host "Fluxo local validado: PySpark -> PostgreSQL Analytics -> Superset." -ForegroundColor Green
