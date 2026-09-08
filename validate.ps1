$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

python .\scripts\validate_project.py
if ($LASTEXITCODE -ne 0) { throw "Validacao Python/YAML falhou." }
node --check .\embedded-app\server.js
node --check .\embedded-app\src\app.js
if ($LASTEXITCODE -ne 0) { throw "Validacao Node falhou." }

if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker compose config --quiet
    if ($LASTEXITCODE -ne 0) { throw "Docker Compose invalido." }
    docker compose build local-engine embedded-app superset
    if ($LASTEXITCODE -ne 0) { throw "Build dos containers principais falhou." }
} else {
    Write-Host "Docker ausente: build dos containers nao executado." -ForegroundColor Yellow
}
Write-Host "V9 Multi-tenant validada." -ForegroundColor Green
