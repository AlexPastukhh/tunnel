#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$CapturedSHA256)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
$session=[Diagnostics.Process]::GetCurrentProcess().SessionId
if($id.User.Value -ne 'S-1-5-21-303538662-3368424508-2654684973-1009' -or $session -ne 2 -or @($id.Groups|Where-Object Value -eq 'S-1-5-32-544').Count){throw 'Exact ordinary G2 Session2 required'}
if($CapturedSHA256 -notmatch '^[A-F0-9]{64}$'){throw 'Captured source hash required'}
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class FortisG2OwnerAssetOpenV1 {
 [DllImport("kernel32.dll",EntryPoint="CreateFileW",CharSet=CharSet.Unicode,SetLastError=true)]
 static extern IntPtr CreateFile(string p,uint access,uint share,IntPtr security,uint disposition,uint flags,IntPtr template);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool CloseHandle(IntPtr h);
 public sealed class Result {public bool Opened,Closed;public int Win32,CloseWin32;}
 public static Result Probe(string path,uint access){
  Result r=new Result();IntPtr h=CreateFile(path,access,7,IntPtr.Zero,3,0x02000000,IntPtr.Zero);
  if(h==new IntPtr(-1)){r.Win32=Marshal.GetLastWin32Error();r.Closed=true;return r;}
  r.Opened=true;r.Closed=CloseHandle(h);if(!r.Closed)r.CloseWin32=Marshal.GetLastWin32Error();return r;
 }
}
'@
$targets=@(
 @{Label='RepoNamedProfile';Kind='File';Path='C:\Users\alexa\AppData\Roaming\tunnel-client\repo-mode.yaml'},
 @{Label='RepoRuntimeKeyFile';Kind='File';Path='C:\Users\alexa\AppData\Roaming\tunnel-client\runtime.key'},
 @{Label='RepoRun';Kind='File';Path='C:\Users\alexa\chatgpt-repo-mode\run-tunnel.ps1'},
 @{Label='RepoControl';Kind='File';Path='C:\Users\alexa\chatgpt-repo-mode\control.ps1'},
 @{Label='RepoRecoveryBackup';Kind='File';Path='C:\Users\alexa\AppData\Local\FortisRepoApiMigration\a6d1e489e8b74a6dbbcc17978070641b\backup.json'},
 @{Label='RuntimeDaclBackup';Kind='File';Path='C:\Users\alexa\AppData\Local\FortisHostG2AclBackup\runtime-dacl-20261013T071259525Z-d7c956e72739475a93ff507bf7048ee7.json'},
 @{Label='OwnerEdgeLocalState';Kind='File';Path='C:\Users\alexa\AppData\Local\Microsoft\Edge\User Data\Local State'},
 @{Label='RepoRecoveryParent';Kind='Directory';Path='C:\Users\alexa\AppData\Local\FortisRepoApiMigration\a6d1e489e8b74a6dbbcc17978070641b'},
 @{Label='RuntimeDaclBackupParent';Kind='Directory';Path='C:\Users\alexa\AppData\Local\FortisHostG2AclBackup'}
)
$rights=@(@('READ_OR_LIST',1),@('WRITE_OR_CREATE',2),@('APPEND_OR_MKDIR',4),@('WRITE_ATTRIBUTES',256),@('DELETE',65536),@('WRITE_DAC',262144),@('WRITE_OWNER',524288))
$workspace=Join-Path $env:LOCALAPPDATA 'FortisHostG2\Workspace'
$item=Get-Item -LiteralPath $workspace -ErrorAction Stop
if(!$item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Ordinary own workspace required'}
$dir=Join-Path $workspace ('owner-asset-positive-'+[guid]::NewGuid().ToString('N'))
$file=Join-Path $dir 'synthetic-marker.txt'
$dirCreated=$false;$fileCreated=$false;$cleanup=$false;$errorKind=$null
$positive=@();$rows=@();$probeCount=0
try{
 $null=New-Item -ItemType Directory -Path $dir -ErrorAction Stop;$dirCreated=$true
 $stream=[IO.File]::Open($file,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
 $fileCreated=$true
 try{$bytes=[Text.Encoding]::UTF8.GetBytes('Fortis G2 owner-asset positive control');$stream.Write($bytes,0,$bytes.Length)}finally{$stream.Dispose()}
 foreach($kind in @('File','Directory')){
  $path=if($kind -eq 'File'){$file}else{$dir}
  $checks=@($rights);if($kind -eq 'Directory'){$checks+=,@('DELETE_CHILD',64)}
  foreach($right in $checks){
   $result=[FortisG2OwnerAssetOpenV1]::Probe($path,[uint32]$right[1])
   $positive+=[pscustomobject]@{Kind=$kind;Right=$right[0];Pass=($result.Opened -and $result.Closed);Result=$result}
  }
 }
 if(@($positive|Where-Object {!$_.Pass}).Count){throw 'Synthetic own positive control failed'}
 foreach($target in $targets){
  $out=[ordered]@{};$pass=$true
  $checks=@($rights);if($target.Kind -eq 'Directory'){$checks+=,@('DELETE_CHILD',64)}
  foreach($namespace in @('Normal','LocalhostCShare')){
   $path=$target.Path;if($namespace -eq 'LocalhostCShare'){$path='\\localhost\C$'+$path.Substring(2)}
   $codes=[ordered]@{}
   foreach($right in $checks){
    $result=[FortisG2OwnerAssetOpenV1]::Probe($path,[uint32]$right[1]);$probeCount++
    $codes[$right[0]]=$result.Win32
    if($result.Opened -or !$result.Closed -or $result.Win32 -ne 5){$pass=$false}
   }
   $out[$namespace]=[pscustomobject]$codes
  }
  $rows+=[pscustomobject]@{Label=$target.Label;Kind=$target.Kind;Namespaces=[pscustomobject]$out;Pass=$pass}
 }
}catch{$errorKind=$_.Exception.GetType().FullName}
finally{
 try{
  if($fileCreated){[IO.File]::Delete($file)}
  if($dirCreated){[IO.Directory]::Delete($dir,$false)}
  $cleanup=!(Test-Path -LiteralPath $file) -and !(Test-Path -LiteralPath $dir)
 }catch{$cleanup=$false;if(!$errorKind){$errorKind='OWN_FIXTURE_CLEANUP_FAILED'}}
}
[pscustomobject]@{
 Check='G2_SELECTED_OWNER_ASSET_CAPABILITIES';Utc=[DateTime]::UtcNow.ToString('o')
 SourceSHA256=$CapturedSHA256;Sid=$id.User.Value;Session=$session;AdminGroupPresent=$false
 PositiveControlCount=$positive.Count;PositiveControlsPass=($positive.Count -eq 15 -and @($positive|Where-Object {!$_.Pass}).Count -eq 0)
 Rows=$rows;TargetCount=$targets.Count;ProtectedOpenCount=$probeCount
 Passed=(!$errorKind -and $cleanup -and $probeCount -eq 130 -and @($rows|Where-Object {!$_.Pass}).Count -eq 0)
 ErrorKind=$errorKind;OwnFixtureCleanup=$cleanup;OpenDisposition='OPEN_EXISTING'
 OwnerContentsRead=0;OwnerContentWrites=0;OwnerDirectoryEnumerations=0;AclWrites=0
 ProfilesOrKeysModified=$false;RuntimeRestarted=$false
 Limits=@('Only 7 selected existing owner files and 2 immediate backup directories','File-parent DELETE_CHILD tested for two selected backups','No key/browser/backup bytes read or hashed','Other personal assets, links, handles, backup restoration and independent Repo mounts not accepted')
}|ConvertTo-Json -Depth 7 -Compress
