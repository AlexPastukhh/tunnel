$ErrorActionPreference = 'Stop'

$TunnelClient = 'C:\Tools\tunnel-client\tunnel-client.exe'
$Profile = 'desktop-commander'

if (-not (Test-Path -LiteralPath $TunnelClient)) {
    Write-Host "tunnel-client not found: $TunnelClient" -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}

$Existing = Get-CimInstance Win32_Process -Filter "Name='tunnel-client.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'run\s+--profile\s+desktop-commander' }

if ($Existing) {
    Write-Host "Desktop Commander Secure Tunnel is already running." -ForegroundColor Green
    Write-Host "PID: $($Existing.ProcessId)"
    Write-Host "UI: http://127.0.0.1:8080/ui"
    Read-Host "Press Enter to close this window"
    exit 0
}

Write-Host "Starting Desktop Commander Secure Tunnel..." -ForegroundColor Cyan
Write-Host "Close this window to stop the tunnel." -ForegroundColor Yellow
Write-Host "Local UI: http://127.0.0.1:8080/ui"
Write-Host ""

& $TunnelClient run --profile $Profile

Write-Host ""
Write-Host "Tunnel stopped." -ForegroundColor Yellow
Read-Host "Press Enter to close"
