#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$CapturedSHA256)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
$session=[Diagnostics.Process]::GetCurrentProcess().SessionId
if($id.User.Value -ne 'S-1-5-21-303538662-3368424508-2654684973-1009' -or $session -ne 2 -or @($id.Groups|Where-Object Value -eq 'S-1-5-32-544').Count){throw 'Exact ordinary guest Session2 required'}
if($CapturedSHA256 -notmatch '^[A-F0-9]{64}$'){throw 'Captured hash required'}
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class FortisG2ProtectedNamespaceV1 {
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
 [pscustomobject]@{Kind='Directory';Path='C:\Tools'},
 [pscustomobject]@{Kind='Directory';Path='C:\Tools\tunnel-client'},
 [pscustomobject]@{Kind='Directory';Path='C:\Tools\desktop-commander-runtime'},
 [pscustomobject]@{Kind='Directory';Path='C:\Tools\desktop-commander'},
 [pscustomobject]@{Kind='File';Path='C:\Tools\tunnel-client\tunnel-client.exe'},
 [pscustomobject]@{Kind='File';Path='C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe'},
 [pscustomobject]@{Kind='File';Path='C:\Tools\desktop-commander-runtime\node.exe'},
 [pscustomobject]@{Kind='File';Path='C:\Tools\desktop-commander\node_modules\@wonderwhy-er\desktop-commander\dist\index.js'}
)
$mutations=@(
 @('WRITE_DATA_OR_CREATE_FILE',2),@('APPEND_OR_CREATE_DIRECTORY',4),
 @('WRITE_ATTRIBUTES',256),@('DELETE',65536),@('WRITE_DAC',262144),@('WRITE_OWNER',524288)
)
$rows=@()
foreach($target in $targets){
 foreach($namespace in @('NormalReadControl','Extended','LocalhostCShare')){
  $path=$target.Path
  if($namespace -eq 'Extended'){$path='\\?\'+$path}
  if($namespace -eq 'LocalhostCShare'){$path='\\localhost\C$'+$path.Substring(2)}
  $rights=@(,@('READ_OR_LIST',1))
  if($namespace -ne 'NormalReadControl'){
   $rights+=$mutations
   if($target.Kind -eq 'Directory'){$rights+=,@('DELETE_CHILD',64)}
  }
  foreach($right in $rights){
   $probe=[FortisG2ProtectedNamespaceV1]::Probe($path,[uint32]$right[1])
   $expected=if($right[1] -eq 1){'ALLOW'}else{'DENY_ACCESS_5'}
   $pass=if($expected -eq 'ALLOW'){$probe.Opened -and $probe.Closed}else{!$probe.Opened -and $probe.Closed -and $probe.Win32 -eq 5}
   $rows+=[pscustomobject]@{Namespace=$namespace;Kind=$target.Kind;NormalPath=$target.Path;Right=$right[0];Mask=$right[1];Expected=$expected;Pass=$pass;Result=$probe}
  }
 }
}
[pscustomobject]@{
 Check='G2_SELECTED_PROTECTED_RUNTIME_NAMESPACE_CAPABILITIES';Utc=[DateTime]::UtcNow.ToString('o')
 SourceSHA256=$CapturedSHA256;Sid=$id.User.Value;Session=$session;AdminGroupPresent=$false
 OpenDisposition='OPEN_EXISTING';TargetCount=$targets.Count;Rows=$rows;RowCount=$rows.Count
 Passed=($rows.Count -eq 128 -and @($rows|Where-Object {!$_.Pass}).Count -eq 0)
 ContentReads=0;ContentWrites=0;AclWrites=0;FilesCreated=0;RuntimeRestarted=$false
 Scope='8_FIXED_INSTALLED_RUNTIME_OBJECTS_EXTENDED_LOCALHOST_C_SHARE_WITH_NORMAL_READ_CONTROLS'
 ReusedEvidence='E26 normal mutation tests; E31 synthetic namespace controls'
 Limitations=@('Capability opens only; no protected writes attempted','C:\Tools directory tested itself, not every child recursively','SMB authenticated identity not independently established','No conclusion about other shares, private files, backups or owner API')
}|ConvertTo-Json -Depth 7
