#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][int]$ExpectedGuestSession,[Parameter(Mandatory=$true)][string]$WorkerPath)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
$session=[Diagnostics.Process]::GetCurrentProcess().SessionId
if($id.User.Value -ne 'S-1-5-21-303538662-3368424508-2654684973-1009' -or $session -ne $ExpectedGuestSession -or $session -le 0 -or @($id.Groups|Where-Object Value -eq 'S-1-5-32-544').Count){throw 'Exact ordinary guest session required'}
$workspace=Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'FortisHostG2\Workspace'
$WorkerPath=[IO.Path]::GetFullPath($WorkerPath)
if(!$WorkerPath.StartsWith($workspace+'\',[StringComparison]::OrdinalIgnoreCase)){throw 'Own Workspace worker required'}
if((Get-FileHash -LiteralPath $WorkerPath -Algorithm SHA256).Hash -cne '16BCAE4F18441156C329EB586123414EE618B039EA95605DCDB109158B81A118'){throw 'Browser worker pin mismatch'}
$node='C:\Tools\desktop-commander-runtime\node.exe'
if((Get-FileHash -LiteralPath $node -Algorithm SHA256).Hash -cne '2FFE3ACC0458FDDE999F50D11809BBE7C9B7EF204DCF17094E325D26ACE101D8'){throw 'Node artifact drift'}
$edge='C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
if((Get-Item -LiteralPath $edge).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Edge reparse point refused'}
$native=@'
using System;
using System.Text;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.IO;
using System.Threading;
public static class FortisG2BrowserFunctionalJob {
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
$root=Join-Path $workspace ('g2-browser-functional-'+[guid]::NewGuid().ToString('N'))
if(Test-Path -LiteralPath $root){throw 'Own fixture root collision'}
$null=[IO.Directory]::CreateDirectory($root)
$marker=Join-Path $root 'fixture-owner.txt'
[IO.File]::WriteAllText($marker,'FORTIS_G2_SYNTHETIC_BROWSER')
$nativeResult=$null;$worker=$null;$failure=$null;$removed=$false
try{
 $nativeResult=[FortisG2BrowserFunctionalJob]::RunWorker($node,$WorkerPath,$root,50000)
 $out=Join-Path $root 'worker-result.json'
 if(Test-Path -LiteralPath $out){$worker=[IO.File]::ReadAllText($out)|ConvertFrom-Json}
}catch{$failure=$_.Exception.GetType().FullName}
finally{
 if($null -ne $nativeResult -and $nativeResult.ActiveAfterStop -eq 0 -and $nativeResult.NodeStopped -and $nativeResult.JobClosed){
  if([IO.File]::ReadAllText($marker) -cne 'FORTIS_G2_SYNTHETIC_BROWSER'){throw 'Own fixture marker mismatch'}
  if((Get-Item -LiteralPath $root).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Own fixture reparse point refused'}
  Remove-Item -LiteralPath $root -Recurse -Force
  $removed=!(Test-Path -LiteralPath $root)
 }
}
$passed=$null -ne $worker -and $worker.pass -and $removed -and !$failure -and $nativeResult.ExitCode -eq 0 -and !$nativeResult.TimedOut -and $nativeResult.ActiveAfterStop -eq 0
[pscustomobject]@{
 Check='G2_GUEST_BROWSER_FUNCTIONAL';Utc=[DateTime]::UtcNow.ToString('o');Sid=$id.User.Value;Session=$session
 WorkerSHA256='16BCAE4F18441156C329EB586123414EE618B039EA95605DCDB109158B81A118'
 Native=$nativeResult;Worker=$worker;ProfileAndScratchRemoved=$removed;RetainedRoot=if($removed){$null}else{$root}
 Passed=$passed;ErrorType=$failure;OwnerProfileRead=$false;BrowserSandboxDisabled=$false;G2Restarted=$false
}|ConvertTo-Json -Depth 6
if(!$passed){throw 'Own browser functional smoke did not pass; inspect JSON before retry'}
