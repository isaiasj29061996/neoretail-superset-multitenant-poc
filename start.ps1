param(
    [switch]$Rebuild,
    [switch]$Assistant,
    [switch]$PullModel,
    [int]$HealthTimeoutSeconds = 300
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location $PSScriptRoot
. "$PSScriptRoot\scripts\container-health.ps1"
$composeArguments = @("compose", "-f", "docker-compose.yml")
if ($Assistant) { $composeArguments += @("-f", "docker-compose.assistant.yml") }
$previousAssistantEnabled = $env:ASSISTANT_ENABLED
$assistantProvider = $null
$assistantModel = $null

function Write-Step([int]$Number, [string]$Text) {
    Write-Host ""
    Write-Host "[$Number/7] $Text" -ForegroundColor Cyan
}

function Invoke-Docker([string]$Step, [string[]]$Arguments) {
    & docker @composeArguments @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Step falhou (codigo $LASTEXITCODE)." }
}

try {
    if ($PullModel -and -not $Assistant) { throw "-PullModel exige -Assistant. Nenhum download foi iniciado." }
    Write-Step 1 "Pre-flight e configuracao local"
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker nao foi encontrado. Abra o Docker Desktop e tente novamente."
    }
    & docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Desktop nao esta pronto. Aguarde o engine iniciar."
    }
    if (-not (Test-Path ".env")) {
        Copy-Item ".env.example" ".env"
        Write-Host "Criado .env. O start local funciona sem Blob; o pipeline exige a connection string." -ForegroundColor Yellow
    }
    New-Item -ItemType Directory -Force -Path ".\generated", ".\certs" | Out-Null
    if ($Assistant) {
        Write-Host "-Assistant: ASSISTANT_ENABLED=true apenas nesta execucao; .env preservado." -ForegroundColor Cyan
        $env:ASSISTANT_ENABLED = "true"
        $resolved = & docker @composeArguments config --format json
        if ($LASTEXITCODE -ne 0) { throw "Nao foi possivel resolver a configuracao do Assistente." }
        $assistantEnvironment = ($resolved | ConvertFrom-Json).services.'embedded-app'.environment
        $assistantProvider = $assistantEnvironment.LLM_PROVIDER.ToLowerInvariant()
        $assistantModel = $assistantEnvironment.OLLAMA_MODEL
        if ($assistantProvider -notin @("mock", "ollama")) { throw "LLM_PROVIDER deve ser mock ou ollama." }
        if ($PullModel -and $assistantProvider -ne "ollama") { throw "-PullModel exige LLM_PROVIDER=ollama." }
        Write-Host "Assistente: provider=$assistantProvider, modelo=$assistantModel" -ForegroundColor Cyan
    }

    Write-Step 2 "Validacao do Compose e build"
    Invoke-Docker "Validacao do Compose" @("config", "--quiet")
    if ($Rebuild) {
        Invoke-Docker "Build das imagens" @(
            "build", "superset-init", "superset", "local-engine", "embedded-app"
        )
    } else {
        Write-Host "Use -Rebuild quando precisar reconstruir as imagens." -ForegroundColor DarkGray
    }

    Write-Step 3 "Infraestrutura: Metadata, Analytics e Redis"
    Invoke-Docker "Inicializacao dos bancos" @(
        "up", "-d", "superset-db", "analytics-db", "redis"
    )
    Wait-NeoRetailHealthy "superset-db" $HealthTimeoutSeconds
    Wait-NeoRetailHealthy "analytics-db" $HealthTimeoutSeconds
    Wait-NeoRetailHealthy "redis" $HealthTimeoutSeconds

    Write-Step 4 "Bootstrap do Superset e conexao Analytics"
    Invoke-Docker "Inicializacao do superset-init" @(
        "up", "-d", "--no-deps", "superset-init"
    )
    Wait-NeoRetailOneShot "superset-init" $HealthTimeoutSeconds

    Write-Step 5 "Superset e PySpark local"
    Invoke-Docker "Inicializacao dos servicos analiticos" @(
        "up", "-d", "--no-deps", "superset", "local-engine"
    )
    Wait-NeoRetailHealthy "superset" $HealthTimeoutSeconds
    Wait-NeoRetailHealthy "local-engine" $HealthTimeoutSeconds
    if ($Assistant -and $assistantProvider -eq "ollama") {
        $ollamaResult = & "$PSScriptRoot\bootstrap-ollama.ps1" -PullModel:$PullModel -AsResult -HealthTimeoutSeconds $HealthTimeoutSeconds
        if (-not $ollamaResult.available) { Write-Warning "Assistente degraded: $($ollamaResult.errorCode). $($ollamaResult.message)" }
    }

    Write-Step 6 "Portal NeoRetail Embedded"
    Invoke-Docker "Inicializacao do Embedded" @(
        "up", "-d", "--no-deps", "embedded-app"
    )
    Wait-NeoRetailHealthy "embedded-app" $HealthTimeoutSeconds

    Write-Step 7 "Health check final"
    & "$PSScriptRoot\health.ps1" -TimeoutSeconds 30
    if ($LASTEXITCODE -ne 0) { throw "Health check final falhou." }
    if ($Assistant) {
        # Read JSON even when the endpoint correctly returns HTTP 503.
        $healthJson = & docker @composeArguments exec -T embedded-app node -e "fetch('http://localhost:3000/api/assistant/health').then(async r=>console.log(JSON.stringify(await r.json()))).catch(()=>process.exit(1))"
        if ($LASTEXITCODE -ne 0) { throw "Nao foi possivel consultar /api/assistant/health." }
        $assistantHealth = $healthJson | ConvertFrom-Json
        if (-not $assistantHealth.enabled -or $assistantHealth.provider -ne $assistantProvider) { throw "Embedded nao recebeu a configuracao do Assistente." }
        if ($assistantProvider -eq "ollama" -and $assistantHealth.model -ne $assistantModel) { throw "Modelo do Assistente diverge do Compose." }
        if ($assistantHealth.status -eq "ok" -and $assistantHealth.available) {
            Write-Host "Assistente: ok ($($assistantHealth.provider), $($assistantHealth.model))." -ForegroundColor Green
        } elseif ($assistantHealth.errorCode -in @("MODEL_NOT_FOUND", "OLLAMA_UNAVAILABLE")) {
            Write-Warning "Assistente degraded: $($assistantHealth.errorCode)."
        } else { throw "Health do Assistente retornou um estado inesperado." }
        & docker stats --no-stream
        & docker system df
    }

    Write-Host ""
    Write-Host "V9 Multi-tenant iniciada e saudavel." -ForegroundColor Green
    Write-Host "NeoRetail Embedded:   http://localhost:3000" -ForegroundColor Green
    Write-Host "Superset Admin:       http://localhost:8088" -ForegroundColor Green
    Write-Host "PySpark/Jupyter:      http://localhost:8888" -ForegroundColor Green
    Write-Host "PostgreSQL Analytics: localhost:5433" -ForegroundColor Green
    Write-Host "Refresh dos clientes: .\run-multitenant-refresh.ps1" -ForegroundColor Cyan
} catch {
    Write-Host ""
    Write-Host "A inicializacao da V9 falhou: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Estado atual dos containers:" -ForegroundColor Yellow
    & docker @composeArguments ps -a
    exit 1
} finally {
    $env:ASSISTANT_ENABLED = $previousAssistantEnabled
}
