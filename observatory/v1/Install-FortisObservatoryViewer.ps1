# Manual, never scheduled. Execute only after independent source/code review.
# Installs a viewer with scoped chat registration, not a Windows service.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_.-]{2,119}$')][string]$Container,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedViewerSha256,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedBridgeSha256,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedDispatchSha256,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedEnrollmentSha256,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedAutoCmdSha256,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedAutoEnableSha256
)
$ErrorActionPreference = 'Stop'
$source = Split-Path -Parent $MyInvocation.MyCommand.Path
$owner = [Security.Principal.WindowsIdentity]::GetCurrent()
$username = ($owner.Name -split '\\')[-1]
if ($username -ine 'alexa') {
    throw 'Manual owner installation permitted only from the intended alexa Windows account.'
}
$install = Join-Path $env:LOCALAPPDATA 'FortisObservatoryV1\Viewer'
if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) { throw 'LOCALAPPDATA missing' }
if (-not (Test-Path -LiteralPath $source -PathType Container)) { throw 'Missing source directory' }
$files = @('owner_viewer.py', 'owner_notifier_bridge.py', 'owner_dispatch.py',
    'owner_enrollment.py', 'Start-FortisObservatory.cmd', 'Start-FortisObservatoryAuto.cmd',
    'Enable-FortisObservatoryAutoStart.ps1')
if (Test-Path -LiteralPath $install -PathType Container) {
    foreach ($name in @('approved-owner.json') + $files) {
        $candidate = Join-Path $install $name
        if (Test-Path -LiteralPath $candidate) {
            $existingFile = Get-Item -LiteralPath $candidate -Force
            if (($existingFile.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw 'Existing installation contains a reparse point.'
            }
        }
    }
}
foreach ($file in $files) {
    $path = Join-Path $source $file
    $item = Get-Item -LiteralPath $path -Force
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw 'Refusing reparse source.'
    }
}
$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $source 'owner_viewer.py')).Hash
if ($hash -ine $ExpectedViewerSha256) {
    throw 'Viewer source has changed since independent reviewed SHA-256. Installation refused.'
}
$bridgeHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $source 'owner_notifier_bridge.py')).Hash
if ($bridgeHash -ine $ExpectedBridgeSha256) {
    throw 'Browser bridge source hash mismatch. Installation refused.'
}
$dispatchHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $source 'owner_dispatch.py')).Hash
if ($dispatchHash -ine $ExpectedDispatchSha256) {
    throw 'Scoped dispatch source hash mismatch. Installation refused.'
}
$enrollmentHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $source 'owner_enrollment.py')).Hash
if ($enrollmentHash -ine $ExpectedEnrollmentSha256) {
    throw 'Enrollment source hash mismatch. Installation refused.'
}
$autoCmdHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $source 'Start-FortisObservatoryAuto.cmd')).Hash
if ($autoCmdHash -ine $ExpectedAutoCmdSha256) {
    throw 'Autostart wrapper source hash mismatch. Installation refused.'
}
$autoEnableHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $source 'Enable-FortisObservatoryAutoStart.ps1')).Hash
if ($autoEnableHash -ine $ExpectedAutoEnableSha256) {
    throw 'Autostart controls source hash mismatch. Installation refused.'
}
if (-not (Get-Command docker.exe -ErrorAction SilentlyContinue)) {
    throw 'Docker CLI not available for this Windows account.'
}
# Verify exact running container identity BEFORE changing owner files.
$containerID = & docker.exe inspect --type container --format '{{.Id}}' $Container 2>$null
if ($LASTEXITCODE -ne 0 -or -not (($containerID | Out-String).Trim() -match '^[a-f0-9]{64}$')) {
    throw 'The selected existing Docker container is not accessible to this owner session.'
}
# No nested python -c quoting: PowerShell 5.1 mangles it before docker exec.
& docker.exe exec $Container test -d /workspace/repo/fortis-observatory-repo-v1
if ($LASTEXITCODE -ne 0) {
    throw 'The selected container does not expose the existing approved Repo volume.'
}
& docker.exe exec $Container test -f /workspace/repos/tunnel/observatory/v1/repo_viewer_export.py
if ($LASTEXITCODE -ne 0) {
    throw 'The selected container is missing the read-only Repo viewer export.'
}
# Install to owner profile only. Do NOT alter Docker networks or G2 access.
if (Test-Path -LiteralPath $install) {
    $existing = Get-Item -LiteralPath $install -Force
    if (($existing.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw 'Protected target is a reparse point.'
    }
} else {
    New-Item -ItemType Directory -Path $install -Force | Out-Null
}
# Remove inheritance and bind to current owner SID, not to Windows Users/Guests.
$sid = $owner.User.Value
# icacls requires a leading * to interpret the identity as an SID.
$ownerAce = '*' + $sid + ':(OI)(CI)F'
& icacls.exe $install /inheritance:r /grant:r $ownerAce | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Could not set owner-only directory ACL.' }
$acl = Get-Acl -LiteralPath $install
if ($acl.AreAccessRulesProtected -ne $true) { throw 'Owner ACL inheritance remains enabled.' }
foreach ($rule in @($acl.Access)) {
    if ($rule.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow) {
        try {
            $resolvedSid = $rule.IdentityReference.Translate(
                [Security.Principal.SecurityIdentifier]).Value
        } catch {
            throw 'Unresolvable allowed identity in target ACL.'
        }
        if ($resolvedSid -ne $sid -and $resolvedSid -ne 'S-1-5-18') {
            throw 'Unexpected allowed identity in target ACL. Refusing deployment.'
        }
    }
}
foreach ($file in $files) {
    Copy-Item -LiteralPath (Join-Path $source $file) -Destination (Join-Path $install $file) -Force
}
$config = @{ owner_sid = $sid; container = $Container }
$json = ConvertTo-Json -InputObject $config -Compress
[IO.File]::WriteAllText((Join-Path $install 'approved-owner.json'), $json, (New-Object System.Text.UTF8Encoding($false)))
$copied = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $install 'owner_viewer.py')).Hash
if ($copied -ine $ExpectedViewerSha256) { throw 'Installed hash mismatch.' }
$copiedBridge = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $install 'owner_notifier_bridge.py')).Hash
if ($copiedBridge -ine $ExpectedBridgeSha256) { throw 'Installed bridge hash mismatch.' }
$copiedDispatch = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $install 'owner_dispatch.py')).Hash
if ($copiedDispatch -ine $ExpectedDispatchSha256) { throw 'Installed dispatch hash mismatch.' }
$copiedEnrollment = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $install 'owner_enrollment.py')).Hash
if ($copiedEnrollment -ine $ExpectedEnrollmentSha256) {
    throw 'Installed enrollment hash mismatch.'
}
$copiedAutoCmd = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $install 'Start-FortisObservatoryAuto.cmd')).Hash
if ($copiedAutoCmd -ine $ExpectedAutoCmdSha256) {
    throw 'Installed autostart wrapper hash mismatch.'
}
$copiedAutoEnable = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $install 'Enable-FortisObservatoryAutoStart.ps1')).Hash
if ($copiedAutoEnable -ine $ExpectedAutoEnableSha256) {
    throw 'Installed autostart control hash mismatch.'
}
$readback = Get-Content -LiteralPath (Join-Path $install 'approved-owner.json') -Raw | ConvertFrom-Json
if ($readback.owner_sid -ne $sid -or $readback.container -ne $Container) {
    throw 'Owner config failed readback.'
}
Write-Output 'INSTALL_SOURCE_VERIFIED=True'
Write-Output 'INSTALL_OWNER_ACL_CHECKED=True'
Write-Output 'INSTALL_DOCKER_VOLUME_FOUND=True'
Write-Output 'MANUAL_START_READY=True'
Write-Output ('Double-click the owner-protected Start-FortisObservatory.cmd inside: ' + $install)
Write-Output 'No Windows listener was started and no Docker network was modified.'
