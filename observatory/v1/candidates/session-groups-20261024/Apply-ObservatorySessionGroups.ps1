# Manual, owner-only staged update of Fortis Observatory session grouping.
# Preview is read-only. Install never touches Docker, G2, archive, or tunnels.
[CmdletBinding()]
param(
 [ValidateSet('Preview','Install','Rollback')][string]$Action='Preview',
 [string]$BackupId=''
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$who=[Security.Principal.WindowsIdentity]::GetCurrent()
if(($who.Name.Split([char]92)[-1]) -ine 'alexa'){throw 'Use the approved Windows owner account.'}
$principal=[Security.Principal.WindowsPrincipal]::new($who)
if($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){
 throw 'Use the non-elevated Windows owner PowerShell.'
}
if([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA) -or
   [string]::IsNullOrWhiteSpace($env:USERPROFILE)){throw 'Owner profile paths missing'}
$destDir=Join-Path $env:LOCALAPPDATA 'FortisObservatoryV1\Viewer'
$sourceDir=Join-Path $env:USERPROFILE 'Repos\tunnel\observatory\v1\candidates\session-groups-20261024'
$approvedFile=Join-Path $destDir 'approved-owner.json'
$files=@(
 [pscustomobject]@{Name='owner_viewer.py';Old='d5a752267ed78bcadf4da4e27b71452f3fb2d2c69fb4d138bda3af13bbf49878';New='eae6879f7559b6b540acbdbaa3ced1c031935883aa6793f8a5901a1d658b3e05'},
 [pscustomobject]@{Name='owner_enrollment.py';Old='51ce3eb96fd3da285c591c063cb71642863b825d5fef63bc6c5060a814ca03e3';New='873ec864c5996234e930c3ceaf9fb75cbcdea945b7b84c76ea47d1cef164b0d3'}
)
$expectedDispatch='9da1bc2a223804660c2a9ea9033b86889dca7119d3a1b1dab18c85565360fea5'
function Assert-Private([string]$Path,[bool]$Protected){
 $item=Get-Item -LiteralPath $Path -Force -ErrorAction Stop
 if(($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){
  throw ('Reparse or symlink refused: '+$Path)
 }
 $acl=Get-Acl -LiteralPath $Path
 if($Protected -and !$acl.AreAccessRulesProtected){
  throw ('Directory ACL inheritance is not disabled: '+$Path)
 }
 foreach($rule in @($acl.Access)){
  if($rule.AccessControlType -ne [Security.AccessControl.AccessControlType]::Allow){continue}
  $sid=$rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
  if($sid -cne $who.User.Value -and $sid -cne 'S-1-5-18'){
   throw ('Unexpected allowed owner SID on: '+$Path)
  }
 }
}
function Sha([string]$Path){
 (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Assert-Stopped {
 $tcp=New-Object System.Net.Sockets.TcpClient
 try{
  $connect=$tcp.BeginConnect('127.0.0.1',18755,$null,$null)
  if($connect.AsyncWaitHandle.WaitOne(400)){
   try{$tcp.EndConnect($connect);throw 'Viewer port 18755 occupied. Stop ONLY Viewer.'}
   catch [System.Net.Sockets.SocketException]{}
  }
 }finally{$tcp.Dispose()}
}
Assert-Private $destDir $true
Assert-Private $approvedFile $false
Assert-Private $MyInvocation.MyCommand.Path $false
$privatePrefix=[IO.Path]::GetFullPath($destDir)+[IO.Path]::DirectorySeparatorChar
if(-not ([IO.Path]::GetFullPath($MyInvocation.MyCommand.Path)).StartsWith(
  $privatePrefix,[StringComparison]::OrdinalIgnoreCase)){
 throw 'Copy this script to the approved private Viewer folder before running.'
}
$config=Get-Content -LiteralPath $approvedFile -Encoding UTF8 -Raw | ConvertFrom-Json
if($config.owner_sid -cne $who.User.Value){throw 'Approved owner SID mismatch'}
Assert-Private (Join-Path $destDir 'owner_dispatch.py') $false
if((Sha (Join-Path $destDir 'owner_dispatch.py')) -cne $expectedDispatch){
 throw 'Installed owner_dispatch.py is not the pinned unified version; no changes made.'
}
foreach($item in $files){
 $src=Join-Path $sourceDir $item.Name
 $dst=Join-Path $destDir $item.Name
 Assert-Private $dst $false
 $srcItem=Get-Item -LiteralPath $src -Force -ErrorAction Stop
 if(($srcItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){
  throw ('Candidate source is a reparse point: '+$src)
 }
 if((Sha $src) -cne $item.New){throw ('Candidate hash mismatch: '+$item.Name)}
 $installed=Sha $dst
 if($installed -cne $item.Old -and $installed -cne $item.New){
  throw ('Unexpected installed version '+$item.Name+': '+$installed)
 }
 Write-Output ($item.Name+' SOURCE='+$item.New+' INSTALLED='+$installed)
}
if($Action -eq 'Preview'){
 Write-Output 'PREVIEW_OK=True; both source files, versions, owner and ACL verified.'
 Write-Output 'No installed code, Notifier or service was changed.'
 return
}
Assert-Stopped
if($Action -eq 'Install'){
 if($BackupId){throw 'BackupId is for rollback only'}
 if(@($files|Where-Object{(Sha (Join-Path $destDir $_.Name)) -cne $_.New}).Count -eq 0){
  Write-Output 'ALREADY_INSTALLED=True';return
 }
 if(@($files|Where-Object{(Sha (Join-Path $destDir $_.Name)) -cne $_.Old}).Count){
  throw 'Refusing a mixed version; no changes made.'
 }
 $id=(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[guid]::NewGuid().ToString('N')
 foreach($item in $files){
  $dst=Join-Path $destDir $item.Name
  $backup=Join-Path $destDir ($item.Name+'.before-session-groups-'+$id+'.bak')
  Copy-Item -LiteralPath $dst -Destination $backup -ErrorAction Stop
  Assert-Private $backup $false
  if((Sha $backup) -cne $item.Old){throw ('Backup readback mismatch: '+$item.Name)}
 }
 try{
  foreach($item in $files){
   $dst=Join-Path $destDir $item.Name
   Copy-Item -LiteralPath (Join-Path $sourceDir $item.Name) -Destination $dst -Force -ErrorAction Stop
   Assert-Private $dst $false
   if((Sha $dst) -cne $item.New){throw ('Install SHA readback mismatch: '+$item.Name)}
  }
 }catch{
  foreach($item in $files){
   $backup=Join-Path $destDir ($item.Name+'.before-session-groups-'+$id+'.bak')
   if(Test-Path -LiteralPath $backup -PathType Leaf){
    Copy-Item -LiteralPath $backup -Destination (Join-Path $destDir $item.Name) -Force
   }
  }
  throw
 }
 Write-Output ('BACKUP_ID='+$id)
 Write-Output 'INSTALL_OK=True; start only the usual owner-local Viewer.'
 return
}
if($BackupId -cnotmatch '^\d{8}-\d{6}-[a-f0-9]{32}$'){
 throw 'Rollback requires the exact BACKUP_ID from Install.'
}
foreach($item in $files){
 if((Sha (Join-Path $destDir $item.Name)) -cne $item.New){
  throw 'Rollback refused: installed Viewer is not the pinned candidate.'
 }
 $backup=Join-Path $destDir ($item.Name+'.before-session-groups-'+$BackupId+'.bak')
 Assert-Private $backup $false
 if((Sha $backup) -cne $item.Old){throw ('Rollback SHA mismatch: '+$item.Name)}
}
foreach($item in $files){
 $backup=Join-Path $destDir ($item.Name+'.before-session-groups-'+$BackupId+'.bak')
 $dst=Join-Path $destDir $item.Name
 Copy-Item -LiteralPath $backup -Destination $dst -Force -ErrorAction Stop
 Assert-Private $dst $false
 if((Sha $dst) -cne $item.Old){throw ('Rollback readback mismatch: '+$item.Name)}
}
Write-Output 'ROLLBACK_OK=True; restart only owner-local Viewer.'
