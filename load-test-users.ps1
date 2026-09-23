param(
    [int[]]$Users = @(1, 5, 10),
    [string]$Dashboard = "neoretail-v9-visao-geral-industria",
    [int]$RowLimitCap = 20000,
    [int]$MaxWorkers = 12,
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
    $number = [double]::Parse(
        $Matches[1],
        [System.Globalization.CultureInfo]::InvariantCulture
    )
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

    $monitorScript = Join-Path $PSScriptRoot "scripts\monitor-docker-stats.ps1"
    $errorPath = "$OutputPath.errors.log"
    $stdoutPath = "$OutputPath.stdout.log"
    $process = $null
    Remove-Item $errorPath -Force -ErrorAction SilentlyContinue

    try {
        $process = Start-Process `
            -FilePath (Join-Path $PSHOME "powershell.exe") `
            -ArgumentList @(
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-File", ('"{0}"' -f $monitorScript),
                "-ContainerIds", ('"{0}"' -f ($containerIds -join ",")),
                "-OutputPath", ('"{0}"' -f $OutputPath),
                "-StopPath", ('"{0}"' -f $StopPath),
                "-IntervalSeconds", $IntervalSeconds
            ) `
            -RedirectStandardOutput $stdoutPath `
            -RedirectStandardError $errorPath `
            -WindowStyle Hidden `
            -PassThru
        $deadline = (Get-Date).AddSeconds(15)
        while ((Get-Date) -lt $deadline) {
            if ($process.HasExited) { break }
            if ((Test-Path $OutputPath) -and (Get-Item $OutputPath).Length -gt 0) {
                break
            }
            Start-Sleep -Milliseconds 200
        }
        if ($process.HasExited -or -not (Test-Path $OutputPath) -or
            (Get-Item $OutputPath).Length -eq 0) {
            $startupError = if (Test-Path $errorPath) {
                (Get-Content $errorPath -Raw).Trim()
            } else {
                "sem detalhe"
            }
            throw "Monitor nao produziu a primeira amostra: $startupError"
        }
        return [PSCustomObject]@{
            Process = $process
            ErrorPath = $errorPath
            StdoutPath = $stdoutPath
        }
    }
    catch {
        if ($null -ne $process -and -not $process.HasExited) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            $process.WaitForExit()
        }
        Remove-Item $errorPath -Force -ErrorAction SilentlyContinue
        Remove-Item $stdoutPath -Force -ErrorAction SilentlyContinue
        Write-Warning "Monitor de recursos nao iniciou: $($_.Exception.Message)"
        return $null
    }
}

function Stop-StatsMonitor {
    param($Monitor, [string]$StopPath)
    if ($null -eq $Monitor) { return }
    try {
        [System.IO.File]::WriteAllText($StopPath, "stop")
        if (-not $Monitor.Process.WaitForExit(10000)) {
            Stop-Process -Id $Monitor.Process.Id -Force -ErrorAction SilentlyContinue
            $Monitor.Process.WaitForExit()
        }
        if ((Test-Path $Monitor.ErrorPath) -and
            (Get-Item $Monitor.ErrorPath).Length -gt 0) {
            $monitorError = (Get-Content $Monitor.ErrorPath -Raw).Trim()
            Write-Warning "Monitor de recursos registrou erro: $monitorError"
        }
    }
    catch {
        Write-Warning "Falha ao encerrar monitor de recursos: $($_.Exception.Message)"
    }
    finally {
        Remove-Item $StopPath -Force -ErrorAction SilentlyContinue
        Remove-Item $Monitor.ErrorPath -Force -ErrorAction SilentlyContinue
        Remove-Item $Monitor.StdoutPath -Force -ErrorAction SilentlyContinue
    }
}

function Convert-ToInvariantDouble {
    param([string]$Value)
    return [double]::Parse(
        $Value,
        [System.Globalization.CultureInfo]::InvariantCulture
    )
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
            Cpu = Convert-ToInvariantDouble (($parts[2] -replace "%", "").Trim())
            MemoryMiB = Convert-ToMiB $memoryUsed
            MemoryPercent = Convert-ToInvariantDouble (($parts[4] -replace "%", "").Trim())
            Pids = [int](($parts[5]).Trim())
        }
    }

    Write-Host ""
    Write-Host "Picos de CPU/RAM durante o teste:" -ForegroundColor Cyan
    $summary = @()
    foreach ($group in ($samples | Group-Object Name)) {
        $maxCpu = ($group.Group | Measure-Object Cpu -Maximum).Maximum
        $maxMemory = ($group.Group | Measure-Object MemoryMiB -Maximum).Maximum
        $maxMemoryPercent = ($group.Group | Measure-Object MemoryPercent -Maximum).Maximum
        $maxPids = ($group.Group | Measure-Object Pids -Maximum).Maximum
        Write-Host ("  {0}: CPU {1:N2}% | RAM {2:N1} MiB ({3:N2}%) | PIDs {4}" -f $group.Name, $maxCpu, $maxMemory, $maxMemoryPercent, $maxPids)
        $summary += [PSCustomObject]@{
            Name = $group.Name
            Samples = $group.Count
            MaxCpuPercent = [math]::Round($maxCpu, 4)
            MaxMemoryMiB = [math]::Round($maxMemory, 4)
            MaxMemoryPercent = [math]::Round($maxMemoryPercent, 4)
            MaxPids = $maxPids
        }
    }
    return $summary
}

function Find-ResourcePeak {
    param($Summary, [string]$ServicePattern)
    return $Summary | Where-Object { $_.Name -match $ServicePattern } | Select-Object -First 1
}

$suiteRows = @()
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
    $modeSuffix = if ($ForceNoCache) { "-force-no-cache" } else { "" }
    $prefix = "users-$userCount-$safeDashboard$modeSuffix"
    $jsonPathContainer = "/generated/load-tests/$prefix.json"
    $statsPath = Join-Path $generatedDir "$prefix-docker-stats.log"
    $stopPath = Join-Path $generatedDir "$prefix.stop"

    Remove-Item $statsPath -Force -ErrorAction SilentlyContinue
    Remove-Item $stopPath -Force -ErrorAction SilentlyContinue

    $statsMonitor = Start-StatsMonitor -OutputPath $statsPath -StopPath $stopPath -IntervalSeconds $StatsIntervalSeconds

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
        Stop-StatsMonitor -Monitor $statsMonitor -StopPath $stopPath
    }

    $statsSummary = @(Show-StatsSummary -StatsPath $statsPath)
    $resourcesPath = Join-Path $generatedDir "$prefix-resources.json"
    $statsSummary | ConvertTo-Json -Depth 4 | Set-Content -Path $resourcesPath -Encoding UTF8
    $benchmarkPath = Join-Path $generatedDir "$prefix.json"
    $benchmark = Get-Content $benchmarkPath -Raw | ConvertFrom-Json
    $supersetPeak = Find-ResourcePeak $statsSummary '(^|[-_])superset([_-]|$)'
    $databasePeak = Find-ResourcePeak $statsSummary 'analytics-db'
    $redisPeak = Find-ResourcePeak $statsSummary '(^|[-_])redis([_-]|$)'
    $suiteRows += [PSCustomObject]@{
        Users = $userCount
        ChartP50 = [double]$benchmark.chart_latency_seconds.p50
        ChartP95 = [double]$benchmark.chart_latency_seconds.p95
        PageP95 = [double]$benchmark.user_page_completion_seconds.p95
        Throughput = [double]$benchmark.throughput_chart_requests_per_second
        ErrorPercent = [double]$benchmark.error_rate_percent
        CacheHitPercent = [double]$benchmark.cache_hit_rate_percent
        SupersetCpu = if ($supersetPeak) { $supersetPeak.MaxCpuPercent } else { 0 }
        SupersetRamMiB = if ($supersetPeak) { $supersetPeak.MaxMemoryMiB } else { 0 }
        DbCpu = if ($databasePeak) { $databasePeak.MaxCpuPercent } else { 0 }
        DbRamMiB = if ($databasePeak) { $databasePeak.MaxMemoryMiB } else { 0 }
        RedisCpu = if ($redisPeak) { $redisPeak.MaxCpuPercent } else { 0 }
        RedisRamMiB = if ($redisPeak) { $redisPeak.MaxMemoryMiB } else { 0 }
    }
    Write-Host "Resultado: generated/load-tests/$prefix.json" -ForegroundColor DarkGray
    Write-Host "Stats: generated/load-tests/$prefix-docker-stats.log" -ForegroundColor DarkGray
    Write-Host "Recursos: generated/load-tests/$prefix-resources.json" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "Resumo da bateria:" -ForegroundColor Cyan
$baseline = $suiteRows | Where-Object { $_.Users -eq 1 } | Select-Object -First 1
foreach ($row in $suiteRows) {
    $p95Ratio = if ($baseline -and $baseline.ChartP95 -gt 0) {
        [math]::Round($row.ChartP95 / $baseline.ChartP95, 3)
    } else { 0 }
    $ramRatio = if ($baseline -and $baseline.SupersetRamMiB -gt 0) {
        [math]::Round($row.SupersetRamMiB / $baseline.SupersetRamMiB, 3)
    } else { 0 }
    $row | Add-Member -NotePropertyName P95Vs1 -NotePropertyValue $p95Ratio
    $row | Add-Member -NotePropertyName SupersetRamVs1 -NotePropertyValue $ramRatio
}
$suiteRows | Format-Table -AutoSize
$suiteMode = if ($ForceNoCache) { "force-no-cache" } else { "cache-enabled" }
$suitePath = Join-Path $generatedDir "summary-$safeDashboard-$suiteMode.json"
$suiteRows | ConvertTo-Json -Depth 4 | Set-Content -Path $suitePath -Encoding UTF8
Write-Host "Resumo JSON: generated/load-tests/$([System.IO.Path]::GetFileName($suitePath))" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Suite de concorrencia concluida." -ForegroundColor Green
