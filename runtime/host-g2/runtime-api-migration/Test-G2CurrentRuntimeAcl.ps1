#requires -Version 5.1
[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][int]$ExpectedGuestSession,
 [Parameter(Mandatory=$true)][int]$RuntimePid,
 [Parameter(Mandatory=$true)][int]$PythonPid,
 [Parameter(Mandatory=$true)][int]$NodePid
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
$session=[Diagnostics.Process]::GetCurrentProcess().SessionId
if($id.User.Value -ne 'S-1-5-21-303538662-3368424508-2654684973-1009' -or $session -ne $ExpectedGuestSession -or $session -le 0 -or @($id.Groups|Where-Object Value -eq 'S-1-5-32-544').Count){throw 'Exact ordinary guest session required'}
$chain=@()
foreach($item in @(@($RuntimePid,'tunnel-client-runtime.exe'),@($PythonPid,'python.exe'),@($NodePid,'node.exe'))){
 $p=Get-CimInstance Win32_Process -Filter ('ProcessId='+$item[0])
 if(!$p -or $p.Name -ne $item[1] -or $p.SessionId -ne $session){throw 'G2 process identity/session drift'}
 $sid=Invoke-CimMethod -InputObject $p -MethodName GetOwnerSid
 if($sid.ReturnValue -ne 0 -or $sid.Sid -ne $id.User.Value){throw 'G2 process SID drift'}
 $chain+=[pscustomobject]@{Pid=$p.ProcessId;Parent=$p.ParentProcessId;Name=$p.Name;Sid=$sid.Sid;Session=$p.SessionId;CreatedUtc=$p.CreationDate.ToUniversalTime().ToString('o')}
}
if($chain[1].Parent -ne $RuntimePid -or $chain[2].Parent -ne $PythonPid){throw 'G2 parent chain drift'}
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class FortisG2FileOpenV1 {
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
$workspace=Join-Path $env:LOCALAPPDATA 'FortisHostG2\Workspace'
foreach($p in @((Split-Path $workspace),$workspace)){
 if(!(Test-Path -LiteralPath $p -PathType Container) -or ((Get-Item -LiteralPath $p).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Own ordinary workspace directory required'}
}
$dir=Join-Path $workspace ('acl-regression-'+[guid]::NewGuid().ToString('N'))
$file=Join-Path $dir 'synthetic-marker.txt'
$created=$false;$fileCreated=$false;$cleanup=$false;$errorText=$null;$roundtrip=$false
$positive=@();$rows=@()
try{
 $null=New-Item -ItemType Directory -Path $dir -ErrorAction Stop;$created=$true
 $b=[Text.Encoding]::UTF8.GetBytes('Fortis G2 synthetic ACL positive marker')
 $f=[IO.File]::Open($file,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
 $fileCreated=$true
 try{$f.Write($b,0,$b.Length)}finally{$f.Dispose()}
 $roundtrip=[Convert]::ToBase64String([IO.File]::ReadAllBytes($file)) -ceq [Convert]::ToBase64String($b)
 $mutations=@(@('WRITE_DATA_OR_CREATE_FILE',2),@('APPEND_OR_CREATE_DIRECTORY',4),@('WRITE_ATTRIBUTES',256),@('DELETE',65536),@('WRITE_DAC',262144),@('WRITE_OWNER',524288))
 foreach($kind in @('Directory','File')){
  $path=if($kind -eq 'Directory'){$dir}else{$file}
  foreach($right in $mutations){
   $probe=[FortisG2FileOpenV1]::Probe($path,[uint32]$right[1])
   $positive+=[pscustomobject]@{Kind=$kind;Right=$right[0];Mask=$right[1];Result=$probe;Pass=($probe.Opened -and $probe.Closed)}
  }
 }
 if(!$roundtrip -or @($positive|Where-Object {!$_.Pass}).Count){throw 'Own positive control failed'}
 $targets=@(
  @('Directory','C:\Tools'),@('Directory','C:\Tools\tunnel-client'),
  @('Directory','C:\Tools\desktop-commander-runtime'),@('Directory','C:\Tools\desktop-commander'),
  @('File','C:\Tools\tunnel-client\tunnel-client.exe'),
  @('File','C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe'),
  @('File','C:\Tools\desktop-commander-runtime\node.exe'),
  @('File','C:\Tools\desktop-commander\node_modules\@wonderwhy-er\desktop-commander\dist\index.js')
 )
 foreach($target in $targets){
  foreach($right in @(@('READ_OR_LIST',1),@('EXECUTE_OR_TRAVERSE',32))+$mutations){
   $probe=[FortisG2FileOpenV1]::Probe($target[1],[uint32]$right[1])
   $expected=if($right[1] -in @(1,32)){'ALLOW'}else{'DENY_ACCESS_5'}
   $pass=if($expected -eq 'ALLOW'){$probe.Opened -and $probe.Closed}else{!$probe.Opened -and $probe.Win32 -eq 5 -and $probe.Closed}
   $rows+=[pscustomobject]@{Kind=$target[0];Path=$target[1];Right=$right[0];Mask=$right[1];Expected=$expected;Pass=$pass;Result=$probe}
  }
 }
}catch{$errorText=$_.Exception.Message}
finally{
 try{
  if($fileCreated){[IO.File]::Delete($file)}
  if($created){[IO.Directory]::Delete($dir,$false)}
  $cleanup=!(Test-Path -LiteralPath $dir)
 }catch{$errorText=([string]$errorText+'; cleanup: '+$_.Exception.Message)}
}
[pscustomobject]@{
 Check='G2_CURRENT_CHAIN_TARGETED_RUNTIME_ACL';Utc=[DateTime]::UtcNow.ToString('o')
 Sid=$id.User.Value;Session=$session;Chain=$chain
 OwnWorkspaceRoundtrip=$roundtrip;PositiveControls=$positive;Rows=$rows;Cleanup=$cleanup;Error=$errorText
 Passed=(!$errorText -and $roundtrip -and $cleanup -and $positive.Count -eq 12 -and $rows.Count -eq 64 -and @($rows|Where-Object {!$_.Pass}).Count -eq 0)
 Scope='8_SELECTED_RUNTIME_OBJECTS_64_OPEN_CLOSE_TESTS';SharedRuntimeContentWrites=0;AclWrites=0;OwnerPrivateContentReads=0;RuntimeRestarted=$false
}|ConvertTo-Json -Depth 7
