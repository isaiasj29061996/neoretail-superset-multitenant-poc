param(
    [string]$HostName = "azreu2platdw.blob.core.windows.net"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force -Path ".\certs" | Out-Null

Write-Host "Lendo a cadeia TLS que o Windows usa para $HostName ..." -ForegroundColor Cyan
$tcp = New-Object System.Net.Sockets.TcpClient
try {
    $tcp.Connect($HostName, 443)
    $ssl = New-Object System.Net.Security.SslStream($tcp.GetStream(), $false, ({ $true }))
    try {
        $ssl.AuthenticateAsClient($HostName)
        $leaf = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($ssl.RemoteCertificate)
        $chain = New-Object System.Security.Cryptography.X509Certificates.X509Chain
        $chain.ChainPolicy.RevocationMode = [System.Security.Cryptography.X509Certificates.X509RevocationMode]::NoCheck
        [void]$chain.Build($leaf)
        if ($chain.ChainElements.Count -lt 1) { throw "Nao foi possivel montar a cadeia de certificados." }
        $root = $chain.ChainElements[$chain.ChainElements.Count - 1].Certificate
        $der = $root.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert)
        $b64 = [Convert]::ToBase64String($der, [Base64FormattingOptions]::InsertLineBreaks)
        $pem = "-----BEGIN CERTIFICATE-----`r`n$b64`r`n-----END CERTIFICATE-----`r`n"
        Set-Content -Path ".\certs\company-root-ca.crt" -Value $pem -Encoding ascii
        Write-Host "CA exportada para .\certs\company-root-ca.crt" -ForegroundColor Green
        Write-Host "Subject: $($root.Subject)" -ForegroundColor DarkGray
        Write-Host "Issuer:  $($root.Issuer)" -ForegroundColor DarkGray
        Write-Host "Agora rode .\discover-blob.ps1 -Rebuild" -ForegroundColor Green
    } finally {
        if ($ssl) { $ssl.Dispose() }
    }
} finally {
    $tcp.Dispose()
}
