# Scoped owner-only Viewer source update. Preview by default. No Docker/tunnel changes.
[CmdletBinding()]
param(
    [ValidateSet('Preview','Install','Rollback')][string]$Action='Preview',
    [string]$BackupFile
)
$ErrorActionPreference = 'Stop'
$PinnedNewSha = 'a3eb75f113a6152adbb3381d6a9b6cd845dec4e927c7b20c80885968e635b48d'
$source = Join-Path $PSScriptRoot 'owner_viewer.py'
$targetDir = Join-Path $env:LOCALAPPDATA 'FortisObservatoryV1\Viewer'
$target = Join-Path $targetDir 'owner_viewer.py'
$config = Join-Path $targetDir 'approved-owner.json'
$who = [Security.Principal.WindowsIdentity]::GetCurrent()
if (($who.Name -split '\\')[-1] -ine 'alexa') {
    throw 'Run only as the Windows alexa account (not guest G2 or Administrator).'
}
if (-not (Test-Path -LiteralPath $config -PathType Leaf) -or
    -not (Test-Path -LiteralPath $target -PathType Leaf)) {
    throw 'Existing approved owner installation is required.'
}
$approved = Get-Content -LiteralPath $config -Raw -Encoding UTF8 | ConvertFrom-Json
if ($approved.owner_sid -cne $who.User.Value) {
    throw 'Approved Windows owner SID mismatch.'
}
function Test-PrivateOwnerPath([string]$Path, [bool]$Protected) {
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Reparse point not accepted: $Path"
    }
    $acl = Get-Acl -LiteralPath $Path
    if ($Protected -and -not $acl.AreAccessRulesProtected) {
        throw "Inherited directory ACL: $Path"
    }
    foreach ($rule in @($acl.Access)) {
        if ($rule.AccessControlType -ne 'Allow') { continue }
        $sid = $rule.IdentityReference.Translate(
            [Security.Principal.SecurityIdentifier]).Value
        if ($sid -ne $who.User.Value -and $sid -ne 'S-1-5-18') {
            throw "Foreign allowed SID in ACL: $Path"
        }
    }
}
Test-PrivateOwnerPath $targetDir $true
Test-PrivateOwnerPath $target $false
Test-PrivateOwnerPath $config $false
$sourceItem = Get-Item -LiteralPath $source -Force -ErrorAction Stop
if (($sourceItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'Refusing reparse source file.'
}
$sourceSha = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
if ($sourceSha -ne $PinnedNewSha) { throw 'Source hash differs from reviewed candidate. Stop.' }
$installedSha = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Output ('SourceSHA='+$sourceSha)
Write-Output ('InstalledSHA='+$installedSha)
if ($Action -eq 'Preview') {
    Write-Output 'PREVIEW_ONLY=True; no changed files, tunnels or services.'
    return
}
function Assert-ViewerStopped {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $ar = $client.BeginConnect('127.0.0.1',18755,$null,$null)
        if ($ar.AsyncWaitHandle.WaitOne(350)) {
            try {
                $client.EndConnect($ar)
                throw 'Viewer port 18755 is occupied: stop only Viewer first.'
            } catch [System.Net.Sockets.SocketException] {}
        }
    } finally {
        $client.Dispose()
    }
}
Assert-ViewerStopped
if ($Action -eq 'Install') {
    if ($BackupFile) { throw '-BackupFile is only for Rollback.' }
    if ($installedSha -eq $sourceSha) {
        Write-Output 'ALREADY_INSTALLED=True'
        return
    }
    $backup = Join-Path $targetDir ('owner_viewer.py.before-owner-auto-'+
        (Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+
        [Guid]::NewGuid().ToString('N')+'.bak')
    Copy-Item -LiteralPath $target -Destination $backup -ErrorAction Stop
    Test-PrivateOwnerPath $backup $false
    if ((Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash.ToLowerInvariant() -ne $installedSha) {
        throw 'Backup mismatch, refusing installation.'
    }
    try {
        Copy-Item -LiteralPath $source -Destination $target -Force -ErrorAction Stop
        Test-PrivateOwnerPath $target $false
        if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $sourceSha) {
            throw 'Installed source readback hash mismatch.'
        }
    } catch {
        Copy-Item -LiteralPath $backup -Destination $target -Force
        throw
    }
    Write-Output ('BACKUP='+$backup)
    Write-Output 'INSTALL_OK=True; start ONLY Viewer via existing shortcut.'
    Write-Output 'To restore old login immediately: python owner_viewer.py --auth-mode manual'
    return
}
if (-not $BackupFile) { throw 'Rollback requires exact -BackupFile path from Install.' }
$fullBackup = [IO.Path]::GetFullPath($BackupFile)
if (-not $fullBackup.StartsWith($targetDir + [IO.Path]::DirectorySeparatorChar,
                               [StringComparison]::OrdinalIgnoreCase) -or
    -not $fullBackup.EndsWith('.bak',[StringComparison]::OrdinalIgnoreCase)) {
    throw 'Backup must be a protected Viewer .bak in the same owner directory.'
}
Test-PrivateOwnerPath $fullBackup $false
$backupSha = (Get-FileHash -LiteralPath $fullBackup -Algorithm SHA256).Hash.ToLowerInvariant()
Copy-Item -LiteralPath $fullBackup -Destination $target -Force -ErrorAction Stop
Test-PrivateOwnerPath $target $false
if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $backupSha) {
    throw 'Rollback verification failed.'
}
Write-Output ('ROLLBACK_OK=True; restored SHA='+$backupSha)
Write-Output 'Start ONLY Viewer via existing shortcut.'
