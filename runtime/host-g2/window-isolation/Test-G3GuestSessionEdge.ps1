# G3 local guest Session 3 Edge synthetic startup only; no owner artifacts.
# Run strictly as SID1009 in Session 3, ordinary non-elevated PowerShell.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$expectedSid='S-1-5-21-303538662-3368424508-2654684973-1009'
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
$session=[Diagnostics.Process]::GetCurrentProcess().SessionId
$admin=(New-Object Security.Principal.WindowsPrincipal($id)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if($id.User.Value -ne $expectedSid -or $session -ne 3 -or $admin){throw 'Exact non-admin SID1009 in Session 3 required'}
if('FortisG3GuestEdgeJob' -as [type]){throw 'Use a fresh guest PowerShell process'}
$edgeCandidates=@('C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe','C:\Program Files\Microsoft\Edge\Application\msedge.exe')
$edge=$edgeCandidates|Where-Object{Test-Path -LiteralPath $_ -PathType Leaf}|Select-Object -First 1
if(!$edge){throw 'Installed Edge executable not found'}
if((Get-Item -LiteralPath $edge).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Edge executable reparse point refused'}
$root=Join-Path ([IO.Path]::GetTempPath()) ('FortisG3Edge-'+[Guid]::NewGuid().ToString('N'))
if(Test-Path -LiteralPath $root){throw 'Unexpected scratch collision'}
$null=New-Item -ItemType Directory -Path $root
$profile=Join-Path $root 'profile'
$native=@'
using System;
using System.Text;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.IO;
using System.Threading;
public static class FortisG3GuestEdgeJob {
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
 public static string Run(string executable,string profile,string workingDirectory,int timeoutMs){
  IntPtr job=IntPtr.Zero,process=IntPtr.Zero,thread=IntPtr.Zero;bool assigned=false;
  bool devtools=false,stopped=true,earlyExit=false;uint pid=0,exitCode=259;
  try{
   job=CreateJobObject(IntPtr.Zero,null);Check(job!=IntPtr.Zero,"CreateJobObject");
   var limit=new Limits();limit.Basic.Flags=0x2000; // JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
   Check(SetInformationJobObject(job,9,ref limit,(uint)Marshal.SizeOf(typeof(Limits))),"SetJobKillOnClose");
   string args="--headless=new --no-first-run --no-default-browser-check --disable-background-networking --disable-extensions --disable-sync --remote-debugging-address=127.0.0.1 --remote-debugging-port=0 --user-data-dir="+Q(profile)+" about:blank";
   var si=new SI{cb=Marshal.SizeOf(typeof(SI))};PI pi;
   Check(CreateProcess(executable,new StringBuilder(Q(executable)+" "+args),IntPtr.Zero,IntPtr.Zero,false,0x00000004,IntPtr.Zero,workingDirectory,ref si,out pi),"CreateEdgeSuspended");
   process=pi.process;thread=pi.thread;pid=pi.pid;
   Check(AssignProcessToJobObject(job,process),"AssignEdgeToKillOnCloseJob");assigned=true;
   Check(ResumeThread(thread)!=UInt32.MaxValue,"ResumeEdge");
   CloseHandle(thread);thread=IntPtr.Zero;
   DateTime deadline=DateTime.UtcNow.AddMilliseconds(timeoutMs);
   string portFile=Path.Combine(profile,"DevToolsActivePort");
   while(DateTime.UtcNow<deadline){
    if(File.Exists(portFile)){devtools=true;break;}
    if(WaitForSingleObject(process,0)==0){earlyExit=true;GetExitCodeProcess(process,out exitCode);break;}
    Thread.Sleep(200);
   }
  }finally{
   if(thread!=IntPtr.Zero)CloseHandle(thread);
   if(!assigned && process!=IntPtr.Zero)TerminateProcess(process,91);
   if(job!=IntPtr.Zero)CloseHandle(job); // kills every child attached to job
   if(process!=IntPtr.Zero){stopped=WaitForSingleObject(process,10000)==0;CloseHandle(process);}
  }
  return "CDP="+devtools+";Stopped="+stopped+";EarlyExit="+earlyExit+";ExitCode="+exitCode+";Assigned="+assigned+";Pid="+pid;
 }
}
'@
$runResult=$null;$profileRemoved=$false;$failureType=$null;$failureMessage=$null
try {
 Add-Type -TypeDefinition $native -ErrorAction Stop
 $runResult=[FortisG3GuestEdgeJob]::Run($edge,$profile,$root,20000)
} catch {
 $failureType=$_.Exception.GetType().FullName
 $failureMessage=$_.Exception.Message
} finally {
 try {
  if(Test-Path -LiteralPath $root){
   if((Get-Item -LiteralPath $root).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Scratch reparse point: manual review required'}
   Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction Stop
  }
  $profileRemoved=!(Test-Path -LiteralPath $root)
 } catch {
  $profileRemoved=$false
  $failureType=$_.Exception.GetType().FullName
  $failureMessage='Scratch cleanup failed; manual review required'
 }
}
$cdp=$runResult -match 'CDP=True'
$stopped=$runResult -match 'Stopped=True'
$testStatus=if($cdp -and $stopped -and $profileRemoved -and !$failureType){'PASS'}else{'FAIL'}
[pscustomobject]@{
 Sid=$id.User.Value;Session=$session;Admin=$admin
 EdgeStartup=$cdp;JobStopped=$stopped;ProfileRemoved=$profileRemoved
 Result=$testStatus
 NativeResult=$runResult;ErrorType=$failureType;ErrorMessage=$failureMessage
 Scope='Guest Session 3 own about:blank CDP file only; no owner objects or clipboard/screen'
}|ConvertTo-Json -Compress -Depth 3
