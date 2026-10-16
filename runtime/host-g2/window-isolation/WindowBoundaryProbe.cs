using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text;
public static class G2WindowBoundary {
 [StructLayout(LayoutKind.Sequential)] struct SA {public int Length;public IntPtr Descriptor;public int Inherit;}
 [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)] struct SI {public int cb;public string reserved,desktop,title;public uint x,y,xsize,ysize,xcount,ycount,fill,flags;public ushort show,reservedSize;public IntPtr reservedPtr,input,output,error;}
 [StructLayout(LayoutKind.Sequential)] struct PI {public IntPtr process,thread;public uint pid,tid;}
 [StructLayout(LayoutKind.Sequential)] struct Mapping {public uint Read,Write,Execute,All;}
 [StructLayout(LayoutKind.Sequential)] struct UserFlags {public int Inherit,Reserved;public uint Flags;}
 [StructLayout(LayoutKind.Sequential)] struct BasicLimits {public long ProcessTime,JobTime;public uint Flags;public UIntPtr Minimum,Maximum;public uint Active;public UIntPtr Affinity;public uint Priority,Scheduling;}
 [StructLayout(LayoutKind.Sequential)] struct IOCounters {public ulong ReadOps,WriteOps,OtherOps,ReadBytes,WriteBytes,OtherBytes;}
 [StructLayout(LayoutKind.Sequential)] struct JobLimits {public BasicLimits Basic;public IOCounters IO;public UIntPtr ProcessMemory,JobMemory,PeakProcess,PeakJob;}
 [DllImport("kernel32.dll",SetLastError=true)] static extern IntPtr CreateJobObject(IntPtr sa,string name);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetInformationJobObject(IntPtr job,int info,ref JobLimits limits,uint size);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool AssignProcessToJobObject(IntPtr job,IntPtr process);
 [DllImport("kernel32.dll",SetLastError=true)] static extern uint ResumeThread(IntPtr thread);
 [DllImport("user32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern IntPtr CreateWindowStation(string name,uint flags,uint access,ref SA sa);
 [DllImport("user32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern IntPtr CreateDesktop(string name,IntPtr device,IntPtr mode,uint flags,uint access,ref SA sa);
 [DllImport("user32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern IntPtr OpenWindowStation(string name,bool inherit,uint access);
 [DllImport("user32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern IntPtr OpenDesktop(string name,uint flags,bool inherit,uint access);
 [DllImport("user32.dll",SetLastError=true)] static extern bool CloseWindowStation(IntPtr h);
 [DllImport("user32.dll",SetLastError=true)] static extern bool CloseDesktop(IntPtr h);
 [DllImport("user32.dll")] public static extern IntPtr GetProcessWindowStation();
 [DllImport("user32.dll")] static extern IntPtr GetThreadDesktop(uint id);
 [DllImport("kernel32.dll")] static extern uint GetCurrentThreadId();
 [DllImport("user32.dll",SetLastError=true)] static extern bool SetProcessWindowStation(IntPtr h);
 [DllImport("user32.dll",SetLastError=true)] static extern bool SetThreadDesktop(IntPtr h);
 [DllImport("user32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool GetUserObjectInformation(IntPtr h,int what,IntPtr value,uint length,out uint needed);
 [DllImport("user32.dll",SetLastError=true)] static extern bool GetUserObjectSecurity(IntPtr h,ref uint info,IntPtr value,uint length,out uint needed);
 [DllImport("user32.dll",SetLastError=true)] static extern bool SetUserObjectSecurity(IntPtr h,ref uint info,byte[] value);
 [DllImport("advapi32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool ConvertStringSecurityDescriptorToSecurityDescriptor(string value,uint rev,out IntPtr sd,out uint size);
 [DllImport("advapi32.dll",SetLastError=true)] static extern bool DuplicateToken(IntPtr token,int level,out IntPtr duplicate);
 [DllImport("advapi32.dll",SetLastError=true)] static extern bool AccessCheck(IntPtr sd,IntPtr token,uint access,ref Mapping mapping,IntPtr privileges,ref uint size,out uint granted,out bool allowed);
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool CreateProcess(string app,StringBuilder cmd,IntPtr pa,IntPtr ta,bool inherit,uint flags,IntPtr env,string cwd,ref SI si,out PI pi);
 [DllImport("kernel32.dll")] static extern uint WaitForSingleObject(IntPtr h,uint ms);
 [DllImport("kernel32.dll")] static extern bool GetExitCodeProcess(IntPtr h,out uint code);
 [DllImport("kernel32.dll")] static extern bool TerminateProcess(IntPtr h,uint code);
 [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
 [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr h);
 static IntPtr ownStation,ownDesktop,previousStation,previousDesktop;
 static byte[] stationBefore,desktopBefore;
 public static IntPtr DesktopHandle(){return GetThreadDesktop(GetCurrentThreadId());}
 static void Check(bool ok){if(!ok)throw new Win32Exception(Marshal.GetLastWin32Error());}
 public static string Name(IntPtr h){uint n;GetUserObjectInformation(h,2,IntPtr.Zero,0,out n);IntPtr b=Marshal.AllocHGlobal((int)n);try{Check(GetUserObjectInformation(h,2,b,n,out n));return Marshal.PtrToStringUni(b);}finally{Marshal.FreeHGlobal(b);}}
 public static bool Visible(IntPtr h){uint n;IntPtr b=Marshal.AllocHGlobal(Marshal.SizeOf(typeof(UserFlags)));try{Check(GetUserObjectInformation(h,1,b,(uint)Marshal.SizeOf(typeof(UserFlags)),out n));return (((UserFlags)Marshal.PtrToStructure(b,typeof(UserFlags))).Flags&1)!=0;}finally{Marshal.FreeHGlobal(b);}}
 public static byte[] Read(IntPtr h){uint info=7,n;GetUserObjectSecurity(h,ref info,IntPtr.Zero,0,out n);IntPtr b=Marshal.AllocHGlobal((int)n);try{Check(GetUserObjectSecurity(h,ref info,b,n,out n));byte[] bytes=new byte[n];Marshal.Copy(b,bytes,0,(int)n);return bytes;}finally{Marshal.FreeHGlobal(b);}}
 public static string Sddl(IntPtr h){return new RawSecurityDescriptor(Read(h),0).GetSddlForm(AccessControlSections.All);}
 public static byte[] Deny(byte[] before,string sid,int mask,bool suppressOwnerRights){
  var sd=new RawSecurityDescriptor(before,0);if(sd.DiscretionaryAcl==null)throw new InvalidOperationException("NULL DACL requires separate review");
  sd.DiscretionaryAcl.InsertAce(0,new CommonAce(AceFlags.None,AceQualifier.AccessDenied,mask,new SecurityIdentifier(sid),false,null));
  if(suppressOwnerRights)sd.DiscretionaryAcl.InsertAce(1,new CommonAce(AceFlags.None,AceQualifier.AccessAllowed,0x20000,new SecurityIdentifier("S-1-3-4"),false,null));
  byte[] bytes=new byte[sd.BinaryLength];sd.GetBinaryForm(bytes,0);return bytes;
 }
 public static void Set(IntPtr h,byte[] sd){uint info=4;Check(SetUserObjectSecurity(h,ref info,sd));}
 public static string Access(byte[] sd,uint right,bool desktop){
  IntPtr d=Marshal.AllocHGlobal(sd.Length),token=IntPtr.Zero,priv=IntPtr.Zero;
  try{Marshal.Copy(sd,0,d,sd.Length);Check(DuplicateToken(WindowsIdentity.GetCurrent().Token,2,out token));uint n=4096,granted;bool allowed;priv=Marshal.AllocHGlobal((int)n);
   Mapping m=desktop?new Mapping{Read=0x20041,Write=0x200be,Execute=0x20100,All=0xf01ff}:new Mapping{Read=0x20303,Write=0x2001c,Execute=0x20060,All=0xf037f};
   Check(AccessCheck(d,token,right,ref m,priv,ref n,out granted,out allowed));return allowed?"ALLOW":"DENY";
  }finally{Marshal.FreeHGlobal(d);if(priv!=IntPtr.Zero)Marshal.FreeHGlobal(priv);if(token!=IntPtr.Zero)CloseHandle(token);}
 }
 public static string CreatePrivate(string sid){
  if(ownStation!=IntPtr.Zero)throw new InvalidOperationException("Already created");
  previousStation=GetProcessWindowStation();previousDesktop=DesktopHandle();IntPtr sd=IntPtr.Zero;uint n;
  try{
   Check(ConvertStringSecurityDescriptorToSecurityDescriptor("D:P(A;;0xf037f;;;SY)(A;;0xf037f;;;"+sid+")",1,out sd,out n));
   SA sa=new SA{Length=Marshal.SizeOf(typeof(SA)),Descriptor=sd,Inherit=0};
   ownStation=CreateWindowStation(null,1,0xf037f,ref sa);Check(ownStation!=IntPtr.Zero);
   if(Name(ownStation).Equals("WinSta0",StringComparison.OrdinalIgnoreCase)||Visible(ownStation))throw new InvalidOperationException("Refuse interactive object");
   Check(SetProcessWindowStation(ownStation));
   LocalFree(sd);sd=IntPtr.Zero;
   Check(ConvertStringSecurityDescriptorToSecurityDescriptor("D:P(A;;0xf01ff;;;SY)(A;;0xf01ff;;;"+sid+")",1,out sd,out n));
   sa.Descriptor=sd;ownDesktop=CreateDesktop("default",IntPtr.Zero,IntPtr.Zero,0,0xf01ff,ref sa);Check(ownDesktop!=IntPtr.Zero);
   stationBefore=Read(ownStation);desktopBefore=Read(ownDesktop);
   return Name(ownStation);
  }finally{if(sd!=IntPtr.Zero)LocalFree(sd);if(previousStation!=IntPtr.Zero)Check(SetProcessWindowStation(previousStation));if(DesktopHandle()!=previousDesktop)Check(SetThreadDesktop(previousDesktop));}
 }
 public static string Quote(string s){
  var b=new StringBuilder("\"");int slash=0;
  foreach(char c in s){if(c=='\\'){slash++;continue;}b.Append('\\',c=='"'?slash*2+1:slash);b.Append(c);slash=0;}
  b.Append('\\',slash*2);return b.Append('"').ToString();
 }
 public static uint Child(string app,string command,string cwd,uint timeout){
  if(ownStation==IntPtr.Zero||ownDesktop==IntPtr.Zero)throw new InvalidOperationException("No private objects");
  IntPtr job=CreateJobObject(IntPtr.Zero,null);Check(job!=IntPtr.Zero);PI pi=new PI();bool assigned=false;
  try{
   JobLimits limits=new JobLimits();limits.Basic.Flags=0x2000;Check(SetInformationJobObject(job,9,ref limits,(uint)Marshal.SizeOf(typeof(JobLimits))));
   SI si=new SI{cb=Marshal.SizeOf(typeof(SI)),desktop=Name(ownStation)+"\\default"};
   Check(CreateProcess(app,new StringBuilder(command),IntPtr.Zero,IntPtr.Zero,false,0x08000004,IntPtr.Zero,cwd,ref si,out pi));
   Check(AssignProcessToJobObject(job,pi.process));assigned=true;Check(ResumeThread(pi.thread)!=0xffffffff);CloseHandle(pi.thread);pi.thread=IntPtr.Zero;
   uint wait=WaitForSingleObject(pi.process,timeout);if(wait==258){CloseHandle(job);job=IntPtr.Zero;WaitForSingleObject(pi.process,10000);throw new TimeoutException("Own child timeout");}
   if(wait!=0)throw new Win32Exception(Marshal.GetLastWin32Error());uint code;Check(GetExitCodeProcess(pi.process,out code));return code;
  }finally{
   if(!assigned&&pi.process!=IntPtr.Zero){TerminateProcess(pi.process,91);WaitForSingleObject(pi.process,10000);}if(job!=IntPtr.Zero)CloseHandle(job);if(pi.thread!=IntPtr.Zero)CloseHandle(pi.thread);if(pi.process!=IntPtr.Zero)CloseHandle(pi.process);
  }
 }
 public static int StationOpen(string name,uint right){IntPtr h=OpenWindowStation(name,false,right);if(h==IntPtr.Zero)return Marshal.GetLastWin32Error();CloseWindowStation(h);return 0;}
 public static int DesktopOpen(uint right){IntPtr h=OpenDesktop("default",0,false,right);if(h==IntPtr.Zero)return Marshal.GetLastWin32Error();CloseDesktop(h);return 0;}
 public static int[] SyntheticDeny(string sid){
  if(ownStation==IntPtr.Zero||Name(ownStation).Equals("WinSta0",StringComparison.OrdinalIgnoreCase))throw new InvalidOperationException("Own object required");
  try{
   Set(ownStation,Deny(stationBefore,sid,0xf037f,true));Set(ownDesktop,Deny(desktopBefore,sid,0xf01ff,true));
   string name=Name(ownStation);int[] result=new int[9];uint[] rights={4,512,0x40000,0x80000};for(int i=0;i<4;i++)result[i]=StationOpen(name,rights[i]);
   Check(SetProcessWindowStation(ownStation));uint[] desktopRights={1,8,256,0x40081,0x80081};for(int i=0;i<5;i++)result[i+4]=DesktopOpen(desktopRights[i]);return result;
  }finally{Set(ownDesktop,desktopBefore);Set(ownStation,stationBefore);Check(SetProcessWindowStation(previousStation));}
 }
 public static bool Cleanup(){
  if(previousStation!=IntPtr.Zero)Check(SetProcessWindowStation(previousStation));
  if(previousDesktop!=IntPtr.Zero&&DesktopHandle()!=previousDesktop)Check(SetThreadDesktop(previousDesktop));
  bool ok=true;if(ownDesktop!=IntPtr.Zero){ok=CloseDesktop(ownDesktop)&&ok;ownDesktop=IntPtr.Zero;}
  if(ownStation!=IntPtr.Zero){ok=CloseWindowStation(ownStation)&&ok;ownStation=IntPtr.Zero;}return ok;
 }
}
