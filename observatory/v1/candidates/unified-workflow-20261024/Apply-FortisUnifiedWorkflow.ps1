# Fortis Observatory unified workflow, owner-only and manually invoked.
# The script itself must be copied into the protected Viewer folder BEFORE running.
[CmdletBinding()]
param(
  [ValidateSet('Preview','Install','Rollback')][string]$Action='Preview',
  [string]$BackupId=''
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$who=[Security.Principal.WindowsIdentity]::GetCurrent()
if (($who.Name -split '\\')[-1] -ine 'alexa') { throw 'Only Windows owner alexa can install.' }
$principal=[Security.Principal.WindowsPrincipal]::new($who)
if($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){
  throw 'Use normal non-elevated owner PowerShell, never Administrator.'
}
$install=Join-Path $env:LOCALAPPDATA 'FortisObservatoryV1\Viewer'
$configPath=Join-Path $install 'approved-owner.json'
$scriptPath=$MyInvocation.MyCommand.Path
$candidateDir=Join-Path $env:USERPROFILE 'Repos\tunnel\observatory\v1\candidates\unified-workflow-20261024'
$spec=@(
  [pscustomobject]@{File='owner_viewer.py'; Old=@(
    'a3eb75f113a6152adbb3381d6a9b6cd845dec4e927c7b20c80885968e635b48d',
    'a34cb4ffd3805446c9e81e4051bcbe0018a14b6a507b65b9eecf10b23d5a3035'
  ); New='f3230cb531d89d9cc4f60bea52fd5722b1b1e82a724759dede6636aabf806c8a'},
  [pscustomobject]@{File='owner_dispatch.py'; Old=@(
    'a00d22dfdf4cfc8902e85cfd7b101867dc9507fb99f9b4b5352ffe1d5a81a31f'
  ); New='9da1bc2a223804660c2a9ea9033b86889dca7119d3a1b1dab18c85565360fea5'}
)
function Verify-Acl([string]$Path,[bool]$RequireProtected){
  $item=Get-Item -LiteralPath $Path -Force -ErrorAction Stop
  if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){
    throw "A reparse point is not allowed: $Path"
  }
  $acl=Get-Acl -LiteralPath $Path
  if ($RequireProtected -and !$acl.AreAccessRulesProtected){
    throw "The owner-private directory must have protected ACLs: $Path"
  }
  foreach($rule in @($acl.Access)){
    if ($rule.AccessControlType -ne [Security.AccessControl.AccessControlType]::Allow){continue}
    $sid=$rule.IdentityReference.Translate(
      [Security.Principal.SecurityIdentifier]).Value
    if ($sid -cne $who.User.Value -and $sid -cne 'S-1-5-18'){
      throw "Unexpected ACL identity on owner target: $Path"
    }
  }
}
function Sha([string]$Path){
  (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Assert-Stopped(){
  $client=New-Object System.Net.Sockets.TcpClient
  try{
    $conn=$client.BeginConnect('127.0.0.1',18755,$null,$null)
    if($conn.AsyncWaitHandle.WaitOne(400)){
      try {
        $client.EndConnect($conn)
        throw 'Viewer port 18755 is active. Stop only Viewer before installation.'
      } catch [System.Net.Sockets.SocketException] {}
    }
  } finally { $client.Dispose() }
}
if(!(Test-Path -LiteralPath $install -PathType Container) -or
   !(Test-Path -LiteralPath $configPath -PathType Leaf)){
  throw 'The existing approved owner Viewer is required.'
}
Verify-Acl $install $true
Verify-Acl $configPath $false
Verify-Acl $scriptPath $false
$installPrefix=[IO.Path]::GetFullPath($install)+[IO.Path]::DirectorySeparatorChar
if(!([IO.Path]::GetFullPath($scriptPath)).StartsWith($installPrefix,
  [StringComparison]::OrdinalIgnoreCase)){
  throw 'Run the installer only from the protected Viewer directory.'
}
$approved=Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
if($approved.owner_sid -cne $who.User.Value){throw 'Approved owner SID mismatch.'}
foreach($entry in $spec){
  $src=Join-Path $candidateDir $entry.File
  $dst=Join-Path $install $entry.File
  Verify-Acl $dst $false
  if(!(Test-Path -LiteralPath $src -PathType Leaf)){
    throw "Missing candidate source: $src"
  }
  $item=Get-Item -LiteralPath $src -Force
  if(($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){
    throw "Refusing linked source: $src"
  }
  $candidateHash=Sha $src
  if($candidateHash -cne $entry.New){throw "Candidate SHA mismatch: $($entry.File)"}
  $currentHash=Sha $dst
  if(($entry.Old -cnotcontains $currentHash) -and ($currentHash -cne $entry.New)){
    throw "Installed version was not reviewed: $($entry.File), SHA $currentHash"
  }
  Write-Output ("SOURCE "+$entry.File+" "+$candidateHash)
  Write-Output ("INSTALLED "+$entry.File+" "+$currentHash)
}
if($Action -eq 'Preview'){
  Write-Output 'PREVIEW_OK=True; owner/ACL and both source hashes verified.'
  Write-Output 'No processes or files changed.'
  return
}
Assert-Stopped
if($Action -eq 'Install'){
  if($BackupId){throw 'BackupId is for Rollback only.'}
  if((Sha (Join-Path $install 'owner_viewer.py')) -ceq $spec[0].New -and
     (Sha (Join-Path $install 'owner_dispatch.py')) -ceq $spec[1].New){
    Write-Output 'ALREADY_INSTALLED=True';return
  }
  $id=(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N')
  foreach($entry in $spec){
    $dst=Join-Path $install $entry.File
    $backup=Join-Path $install ($entry.File+'.before-unified-'+$id+'.bak')
    Copy-Item -LiteralPath $dst -Destination $backup -ErrorAction Stop
    Verify-Acl $backup $false
    if((Sha $backup) -cne (Sha $dst)){throw "Backup readback failed: $($entry.File)"}
  }
  try{
    foreach($entry in $spec){
      $src=Join-Path $candidateDir $entry.File
      $dst=Join-Path $install $entry.File
      Copy-Item -LiteralPath $src -Destination $dst -Force -ErrorAction Stop
      Verify-Acl $dst $false
      if((Sha $dst) -cne $entry.New){throw "Install readback failed: $($entry.File)"}
    }
  } catch {
    foreach($entry in $spec){
      $backup=Join-Path $install ($entry.File+'.before-unified-'+$id+'.bak')
      if(Test-Path -LiteralPath $backup -PathType Leaf){
        Copy-Item -LiteralPath $backup -Destination (Join-Path $install $entry.File) -Force
      }
    }
    throw
  }
  Write-Output ('BACKUP_ID='+$id)
  Write-Output 'INSTALL_OK=True; use existing Viewer shortcut to restart only Viewer.'
  return
}
if($BackupId -cnotmatch '^\d{8}-\d{6}-[a-f0-9]{32}$'){
  throw 'Rollback requires exact BACKUP_ID from a successful Install.'
}
foreach($entry in $spec){
  $dst=Join-Path $install $entry.File
  if((Sha $dst) -cne $entry.New){throw "Rollback refuses unknown installed version: $($entry.File)"}
  $backup=Join-Path $install ($entry.File+'.before-unified-'+$BackupId+'.bak')
  Verify-Acl $backup $false
  if($entry.Old -cnotcontains (Sha $backup)){
    throw "Rollback backup SHA not reviewed: $($entry.File)"
  }
}
foreach($entry in $spec){
  $backup=Join-Path $install ($entry.File+'.before-unified-'+$BackupId+'.bak')
  $dst=Join-Path $install $entry.File
  Copy-Item -LiteralPath $backup -Destination $dst -Force
  Verify-Acl $dst $false
  if((Sha $backup) -cne (Sha $dst)){throw "Rollback readback failed: $($entry.File)"}
}
Write-Output 'ROLLBACK_OK=True; use existing Viewer shortcut to restart only Viewer.'
