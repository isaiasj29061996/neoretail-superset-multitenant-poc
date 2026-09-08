$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

docker compose ps -a
Write-Host ""
& "$PSScriptRoot\health.ps1" -TimeoutSeconds 15
