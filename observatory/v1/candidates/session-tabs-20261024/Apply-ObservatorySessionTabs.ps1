# Only replaces owner_viewer.py in a previously approved owner-private Viewer install.
# Preview is read-only. Never touches Docker, G2, tunnels, notifier or credentials.
[CmdletBinding()]
param(
  [ValidateSet('Preview','Install','Rollback')][string]$Action='Preview',
  [string]$BackupFile
)
$ErrorActionPreference='Stop'
$ExpectedOld='a3eb75f113a6152adbb3381d6a9b6cd845dec4e927c7b20c80885968e635b48d'
$ExpectedNew='a34cb4ffd3805446c9e81e4051bcbe0018a14b6a507b65b9eecf10b23d5a3035'
$source=Join-Path $PSScriptRoot 'owner_viewer.py'
$targetDir=Join-Path $env:LOCALAPPDATA 'FortisObservatoryV1\Viewer'
$target=Join-Path $targetDir 'owner_viewer.py'
$config=Join-Path $targetDir 'approved-owner.json'
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
if (($identity.Name -split '\\')[-1] -ine 'alexa') {
  throw 'Run as approved Windows user alexa, never as G2 or Administrator.'
}
if (!(Test-Path -LiteralPath $targetDir -PathType Container) -or
    !(Test-Path -LiteralPath $target -PathType Leaf) -or
    !(Test-Path -LiteralPath $config -PathType Leaf)) {
  throw 'Existing approved Viewer installation is required.'
}
$approved=Get-Content -LiteralPath $config -Encoding UTF8 -Raw | ConvertFrom-Json
if ($approved.owner_sid -cne $identity.User.Value) { throw 'Approved owner SID mismatch.' }
function Assert-PrivatePath([string]$Path,[bool]$NeedProtected) {
  $item=Get-Item -LiteralPath $Path -Force -ErrorAction Stop
  if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw ('Symlink/reparse point is prohibited: '+$Path)
  }
  $acl=Get-Acl -LiteralPath $Path
  if ($NeedProtected -and -not $acl.AreAccessRulesProtected) {
    throw ('Owner directory inherits ACL: '+$Path)
  }
  foreach ($rule in @($acl.Access)) {
    if ($rule.AccessControlType -ne 'Allow') { continue }
    $sid=$rule.IdentityReference.Translate(
      [Security.Principal.SecurityIdentifier]).Value
    if ($sid -ne $identity.User.Value -and $sid -ne 'S-1-5-18') {
      throw ('Foreign allowed SID: '+$Path)
    }
  }
}
Assert-PrivatePath $targetDir $true
Assert-PrivatePath $target $false
Assert-PrivatePath $config $false
$sourceItem=Get-Item -LiteralPath $source -Force -ErrorAction Stop
if (($sourceItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
  throw 'Candidate source cannot be a symlink.'
}
$sourceSha=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
if ($sourceSha -cne $ExpectedNew) { throw 'Candidate hash mismatch. No changes made.' }
$currentSha=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
Write-Output ('CandidateSHA='+$sourceSha)
Write-Output ('InstalledSHA='+$currentSha)
if ($Action -eq 'Preview') {
  $ready=($currentSha -ceq $ExpectedOld -or $currentSha -ceq $ExpectedNew)
  Write-Output ('READY_TO_INSTALL='+$ready)
  Write-Output 'PREVIEW_ONLY=True; no installed files changed.'
  return
}
function Assert-ViewerStopped {
  $client=New-Object System.Net.Sockets.TcpClient
  try {
    $ar=$client.BeginConnect('127.0.0.1',18755,$null,$null)
    if ($ar.AsyncWaitHandle.WaitOne(400)) {
      try {
        $client.EndConnect($ar)
        throw 'Port 18755 is occupied. Stop ONLY Observatory Viewer first.'
      } catch [System.Net.Sockets.SocketException] {}
    }
  } finally { $client.Dispose() }
}
Assert-ViewerStopped
if ($Action -eq 'Install') {
  if ($BackupFile) { throw '-BackupFile is for Rollback only.' }
  if ($currentSha -ceq $ExpectedNew) {
    Write-Output 'ALREADY_INSTALLED=True'
    return
  }
  if ($currentSha -cne $ExpectedOld) {
    throw 'Installed Viewer differs from reviewed base. Stop; do not overwrite.'
  }
  $backup=Join-Path $targetDir ('owner_viewer.before-session-tabs-'+
    (Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+
    [Guid]::NewGuid().ToString('N')+'.bak')
  Copy-Item -LiteralPath $target -Destination $backup -ErrorAction Stop
  Assert-PrivatePath $backup $false
  if ((Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash.ToLowerInvariant() -cne $ExpectedOld) {
    throw 'Backup verification failed. No candidate installed.'
  }
  try {
    Copy-Item -LiteralPath $source -Destination $target -Force -ErrorAction Stop
    Assert-PrivatePath $target $false
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -cne $ExpectedNew) {
      throw 'Installed candidate verification failed.'
    }
  } catch {
    Copy-Item -LiteralPath $backup -Destination $target -Force
    throw
  }
  Write-Output ('BACKUP='+$backup)
  Write-Output 'INSTALL_OK=True; start only your existing Observatory Viewer.'
  return
}
if ($currentSha -cne $ExpectedNew) { throw 'Rollback is allowed only from the reviewed tab version.' }
if (!$BackupFile) { throw 'Rollback requires the exact BACKUP path from Install.' }
$fullBackup=[IO.Path]::GetFullPath($BackupFile)
$prefix=[IO.Path]::GetFullPath($targetDir)+[IO.Path]::DirectorySeparatorChar
if (!$fullBackup.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase) -or
    !$fullBackup.EndsWith('.bak',[StringComparison]::OrdinalIgnoreCase)) {
  throw 'Backup path must point into approved Viewer directory.'
}
Assert-PrivatePath $fullBackup $false
$backupSha=(Get-FileHash -LiteralPath $fullBackup -Algorithm SHA256).Hash.ToLowerInvariant()
if ($backupSha -cne $ExpectedOld) { throw 'Rollback backup differs from reviewed original.' }
Copy-Item -LiteralPath $fullBackup -Destination $target -Force -ErrorAction Stop
Assert-PrivatePath $target $false
if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -cne $ExpectedOld) {
  throw 'Rollback readback failed.'
}
Write-Output 'ROLLBACK_OK=True; start only Observatory Viewer.'
