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
public static class FortisG2BrokerOpenV1 {
 [DllImport("kernel32.dll",EntryPoint="CreateFileW",CharSet=CharSet.Unicode,SetLastError=true)]
 static extern IntPtr CreateFile(string p,uint access,uint share,IntPtr security,uint disposition,uint flags,IntPtr template);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool CloseHandle(IntPtr h);
 public sealed class Result {public bool Opened,Closed;public int Win32;}
 public static Result Probe(string p,uint access){
  Result r=new Result();IntPtr h=CreateFile(p,access,7,IntPtr.Zero,3,0x02000000,IntPtr.Zero);
  if(h==new IntPtr(-1)){r.Win32=Marshal.GetLastWin32Error();r.Closed=true;return r;}
  r.Opened=true;r.Closed=CloseHandle(h);return r;
 }
}
'@
$queueRights=@(@('LIST',1),@('CREATE_FILE',2),@('CREATE_DIRECTORY',4),@('DELETE_CHILD',64),@('WRITE_DAC',262144),@('WRITE_OWNER',524288))
$parentRights=@(@('CREATE_FILE',2),@('CREATE_DIRECTORY',4),@('DELETE_CHILD',64),@('DELETE',65536),@('WRITE_DAC',262144),@('WRITE_OWNER',524288))
$fileRights=@(@('WRITE',2),@('APPEND',4),@('DELETE',65536),@('WRITE_DAC',262144),@('WRITE_OWNER',524288))
$targets=@(
 @{Label='BrokerInbox';Kind='Queue';Path='C:\Users\alexa\Workfiles\.fortis-bridge-broker-v1\in'},
 @{Label='BrokerOutbox';Kind='Queue';Path='C:\Users\alexa\Workfiles\.fortis-bridge-broker-v1\out'},
 @{Label='BrokerWorker';Kind='File';Path='C:\Users\alexa\chatgpt-repo-mode\broker\worker.py'},
 @{Label='BrokerWorkerParent';Kind='Parent';Path='C:\Users\alexa\chatgpt-repo-mode\broker'},
 @{Label='BridgePython';Kind='File';Path='C:\Users\alexa\chatgpt-bridge\bridge.py'},
 @{Label='BridgeParent';Kind='Parent';Path='C:\Users\alexa\chatgpt-bridge'},
 @{Label='BridgeRegistry';Kind='File';Path='C:\Users\alexa\chatgpt-bridge\repos.json'}
)
$workspace=Join-Path $env:LOCALAPPDATA 'FortisHostG2\Workspace'
$positive=@()
foreach($right in $queueRights){
 $r=[FortisG2BrokerOpenV1]::Probe($workspace,[uint32]$right[1])
 $positive+=[pscustomobject]@{Right=$right[0];Pass=($r.Opened -and $r.Closed)}
}
if(@($positive|Where-Object {!$_.Pass}).Count){throw 'Own workspace positive control failed'}
$rows=@();$count=0;$allClosed=$true
foreach($target in $targets){
 $rights=if($target.Kind -eq 'Queue'){$queueRights}elseif($target.Kind -eq 'Parent'){$parentRights}else{$fileRights}
 $out=[ordered]@{};$pass=$true
 foreach($namespace in @('Normal','LocalhostCShare')){
  $path=$target.Path;if($namespace -eq 'LocalhostCShare'){$path='\\localhost\C$'+$path.Substring(2)}
  $codes=[ordered]@{}
  foreach($right in $rights){
   $r=[FortisG2BrokerOpenV1]::Probe($path,[uint32]$right[1]);$count++
   $codes[$right[0]]=$r.Win32
   if(!$r.Closed){$allClosed=$false}
   if($r.Opened -or !$r.Closed -or $r.Win32 -ne 5){$pass=$false}
  }
  $out[$namespace]=[pscustomobject]$codes
 }
 $rows+=[pscustomobject]@{Label=$target.Label;Kind=$target.Kind;Namespaces=[pscustomobject]$out;Pass=$pass}
}
[pscustomobject]@{
 Check='G2_KNOWN_SNAPSHOT_BROKER_BOUNDARY';Utc=[DateTime]::UtcNow.ToString('o')
 SourceSHA256=$CapturedSHA256;Sid=$id.User.Value;Session=$session;AdminGroupPresent=$false
 OwnPositiveCount=$positive.Count;OwnPositivesPass=$true;OpenCount=$count;TargetCount=$targets.Count;Rows=$rows
 Passed=($count -eq 78 -and $allClosed -and @($rows|Where-Object {!$_.Pass}).Count -eq 0)
 AllHandlesClosed=$allClosed;OpenDisposition='OPEN_EXISTING'
 QueueEntriesListed=0;QueueMessagesCreated=0;ContentReads=0;ContentWrites=0;AclWrites=0
 TaskStartedOrStopped=$false;SnapshotRequested=$false;RuntimeRestarted=$false
 Limits=@('Selected queue directory capabilities and mutation handles for worker/bridge/registry/parents','No request files read, written or submitted','Individual historical queue responses, private permits/claims and all other IPC not audited','Independent Repo access to queue intentionally remains outside G2 token scope')
}|ConvertTo-Json -Depth 7 -Compress
