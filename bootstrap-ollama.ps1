param([switch]$PullModel, [switch]$AsResult, [int]$HealthTimeoutSeconds = 300)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location $PSScriptRoot

$composeFiles = @("-f", "docker-compose.yml", "-f", "docker-compose.assistant.yml")
$resolved = & docker compose @composeFiles config --format json
if ($LASTEXITCODE -ne 0) { throw "Falha ao resolver Compose." }
$model = ($resolved | ConvertFrom-Json).services.'embedded-app'.environment.OLLAMA_MODEL
$engine = & docker compose @composeFiles ps --status running -q local-engine
if ($LASTEXITCODE -ne 0) { throw "Falha ao verificar local-engine." }
if ($engine) {
    $probe = @'
from pathlib import Path
import sys
active = False
for path in Path('/proc').glob('[0-9]*/cmdline'):
    try:
        command = path.read_bytes()
        active = active or any(marker in command for marker in (b'org.apache.spark', b'pyspark.daemon', b'pyspark.worker'))
    except OSError:
        pass
sys.exit(10 if active else 0)
'@
    $probe | & docker compose @composeFiles exec -T local-engine python -
    if ($LASTEXITCODE -eq 10) { throw "SPARK_ACTIVE: aguarde o pipeline terminar antes de iniciar Ollama." }
    if ($LASTEXITCODE -ne 0) { throw "Nao foi possivel verificar Spark; Ollama nao iniciado." }
}

function Test-ModelAvailable {
    $installed = & docker compose @composeFiles exec -T ollama ollama list
    if ($LASTEXITCODE -ne 0) { throw "OLLAMA_UNAVAILABLE: falha ao consultar modelos." }
    return [bool](@($installed | Where-Object { (($_ -split '\s+')[0]) -ceq $model }).Count)
}

try {

& docker compose @composeFiles --profile assistant up -d --wait --wait-timeout $HealthTimeoutSeconds ollama | Out-Host
if ($LASTEXITCODE -ne 0) { throw "OLLAMA_UNAVAILABLE: falha ao iniciar/aguardar health." }

$available = Test-ModelAvailable

if ($available) {
    Write-Host "Modelo $model disponível." -ForegroundColor Green
    if ($AsResult) { return [pscustomobject]@{ available = $true; errorCode = $null; message = "Modelo disponivel" } }
    exit 0
}

if (-not $PullModel) {
    Write-Host "MODEL_NOT_FOUND: modelo $model ainda não foi baixado." -ForegroundColor Yellow
    Write-Host "Execute .\bootstrap-ollama.ps1 -PullModel para autorizar o download." -ForegroundColor Cyan
    if ($AsResult) { return [pscustomobject]@{ available = $false; errorCode = "MODEL_NOT_FOUND"; message = "Modelo ausente; download nao autorizado" } }
    exit 2
}

& docker compose @composeFiles --profile assistant --profile assistant-model run --rm ollama-model-init | Out-Host
if ($LASTEXITCODE -ne 0) { throw "Download do modelo $model falhou." }
if (-not (Test-ModelAvailable)) { throw "MODEL_NOT_FOUND: download terminou sem disponibilizar $model." }
Write-Host "Modelo $model instalado." -ForegroundColor Green
if ($AsResult) { return [pscustomobject]@{ available = $true; errorCode = $null; message = "Modelo instalado" } }
} catch {
    if (-not $AsResult) { throw }
    $code = if ($_.Exception.Message -like 'MODEL_NOT_FOUND:*') { "MODEL_NOT_FOUND" } else { "OLLAMA_UNAVAILABLE" }
    return [pscustomobject]@{ available = $false; errorCode = $code; message = $_.Exception.Message }
}
