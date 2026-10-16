#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][int]$ExpectedGuestSession,[Parameter(Mandatory=$true)][string]$WorkerPath,[Parameter(Mandatory=$true)][int]$RuntimePid,[Parameter(Mandatory=$true)][int]$PythonPid,[Parameter(Mandatory=$true)][int]$NodePid)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
$session=[Diagnostics.Process]::GetCurrentProcess().SessionId
if($id.User.Value -ne 'S-1-5-21-303538662-3368424508-2654684973-1009' -or $session -ne $ExpectedGuestSession -or $session -le 0 -or @($id.Groups|Where-Object Value -eq 'S-1-5-32-544').Count){throw 'Exact ordinary guest session required'}
function Get-RealChain {
 $rows=@()
 foreach($pair in @(@($RuntimePid,'tunnel-client-runtime.exe'),@($PythonPid,'python.exe'),@($NodePid,'node.exe'))){
  $p=Get-CimInstance Win32_Process -Filter ('ProcessId='+$pair[0])
  if(!$p -or $p.Name -ne $pair[1] -or $p.SessionId -ne $session){throw 'Current G2 chain drift'}
  $o=Invoke-CimMethod -InputObject $p -MethodName GetOwnerSid
  if($o.ReturnValue -ne 0 -or $o.Sid -ne $id.User.Value){throw 'Current G2 SID mismatch'}
  $rows+=[pscustomobject]@{Pid=$p.ProcessId;Parent=$p.ParentProcessId;Name=$p.Name;Sid=$o.Sid;Session=$p.SessionId;CreatedUtc=$p.CreationDate.ToUniversalTime().ToString('o')}
 }
 if($rows[1].Parent -ne $RuntimePid -or $rows[2].Parent -ne $PythonPid){throw 'Current G2 ancestry mismatch'}
 return $rows
}
$before=Get-RealChain
$workspace=Join-Path $env:LOCALAPPDATA 'FortisHostG2\Workspace'
$WorkerPath=[IO.Path]::GetFullPath($WorkerPath)
if(!$WorkerPath.StartsWith($workspace+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Own workspace worker required'}
if((Get-FileHash -LiteralPath $WorkerPath -Algorithm SHA256).Hash -cne 'FB8FD7129213EDD9C3DB451E1A10E8291283738EFA457D4B9A0E20C82955E844'){throw 'Worker pin differs'}
$node='C:\Tools\desktop-commander-runtime\node.exe'
$runtime='C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe'
if((Get-FileHash -LiteralPath $node -Algorithm SHA256).Hash -cne '2FFE3ACC0458FDDE999F50D11809BBE7C9B7EF204DCF17094E325D26ACE101D8'){throw 'Node artifact drift'}
if((Get-FileHash -LiteralPath $runtime -Algorithm SHA256).Hash -cne 'A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A'){throw 'Runtime artifact drift'}
$native=@'
using System;
using System.Text;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.IO;
using System.Threading;
public static class FortisG2PeerFailureJob {
 [StructLayout(LayoutKind.Sequential)]
 struct Basic {public long PerProcessUserTimeLimit,PerJobUserTimeLimit;public uint Flags;public UIntPtr Minimum,Maximum;public uint Active;public UIntPtr Affinity;public uint Priority,Scheduling;}
 [StructLayout(LayoutKind.Sequential)]
 struct IO {public ulong ReadOps,WriteOps,OtherOps,ReadBytes,WriteBytes,OtherBytes;}
 [StructLayout(LayoutKind.Sequential)]
 struct Limits {public Basic Basic;public IO IO;public UIntPtr ProcessMemory,JobMemory,PeakProcess,PeakJob;}
 [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)]
 struct SI {public int cb;public string reserved,desktop,title;public uint x,y,xsize,ysize,xcount,ycount,fill,flags;public ushort show,reservedSize;public IntPtr reservedPtr,input,output,error;}
 [StructLayout(LayoutKind.Sequential)] struct PI {public IntPtr process,thread;public uint pid,tid;}
 [DllImport("kernel32.dll",SetLastError=true)] static extern IntPtr CreateJobObject(IntPtr a,string name);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetInformationJobObject(IntPtr job,int info,ref Limits limits,uint size);
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,EntryPoint="CreateProcessW",SetLastError=true)]
 static extern bool CreateProcess(string app,StringBuilder command,IntPtr pa,IntPtr ta,bool inherit,uint flags,IntPtr env,string cwd,ref SI si,out PI pi);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool AssignProcessToJobObject(IntPtr job,IntPtr process);
 [DllImport("kernel32.dll",SetLastError=true)] static extern uint ResumeThread(IntPtr thread);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool TerminateProcess(IntPtr process,uint code);
 [DllImport("kernel32.dll",SetLastError=true)] static extern uint WaitForSingleObject(IntPtr h,uint ms);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetExitCodeProcess(IntPtr h,out uint code);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool CloseHandle(IntPtr h);
 static void Check(bool ok,string stage){if(!ok)throw new Win32Exception(Marshal.GetLastWin32Error(),stage);}
 static string Q(string arg){return "\""+arg.Replace("\"","\\\"")+"\"";}

 [DllImport("kernel32.dll",SetLastError=true)] static extern bool TerminateJobObject(IntPtr job,uint code);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool QueryInformationJobObject(IntPtr job,int kind,IntPtr data,uint size,out uint returned);
 static int Active(IntPtr job){IntPtr data=Marshal.AllocHGlobal(48);uint returned;try{return QueryInformationJobObject(job,1,data,48,out returned)?Marshal.ReadInt32(data,40):-1;}finally{Marshal.FreeHGlobal(data);}}
 public static System.Collections.Generic.Dictionary<string,object> RunWorker(string executable,string script,string root,int timeoutMs){
  var r=new System.Collections.Generic.Dictionary<string,object>();
  IntPtr job=IntPtr.Zero,process=IntPtr.Zero,thread=IntPtr.Zero;bool assigned=false;uint exitCode=259;
  try{
   job=CreateJobObject(IntPtr.Zero,null);Check(job!=IntPtr.Zero,"CreateTestJob");
   var limit=new Limits();limit.Basic.Flags=0x2000;
   Check(SetInformationJobObject(job,9,ref limit,(uint)Marshal.SizeOf(typeof(Limits))),"SetTestJobKillOnClose");
   var si=new SI{cb=Marshal.SizeOf(typeof(SI))};PI pi;
   Check(CreateProcess(executable,new StringBuilder(Q(executable)+" "+Q(script)+" "+Q(root)),IntPtr.Zero,IntPtr.Zero,false,4,IntPtr.Zero,root,ref si,out pi),"CreateOwnNodeSuspended");
   process=pi.process;thread=pi.thread;r["NodePid"]=pi.pid;
   Check(AssignProcessToJobObject(job,process),"AssignOwnNodeToTestJob");assigned=true;r["Assigned"]=true;
   Check(ResumeThread(thread)!=UInt32.MaxValue,"ResumeOwnNode");CloseHandle(thread);thread=IntPtr.Zero;
   uint wait=WaitForSingleObject(process,(uint)timeoutMs);Check(wait!=UInt32.MaxValue,"WaitOwnNode");
   r["TimedOut"]=wait==258;Check(GetExitCodeProcess(process,out exitCode),"OwnNodeExitCode");r["ExitCode"]=exitCode;
  }finally{
   if(thread!=IntPtr.Zero)CloseHandle(thread);
   if(!assigned&&process!=IntPtr.Zero)TerminateProcess(process,91);
   if(job!=IntPtr.Zero){
    int before=Active(job);r["ActiveBeforeStop"]=before;
    r["TerminateRequested"]=assigned&&before!=0;
    if(assigned&&before!=0)r["TerminateSucceeded"]=TerminateJobObject(job,92);
    DateTime stop=DateTime.UtcNow.AddSeconds(5);int active=Active(job);
    while(active>0&&DateTime.UtcNow<stop){Thread.Sleep(100);active=Active(job);}
    r["ActiveAfterStop"]=active;r["JobClosed"]=CloseHandle(job);
   }
   if(process!=IntPtr.Zero){r["NodeStopped"]=WaitForSingleObject(process,5000)==0;CloseHandle(process);}
  }
  return r;
 }
}
'@
Add-Type -TypeDefinition $native
$root=Join-Path $workspace ('g2-peer-failure-'+[guid]::NewGuid().ToString('N'))
if(Test-Path -LiteralPath $root){throw 'Fixture path collision'}
$null=New-Item -ItemType Directory -Path $root
$marker=Join-Path $root 'fixture-owner.txt'
[IO.File]::WriteAllText($marker,'FORTIS_G2_SYNTHETIC_PEER_FAILURE')
$nativeResult=$null;$worker=$null;$failure=$null;$removed=$false;$portRows=@();$after=@()
try {
 $nativeResult=[FortisG2PeerFailureJob]::RunWorker($node,$WorkerPath,$root,45000)
 $resultPath=Join-Path $root 'worker-result.json'
 if(Test-Path -LiteralPath $resultPath){$worker=[IO.File]::ReadAllText($resultPath)|ConvertFrom-Json}
 if($null -ne $worker -and $worker.PSObject.Properties.Name -contains 'runtimePid'){
  $ports=@($worker.controlPort)
  if($worker.PSObject.Properties.Name -contains 'healthPort'){$ports+=@($worker.healthPort)}
  $portRows=@(Get-NetTCPConnection -State Listen -ErrorAction Stop|Where-Object {$_.LocalPort -in $ports}|Select-Object LocalAddress,LocalPort,OwningProcess)
 }
 $after=Get-RealChain
}catch{$failure=$_.Exception.Message}
finally {
 if($null -ne $nativeResult -and $nativeResult.ActiveAfterStop -eq 0 -and $nativeResult.NodeStopped -and $nativeResult.JobClosed){
  if([IO.File]::ReadAllText($marker) -cne 'FORTIS_G2_SYNTHETIC_PEER_FAILURE'){throw 'Own marker mismatch'}
  $items=@(Get-ChildItem -LiteralPath $root -Force -Recurse -ErrorAction Stop)
  if($items.Count -gt 128 -or ((Get-Item -LiteralPath $root).Attributes -band [IO.FileAttributes]::ReparsePoint) -or @($items|Where-Object {$_.Attributes -band [IO.FileAttributes]::ReparsePoint}).Count){throw 'Fixture cleanup scope requires inspection'}
  [IO.Directory]::Delete($root,$true)
  $removed=!(Test-Path -LiteralPath $root)
 }
}
$unchanged=($before|ConvertTo-Json -Compress) -ceq ($after|ConvertTo-Json -Compress)
$pass=$null -ne $worker -and $worker.pass -and !$failure -and $removed -and $unchanged -and $nativeResult.ExitCode -eq 0 -and !$nativeResult.TimedOut -and $nativeResult.ActiveBeforeStop -eq 0 -and $nativeResult.ActiveAfterStop -eq 0 -and $portRows.Count -eq 0
[pscustomobject]@{
 Check='G2_ISOLATED_MCP_PEER_FAILURE';Utc=[DateTime]::UtcNow.ToString('o');Sid=$id.User.Value;Session=$session
 WorkerSHA256='FB8FD7129213EDD9C3DB451E1A10E8291283738EFA457D4B9A0E20C82955E844'
 Native=$nativeResult;Worker=$worker;FixturePortRowsAfter=$portRows;RealChainBefore=$before;RealChainAfter=$after;RealChainUnchanged=$unchanged
 FixtureRemoved=$removed;RetainedRoot=if($removed){$null}else{$root};Passed=$pass;Error=$failure
 RealG2Stopped=$false;RealProfilesRead=$false;RealKeysUsed=$false;OwnerContentReads=0;RuntimeChanges=0;AclChanges=0
}|ConvertTo-Json -Depth 8
if(!$pass){throw 'Synthetic peer failure test did not pass; inspect result before any retry'}
