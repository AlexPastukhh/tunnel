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
public static class FortisG2NamespaceOpenV1 {
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
$root='C:\Users\Public\Documents\FortisHostG1Probe'
$namespaces=@(
 [pscustomobject]@{Name='Normal';Root=$root},
 [pscustomobject]@{Name='Extended';Root=('\\?\'+$root)},
 [pscustomobject]@{Name='LocalhostCShare';Root='\\localhost\C$\Users\Public\Documents\FortisHostG1Probe'}
)
$rights=@(
 @('READ_OR_LIST',1),@('WRITE_DATA_OR_CREATE_FILE',2),@('APPEND_OR_CREATE_DIRECTORY',4),
 @('WRITE_ATTRIBUTES',256),@('DELETE',65536),@('WRITE_DAC',262144),@('WRITE_OWNER',524288)
)
# RW contract: Modify, Synchronize (1245631), not FullControl; checked on fixture directory/file.
$rows=@()
foreach($ns in $namespaces){
 foreach($fixture in @('RW','RO','DENY')){
  foreach($kind in @('Directory','File')){
   $path=$ns.Root+'\'+$fixture
   if($kind -eq 'File'){$path+='\marker.txt'}
   $selected=@($rights)
   if($kind -eq 'Directory'){$selected+=,@('DELETE_CHILD',64)}
   foreach($right in $selected){
    $probe=[FortisG2NamespaceOpenV1]::Probe($path,[uint32]$right[1])
    $expected=if(($fixture -eq 'RW' -and ((1245631 -band [int]$right[1]) -eq [int]$right[1])) -or ($fixture -eq 'RO' -and $right[1] -eq 1)){'ALLOW'}else{'DENY_ACCESS_5'}
    $pass=if($expected -eq 'ALLOW'){$probe.Opened -and $probe.Closed}else{!$probe.Opened -and $probe.Closed -and $probe.Win32 -eq 5}
    $rows+=[pscustomobject]@{Namespace=$ns.Name;Fixture=$fixture;Kind=$kind;Right=$right[0];Mask=$right[1];Expected=$expected;Pass=$pass;Result=$probe}
   }
  }
 }
}
[pscustomobject]@{
 Check='G2_SYNTHETIC_NAMESPACE_CAPABILITY_MATRIX';Utc=[DateTime]::UtcNow.ToString('o')
 SourceSHA256=$CapturedSHA256;Sid=$id.User.Value;Session=$session;AdminGroupPresent=$false
 OpenDisposition='OPEN_EXISTING';Rows=$rows;RowCount=$rows.Count
 Passed=($rows.Count -eq 135 -and @($rows|Where-Object {!$_.Pass}).Count -eq 0)
 ContentReads=0;ContentWrites=0;AclWrites=0;FilesCreated=0;RuntimeRestarted=$false
 Scope='FIXED_SYNTHETIC_RW_RO_DENY_NORMAL_EXTENDED_LOCALHOST_C_SHARE'
 Limitations=@('Capability opens only; no protected writes attempted','Localhost SMB authenticated identity not independently established','No conclusion about other shares, private files or owner API')
}|ConvertTo-Json -Depth 7
