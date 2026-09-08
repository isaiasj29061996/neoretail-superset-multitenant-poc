Set-StrictMode -Version Latest

function Get-NeoRetailContainerId([string]$Service) {
    $containerId = & docker compose ps -a -q $Service 2>$null | Select-Object -First 1
    if ([string]::IsNullOrWhiteSpace($containerId)) {
        return $null
    }
    return $containerId.Trim()
}

function Get-NeoRetailContainerState([string]$Service) {
    $containerId = Get-NeoRetailContainerId $Service
    if (-not $containerId) {
        return [pscustomobject]@{
            Service = $Service
            State = "missing"
            Health = "missing"
            ExitCode = $null
        }
    }

    $state = (& docker inspect --format "{{.State.Status}}" $containerId 2>$null).Trim()
    $health = (& docker inspect --format "{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}" $containerId 2>$null).Trim()
    $exitCode = (& docker inspect --format "{{.State.ExitCode}}" $containerId 2>$null).Trim()

    return [pscustomobject]@{
        Service = $Service
        State = $state
        Health = $health
        ExitCode = $exitCode
    }
}

function Show-NeoRetailLogs([string]$Service, [int]$Tail = 120) {
    Write-Host ""
    Write-Host "Ultimos logs de ${Service}:" -ForegroundColor Yellow
    & docker compose logs --no-color --tail $Tail $Service
}

function Wait-NeoRetailHealthy([string]$Service, [int]$TimeoutSeconds = 300) {
    Write-Host "Aguardando ${Service} ficar healthy..." -ForegroundColor DarkGray
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    while ((Get-Date) -lt $deadline) {
        $status = Get-NeoRetailContainerState $Service
        if ($status.Health -eq "healthy") {
            Write-Host "OK  ${Service}: healthy" -ForegroundColor Green
            return
        }
        if ($status.State -in @("exited", "dead") -or $status.Health -eq "unhealthy") {
            Show-NeoRetailLogs $Service
            throw "${Service} falhou (state=$($status.State), health=$($status.Health), exit=$($status.ExitCode))."
        }
        Start-Sleep -Seconds 2
    }

    Show-NeoRetailLogs $Service
    $status = Get-NeoRetailContainerState $Service
    throw "Timeout aguardando ${Service} (state=$($status.State), health=$($status.Health))."
}

function Wait-NeoRetailOneShot([string]$Service, [int]$TimeoutSeconds = 300) {
    Write-Host "Aguardando ${Service} concluir..." -ForegroundColor DarkGray
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)

    while ((Get-Date) -lt $deadline) {
        $status = Get-NeoRetailContainerState $Service
        if ($status.State -eq "exited") {
            if ([int]$status.ExitCode -eq 0) {
                Write-Host "OK  ${Service}: completed (exit 0)" -ForegroundColor Green
                return
            }
            Show-NeoRetailLogs $Service
            throw "${Service} terminou com exit $($status.ExitCode)."
        }
        if ($status.State -eq "dead") {
            Show-NeoRetailLogs $Service
            throw "${Service} terminou em estado dead."
        }
        Start-Sleep -Seconds 2
    }

    Show-NeoRetailLogs $Service
    $status = Get-NeoRetailContainerState $Service
    throw "Timeout aguardando ${Service} (state=$($status.State))."
}
