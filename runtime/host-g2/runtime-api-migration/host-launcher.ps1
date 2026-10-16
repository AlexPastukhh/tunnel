$ErrorActionPreference = 'Stop'

$TunnelClient = 'C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe'
$Profile = 'desktop-commander'

if (-not (Test-Path -LiteralPath $TunnelClient)) {
    Write-Host "tunnel-client not found: $TunnelClient" -ForegroundColor Red
    Read-Host "Press Enter to close"
    exit 1
}

if ((Get-FileHash -LiteralPath $TunnelClient -Algorithm SHA256).Hash -ne 'A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A') { throw 'Runtime SHA256 changed' }

$Existing = Get-CimInstance Win32_Process -Filter "Name='tunnel-client.exe' OR Name='tunnel-client-runtime.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'run\s+--profile\s+desktop-commander' }

if ($Existing) {
    Write-Host "Desktop Commander Secure Tunnel is already running." -ForegroundColor Green
    Write-Host "PID: $($Existing.ProcessId)"
    Write-Host "Health: http://127.0.0.1:8080/health"
    Read-Host "Press Enter to close this window"
    exit 0
}

Write-Host "Starting Desktop Commander Secure Tunnel..." -ForegroundColor Cyan
Write-Host "Close this window to stop the tunnel." -ForegroundColor Yellow
Write-Host "Local Health: http://127.0.0.1:8080/health"
Write-Host ""

& $TunnelClient run --profile $Profile '--harpoon.additional-transport='

Write-Host ""
Write-Host "Tunnel stopped." -ForegroundColor Yellow
Read-Host "Press Enter to close"
