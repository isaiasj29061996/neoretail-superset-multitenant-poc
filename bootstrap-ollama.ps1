param([switch]$PullModel)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location $PSScriptRoot

$model = if ($env:OLLAMA_MODEL) { $env:OLLAMA_MODEL } else { "llama3.1:8b" }

& docker compose --profile assistant up -d ollama
if ($LASTEXITCODE -ne 0) { throw "Não foi possível iniciar o Ollama." }

$available = & docker compose exec -T ollama ollama list
if ($LASTEXITCODE -ne 0) { throw "Não foi possível consultar os modelos do Ollama." }

if ($available -match [regex]::Escape($model)) {
    Write-Host "Modelo $model disponível." -ForegroundColor Green
    exit 0
}

if (-not $PullModel) {
    Write-Host "Modelo $model ainda não foi baixado." -ForegroundColor Yellow
    Write-Host "Execute .\bootstrap-ollama.ps1 -PullModel para autorizar o download." -ForegroundColor Cyan
    exit 2
}

& docker compose --profile assistant --profile assistant-model run --rm ollama-model-init
if ($LASTEXITCODE -ne 0) { throw "Download do modelo $model falhou." }
Write-Host "Modelo $model instalado." -ForegroundColor Green
