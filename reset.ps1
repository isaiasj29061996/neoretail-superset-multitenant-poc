param([switch]$Confirm)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not $Confirm) { throw "Este comando remove Metadata, Analytics, Redis e lake local. Execute .\reset.ps1 -Confirm se for intencional." }
docker compose --profile blob down --volumes --remove-orphans
Write-Host "Volumes da V9 removidos, incluindo Metadata, Analytics e lake local. Codigo, .env e generated foram preservados." -ForegroundColor Yellow
