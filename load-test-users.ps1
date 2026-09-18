param(
    [int[]]$Users = @(1, 5, 10),
    [string]$Dashboard = "neoretail-v9-visao-geral-industria",
    [int]$RowLimitCap = 20000,
    [int]$MaxWorkers = 40,
    [int]$Iterations = 1,
    [switch]$ColdCache,
    [switch]$ForceNoCache,
    [int]$StatsIntervalSeconds = 1
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
Set-Location $PSScriptRoot

if ($Users.Count -eq 0 -or ($Users | Where-Object { $_ -lt 1 })) {
    throw "Users deve conter apenas valores maiores que zero."
}
if ($RowLimitCap -lt 1) { throw "RowLimitCap precisa ser maior que zero." }
if ($MaxWorkers -lt 1) { throw "MaxWorkers precisa ser maior que zero." }
if ($Iterations -lt 1) { throw "Iterations precisa ser maior que zero." }
if ($StatsIntervalSeconds -lt 1) { throw "StatsIntervalSeconds precisa ser maior que zero." }

$generatedDir = Join-Path $PSScriptRoot "generated\load-tests"
New-Item -ItemType Directory -Force -Path $generatedDir | Out-Null

docker compose up -d analytics-db redis superset
if ($LASTEXITCODE -ne 0) {
    throw "Nao foi possivel iniciar a stack necessaria para o teste de concorrencia."
}

function Convert-ToMiB {
    param([string]$Value)
    if ($Value -notmatch '^\s*([0-9.]+)\s*([KMGT]iB)\s*$') { return 0.0 }
    $number = [double]$Matches[1]
    switch ($Matches[2]) {
        "KiB" { return $number / 1024.0 }
        "MiB" { return $number }
        "GiB" { return $number * 1024.0 }
        "TiB" { return $number * 1024.0 * 1024.0 }
    }
    return 0.0
}

function Start-StatsMonitor {
    param(
        [string]$OutputPath,
        [string]$StopPath,
        [int]$IntervalSeconds
    )

    $containerIds = @(
        (docker compose ps -q superset),
        (docker compose ps -q analytics-db),
        (docker compose ps -q redis)
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

    if ($containerIds.Count -eq 0) {
        return $null
    }

    $joinedIds = $containerIds -join ","
    return Start-Job -ArgumentList $joinedIds, $OutputPath, $StopPath, $IntervalSeconds -ScriptBlock {
        param($JoinedIds, $OutputPath, $StopPath, $IntervalSeconds)
        $ids = $JoinedIds -split ","
        while (-not (Test-Path $StopPath)) {
            $timestamp = (Get-Date).ToString("o")
            $lines = & docker stats --no-stream --format "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.MemPerc}}|{{.PIDs}}" @ids
            foreach ($line in $lines) {
                Add-Content -Path $OutputPath -Value "$timestamp|$line"
            }
            Start-Sleep -Seconds $IntervalSeconds
        }
    }
}

function Stop-StatsMonitor {
    param($Job, [string]$StopPath)
    if ($null -eq $Job) { return }
    New-Item -ItemType File -Force -Path $StopPath | Out-Null
    Wait-Job $Job | Out-Null
    Receive-Job $Job | Out-Null
    Remove-Job $Job
    Remove-Item $StopPath -Force -ErrorAction SilentlyContinue
}

function Show-StatsSummary {
    param([string]$StatsPath)
    if (-not (Test-Path $StatsPath)) {
        Write-Host "Sem amostras de docker stats." -ForegroundColor DarkYellow
        return
    }

    $samples = foreach ($line in Get-Content $StatsPath) {
        $parts = $line -split "\|", 6
        if ($parts.Count -lt 6) { continue }
        $memoryUsed = (($parts[3] -split " / ")[0]).Trim()
        [PSCustomObject]@{
            Timestamp = $parts[0]
            Name = $parts[1]
            Cpu = [double](($parts[2] -replace "%", "").Trim())
            MemoryMiB = Convert-ToMiB $memoryUsed
            MemoryPercent = [double](($parts[4] -replace "%", "").Trim())
            Pids = [int](($parts[5]).Trim())
        }
    }

    Write-Host ""
    Write-Host "Picos de CPU/RAM durante o teste:" -ForegroundColor Cyan
    foreach ($group in ($samples | Group-Object Name)) {
        $maxCpu = ($group.Group | Measure-Object Cpu -Maximum).Maximum
        $maxMemory = ($group.Group | Measure-Object MemoryMiB -Maximum).Maximum
        $maxMemoryPercent = ($group.Group | Measure-Object MemoryPercent -Maximum).Maximum
        $maxPids = ($group.Group | Measure-Object Pids -Maximum).Maximum
        Write-Host ("  {0}: CPU {1:N2}% | RAM {2:N1} MiB ({3:N2}%) | PIDs {4}" -f $group.Name, $maxCpu, $maxMemory, $maxMemoryPercent, $maxPids)
    }
}

foreach ($userCount in $Users) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor DarkGray
    Write-Host "Teste com $userCount usuario(s) simultaneo(s)" -ForegroundColor Green
    Write-Host "Dashboard: $Dashboard" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor DarkGray

    if ($ColdCache) {
        Write-Host "Limpando caches Redis DB 1-4..." -ForegroundColor Yellow
        foreach ($dbIndex in 1..4) {
            docker compose exec -T redis redis-cli -n $dbIndex FLUSHDB | Out-Null
            if ($LASTEXITCODE -ne 0) {
                throw "Falha ao limpar Redis DB $dbIndex."
            }
        }
    }

    $safeDashboard = ($Dashboard -replace '[^A-Za-z0-9_.-]', '_')
    $prefix = "users-$userCount-$safeDashboard"
    $jsonPathContainer = "/generated/load-tests/$prefix.json"
    $statsPath = Join-Path $generatedDir "$prefix-docker-stats.log"
    $stopPath = Join-Path $generatedDir "$prefix.stop"

    Remove-Item $statsPath -Force -ErrorAction SilentlyContinue
    Remove-Item $stopPath -Force -ErrorAction SilentlyContinue

    $statsJob = Start-StatsMonitor -OutputPath $statsPath -StopPath $stopPath -IntervalSeconds $StatsIntervalSeconds

    $arguments = @(
        "compose", "exec", "-T",
        "-e", "LOAD_TEST_USERS=$userCount",
        "-e", "LOAD_TEST_DASHBOARD_SLUGS=$Dashboard",
        "-e", "LOAD_TEST_ROW_LIMIT_CAP=$RowLimitCap",
        "-e", "LOAD_TEST_MAX_WORKERS=$MaxWorkers",
        "-e", "LOAD_TEST_ITERATIONS=$Iterations",
        "-e", "LOAD_TEST_FORCE=$($ForceNoCache.IsPresent.ToString().ToLowerInvariant())",
        "-e", "LOAD_TEST_OUTPUT=$jsonPathContainer",
        "superset",
        "/app/.venv/bin/python",
        "/app/pythonpath/concurrent_dashboard_benchmark.py"
    )

    try {
        & docker @arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Benchmark falhou para $userCount usuario(s)."
        }
    }
    finally {
        Stop-StatsMonitor -Job $statsJob -StopPath $stopPath
    }

    Show-StatsSummary -StatsPath $statsPath
    Write-Host "Resultado: generated/load-tests/$prefix.json" -ForegroundColor DarkGray
    Write-Host "Stats: generated/load-tests/$prefix-docker-stats.log" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "Suite de concorrencia concluida." -ForegroundColor Green
