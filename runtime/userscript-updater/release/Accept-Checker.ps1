param(
    [Parameter(Mandatory=$true)][string]$NativeReport,
    [Parameter(Mandatory=$true)][string]$RouteInventory,
    [Parameter(Mandatory=$true)][string]$GuiReport
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Push-Location $PSScriptRoot
try {
    & (Join-Path $PSScriptRoot 'python\python.exe') -I -S -B -X utf8 (Join-Path $PSScriptRoot 'qa\accept_install.py') --native-report $NativeReport --routes $RouteInventory --gui-report $GuiReport
    if ($LASTEXITCODE -ne 0) { throw 'Acceptance failed. Update remains unavailable.' }
} finally { Pop-Location }
