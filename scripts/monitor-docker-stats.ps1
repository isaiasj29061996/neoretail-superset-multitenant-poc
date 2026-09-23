param(
    [Parameter(Mandatory = $true)]
    [string]$ContainerIds,
    [Parameter(Mandatory = $true)]
    [string]$OutputPath,
    [Parameter(Mandatory = $true)]
    [string]$StopPath,
    [int]$IntervalSeconds = 1
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ids = @($ContainerIds -split "," | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
if ($ids.Count -eq 0) {
    exit 0
}

$utf8WithoutBom = New-Object System.Text.UTF8Encoding($false)
$writer = New-Object System.IO.StreamWriter($OutputPath, $false, $utf8WithoutBom)

try {
    while (-not (Test-Path -LiteralPath $StopPath)) {
        $timestamp = (Get-Date).ToUniversalTime().ToString("o")
        $lines = @(
            & docker stats --no-stream `
                --format "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.MemPerc}}|{{.PIDs}}" `
                @ids
        )
        if ($LASTEXITCODE -ne 0) {
            throw "docker stats terminou com codigo $LASTEXITCODE."
        }
        foreach ($line in $lines) {
            $writer.WriteLine("$timestamp|$line")
        }
        $writer.Flush()

        for ($step = 0; $step -lt ($IntervalSeconds * 10); $step++) {
            if (Test-Path -LiteralPath $StopPath) { break }
            Start-Sleep -Milliseconds 100
        }
    }
}
finally {
    $writer.Flush()
    $writer.Dispose()
}
