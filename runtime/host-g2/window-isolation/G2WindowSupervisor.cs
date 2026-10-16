using System;
using System.Collections;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security;
using System.Security.Principal;
using System.Text;
public sealed class G2WindowSupervisor : IDisposable {
 [StructLayout(LayoutKind.Sequential)] struct SA {public int Length;public IntPtr Descriptor;public int Inherit;}
 [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)] struct SI {public int cb;public string reserved,desktop,title;public uint x,y,xsize,ysize,xcount,ycount,fill,flags;public ushort show,reservedSize;public IntPtr reservedPtr,input,output,error;}
 [StructLayout(LayoutKind.Sequential)] struct PI {public IntPtr process,thread;public uint pid,tid;}
 [StructLayout(LayoutKind.Sequential)] struct Basic {public long ProcessTime,JobTime;public uint Flags;public UIntPtr Minimum,Maximum;public uint Active;public UIntPtr Affinity;public uint Priority,Scheduling;}
 [StructLayout(LayoutKind.Sequential)] struct IO {public ulong ReadOps,WriteOps,OtherOps,ReadBytes,WriteBytes,OtherBytes;}
 [StructLayout(LayoutKind.Sequential)] struct Limits {public Basic Basic;public IO IO;public UIntPtr ProcessMemory,JobMemory,PeakProcess,PeakJob;}
 [DllImport("user32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern IntPtr CreateWindowStation(string name,uint flags,uint access,ref SA sa);
 [DllImport("user32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern IntPtr CreateDesktop(string name,IntPtr device,IntPtr mode,uint flags,uint access,ref SA sa);
 [DllImport("user32.dll",SetLastError=true)] static extern bool SetProcessWindowStation(IntPtr h);
 [DllImport("user32.dll",SetLastError=true)] static extern bool SetThreadDesktop(IntPtr h);
 [DllImport("user32.dll",SetLastError=true)] static extern bool CloseWindowStation(IntPtr h);
 [DllImport("user32.dll",SetLastError=true)] static extern bool CloseDesktop(IntPtr h);
 [DllImport("advapi32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool ConvertStringSecurityDescriptorToSecurityDescriptor(string s,uint revision,out IntPtr sd,out uint n);
 [DllImport("kernel32.dll",SetLastError=true)] static extern IntPtr CreateJobObject(IntPtr sa,string name);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetInformationJobObject(IntPtr job,int kind,ref Limits limits,uint size);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool AssignProcessToJobObject(IntPtr job,IntPtr process);
 [DllImport("kernel32.dll",SetLastError=true)] static extern uint ResumeThread(IntPtr thread);
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool CreateProcess(string app,StringBuilder cmd,IntPtr pa,IntPtr ta,bool inherit,uint flags,IntPtr env,string cwd,ref SI si,out PI pi);
 [DllImport("advapi32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool CreateProcessWithLogonW(string user,string domain,IntPtr password,uint logonFlags,string app,StringBuilder command,uint flags,IntPtr env,string cwd,ref SI si,out PI pi);
 [DllImport("advapi32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool LogonUser(string user,string domain,IntPtr password,uint type,uint provider,out IntPtr token);
 [DllImport("advapi32.dll",SetLastError=true)] static extern bool OpenProcessToken(IntPtr process,uint access,out IntPtr token);
 [DllImport("advapi32.dll",SetLastError=true)] static extern bool GetTokenInformation(IntPtr token,int kind,IntPtr buffer,uint length,out uint returned);
 [StructLayout(LayoutKind.Sequential)] struct SidAttributes {public IntPtr Sid;public uint Attributes;}
 [StructLayout(LayoutKind.Sequential)] struct Luid {public uint Low;public int High;}
 [StructLayout(LayoutKind.Sequential)] struct TokenPrivilege {public uint Count;public Luid Luid;public uint Attributes;}
 [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
 [DllImport("advapi32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool LookupPrivilegeValue(string system,string name,out Luid luid);
 [DllImport("advapi32.dll",SetLastError=true)] static extern bool AdjustTokenPrivileges(IntPtr token,bool disableAll,ref TokenPrivilege state,uint size,out TokenPrivilege previous,out uint returned);
 [DllImport("advapi32.dll",EntryPoint="AdjustTokenPrivileges",SetLastError=true)] static extern bool RestoreTokenPrivileges(IntPtr token,bool disableAll,ref TokenPrivilege state,uint size,IntPtr previous,IntPtr returned);
 [DllImport("kernel32.dll",SetLastError=true)] static extern uint WaitForSingleObject(IntPtr h,uint ms);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetExitCodeProcess(IntPtr h,out uint code);
 [DllImport("kernel32.dll")] static extern bool TerminateProcess(IntPtr h,uint code);
 [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
 [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr h);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetNamedPipeClientProcessId(IntPtr pipe,out uint pid);
 public static uint PipeClientPid(System.IO.Pipes.NamedPipeServerStream pipe){uint pid;Check(GetNamedPipeClientProcessId(pipe.SafePipeHandle.DangerousGetHandle(),out pid));return pid;}
 IntPtr station,desktop,job,process;
 public string StationName {get;private set;}
 public uint ProcessId {get;private set;}
 public IntPtr StationHandle {get{return station;}}
 public IntPtr DesktopHandle {get{return desktop;}}
 static void Check(bool ok){Check(ok,"Win32 operation");}
 static void Check(bool ok,string stage){if(!ok){int code=Marshal.GetLastWin32Error();throw new Win32Exception(code,stage+" failed (Win32 "+code+")");}}
 sealed class DebugPrivilegeScope : IDisposable {
  IntPtr callerToken;TokenPrivilege previous;bool changed;
  public DebugPrivilegeScope(bool enable){
   if(!enable)return;
   try{
    Check(OpenProcessToken(GetCurrentProcess(),40,out callerToken),"Attach/OpenCallerToken");
    Luid luid;Check(LookupPrivilegeValue(null,"SeDebugPrivilege",out luid),"Attach/LookupSeDebugPrivilege");
    TokenPrivilege request=new TokenPrivilege{Count=1,Luid=luid,Attributes=2};uint returned;
    bool ok=AdjustTokenPrivileges(callerToken,false,ref request,(uint)Marshal.SizeOf(typeof(TokenPrivilege)),out previous,out returned);
    int code=Marshal.GetLastWin32Error();changed=ok&&previous.Count!=0;
    if(!ok||code!=0)throw new Win32Exception(code,"Attach/EnableSeDebugPrivilege failed (Win32 "+code+")");
   }catch{Dispose();throw;}
  }
  public void Dispose(){
   if(callerToken==IntPtr.Zero)return;
   try{if(changed){bool ok=RestoreTokenPrivileges(callerToken,false,ref previous,0,IntPtr.Zero,IntPtr.Zero);int code=Marshal.GetLastWin32Error();if(!ok||code!=0)throw new Win32Exception(code,"Attach/RestoreSeDebugPrivilege failed (Win32 "+code+")");}}
   finally{CloseHandle(callerToken);callerToken=IntPtr.Zero;changed=false;}
  }
 }
 static IntPtr TokenBuffer(IntPtr token,int kind,out uint size){
  bool sized=GetTokenInformation(token,kind,IntPtr.Zero,0,out size);int code=Marshal.GetLastWin32Error();
  if(!sized&&code!=122)throw new Win32Exception(code,"Verify/GetTokenInformation size class "+kind+" failed (Win32 "+code+")");
  if(size<4||size>1048576)throw new InvalidOperationException("Invalid token metadata size");
  IntPtr buffer=Marshal.AllocHGlobal((int)size);
  try{uint actual;Check(GetTokenInformation(token,kind,buffer,size,out actual),"Verify/GetTokenInformation class "+kind);if(actual>size)throw new InvalidOperationException("Token metadata size changed");size=actual;return buffer;}
  catch{Marshal.FreeHGlobal(buffer);throw;}
 }
 static uint TokenUInt(IntPtr token,int kind){IntPtr b=Marshal.AllocHGlobal(4);try{uint size;Check(GetTokenInformation(token,kind,b,4,out size),"Verify/GetTokenInformation DWORD class "+kind);if(size!=4)throw new InvalidOperationException("Unexpected DWORD token metadata size");return (uint)Marshal.ReadInt32(b);}finally{Marshal.FreeHGlobal(b);}}
 static void VerifyIdentity(IntPtr token,string sid,bool requireStandard){
  uint size;IntPtr b=TokenBuffer(token,1,out size);
  try{if(size<IntPtr.Size)throw new InvalidOperationException("Truncated token user");if(new SecurityIdentifier(Marshal.ReadIntPtr(b)).Value!=sid)throw new InvalidOperationException("Wrong target SID");}
  finally{Marshal.FreeHGlobal(b);}
  if(!requireStandard)return;
  if(TokenUInt(token,20)!=0)throw new InvalidOperationException("Target must be non-admin: elevated token");
  b=TokenBuffer(token,2,out size);
  try{
   uint count=(uint)Marshal.ReadInt32(b);int offset=IntPtr.Size==8?8:4,stride=Marshal.SizeOf(typeof(SidAttributes));
   if(offset+(long)count*stride>size)throw new InvalidOperationException("Truncated token groups");
   for(uint i=0;i<count;i++){
    var group=(SidAttributes)Marshal.PtrToStructure(IntPtr.Add(b,offset+(int)i*stride),typeof(SidAttributes));
    if(new SecurityIdentifier(group.Sid).IsWellKnown(WellKnownSidType.BuiltinAdministratorsSid))throw new InvalidOperationException("Target must be non-admin: Administrators membership");
   }
  }finally{Marshal.FreeHGlobal(b);}
 }
 public static void ValidateAccount(string user,string domain,SecureString password,string sid){
  IntPtr p=IntPtr.Zero,t=IntPtr.Zero;
  try{p=Marshal.SecureStringToGlobalAllocUnicode(password);Check(LogonUser(user,domain,p,2,0,out t));VerifyIdentity(t,sid,true);}
  finally{if(t!=IntPtr.Zero)CloseHandle(t);if(p!=IntPtr.Zero)Marshal.ZeroFreeGlobalAllocUnicode(p);}
 }
 // Full guest access is confined to these new private objects: Chromium clones
 // their ACLs for sandbox desktops. The owner WinSta0/default deny is separate.
 public G2WindowSupervisor(string ownerSid,string guestSid,bool named){
  if(WindowsIdentity.GetCurrent().User.Value!=ownerSid)throw new InvalidOperationException("Owner identity required");
  IntPtr oldStation=G2WindowBoundary.GetProcessWindowStation(),oldDesktop=G2WindowBoundary.DesktopHandle(),sd=IntPtr.Zero;uint n;
  try{
   Check(ConvertStringSecurityDescriptorToSecurityDescriptor("D:P(A;;0xf037f;;;SY)(A;;0xf037f;;;"+ownerSid+")(A;;0xf037f;;;"+guestSid+")",1,out sd,out n));
   SA sa=new SA{Length=Marshal.SizeOf(typeof(SA)),Descriptor=sd,Inherit=0};
   station=CreateWindowStation(named?"FortisG2-"+Guid.NewGuid().ToString("N"):null,1,0xf037f,ref sa);Check(station!=IntPtr.Zero);
   StationName=G2WindowBoundary.Name(station);
   if(StationName.Equals("WinSta0",StringComparison.OrdinalIgnoreCase)||G2WindowBoundary.Visible(station))throw new InvalidOperationException("Interactive object refused");
   Check(SetProcessWindowStation(station));LocalFree(sd);sd=IntPtr.Zero;
   Check(ConvertStringSecurityDescriptorToSecurityDescriptor("D:P(A;;0xf01ff;;;SY)(A;;0xf01ff;;;"+ownerSid+")(A;;0xf01ff;;;"+guestSid+")",1,out sd,out n));
   sa.Descriptor=sd;desktop=CreateDesktop("default",IntPtr.Zero,IntPtr.Zero,0,0xf01ff,ref sa);Check(desktop!=IntPtr.Zero);
  }catch{SetProcessWindowStation(oldStation);if(G2WindowBoundary.DesktopHandle()!=oldDesktop)SetThreadDesktop(oldDesktop);Dispose();throw;}
  finally{if(sd!=IntPtr.Zero)LocalFree(sd);Check(SetProcessWindowStation(oldStation));if(G2WindowBoundary.DesktopHandle()!=oldDesktop)Check(SetThreadDesktop(oldDesktop));}
 }
 static IntPtr EnvironmentBlock(IDictionary source,SecureString key,out int bytes){
  var names=new List<string>();foreach(DictionaryEntry e in source){string n=(string)e.Key,v=(string)e.Value;if(n.IndexOfAny(new char[]{'=','\0'})>=0||v.IndexOf('\0')>=0)throw new InvalidOperationException("Invalid environment");names.Add(n);}
  if(names.Exists(n=>n.Equals("CONTROL_PLANE_API_KEY",StringComparison.OrdinalIgnoreCase)))throw new InvalidOperationException("Ambient key refused");
  if(key!=null)names.Add("CONTROL_PLANE_API_KEY");names.Sort(StringComparer.OrdinalIgnoreCase);
  int chars=1;foreach(string n in names)chars+=n.Length+1+(n=="CONTROL_PLANE_API_KEY"?key.Length:((string)source[n]).Length)+1;
  bytes=checked(chars*2);IntPtr b=Marshal.AllocHGlobal(bytes),secret=IntPtr.Zero;int index=0;
  try{
   if(key!=null)secret=Marshal.SecureStringToGlobalAllocUnicode(key);
   foreach(string n in names){
    foreach(char c in n+"=")Marshal.WriteInt16(b,index++*2,(short)c);
    if(n=="CONTROL_PLANE_API_KEY"){for(int i=0;i<key.Length;i++)Marshal.WriteInt16(b,index++*2,Marshal.ReadInt16(secret,i*2));}
    else foreach(char c in (string)source[n])Marshal.WriteInt16(b,index++*2,(short)c);
    Marshal.WriteInt16(b,index++*2,0);
   }
   Marshal.WriteInt16(b,index++*2,0);return b;
  }catch{ClearFree(b,bytes);throw;}finally{if(secret!=IntPtr.Zero)Marshal.ZeroFreeGlobalAllocUnicode(secret);}
 }
 static void ClearFree(IntPtr p,int n){if(p==IntPtr.Zero)return;for(int i=0;i<n;i++)Marshal.WriteByte(p,i,0);Marshal.FreeHGlobal(p);}
 void Attach(PI pi,string expectedSid,bool standard){
  process=pi.process;ProcessId=pi.pid;IntPtr token=IntPtr.Zero;bool assigned=false;
  try{
   using(var debug=new DebugPrivilegeScope(expectedSid!=WindowsIdentity.GetCurrent().User.Value)){
    Check(OpenProcessToken(process,8,out token),"Attach/OpenProcessToken(TOKEN_QUERY)");VerifyIdentity(token,expectedSid,standard);
    if(TokenUInt(token,8)!=1)throw new InvalidOperationException("Target token must be primary");
    if(TokenUInt(token,12)!=(uint)Process.GetCurrentProcess().SessionId)throw new InvalidOperationException("Wrong target session");
   }
   job=CreateJobObject(IntPtr.Zero,null);Check(job!=IntPtr.Zero,"Attach/CreateJobObject");Limits limits=new Limits();limits.Basic.Flags=0x2000;
   Check(SetInformationJobObject(job,9,ref limits,(uint)Marshal.SizeOf(typeof(Limits))),"Attach/SetInformationJobObject");Check(AssignProcessToJobObject(job,process),"Attach/AssignProcessToJobObject");assigned=true;
   Check(ResumeThread(pi.thread)!=0xffffffff,"Attach/ResumeThread");
  }catch{if(!assigned)TerminateProcess(process,92);Dispose();throw;}
  finally{if(token!=IntPtr.Zero)CloseHandle(token);if(pi.thread!=IntPtr.Zero)CloseHandle(pi.thread);}
 }
 public uint StartOwner(string app,string command,string cwd,IDictionary env,SecureString syntheticKey){
  if(process!=IntPtr.Zero)throw new InvalidOperationException("Child already started");
  IntPtr block=IntPtr.Zero;int size=0;PI pi;SI si=new SI{cb=Marshal.SizeOf(typeof(SI)),desktop=StationName+"\\default"};
  try{block=EnvironmentBlock(env,syntheticKey,out size);Check(CreateProcess(app,new StringBuilder(command),IntPtr.Zero,IntPtr.Zero,false,0x08000404,block,cwd,ref si,out pi));Attach(pi,WindowsIdentity.GetCurrent().User.Value,false);return ProcessId;}
  finally{ClearFree(block,size);}
 }
 public uint StartUser(string user,string domain,SecureString password,string sid,string app,string command,string cwd,IDictionary env,SecureString key){
  if(process!=IntPtr.Zero)throw new InvalidOperationException("Child already started");
  IntPtr p=IntPtr.Zero,block=IntPtr.Zero;int size=0;PI pi;SI si=new SI{cb=Marshal.SizeOf(typeof(SI)),desktop=StationName+"\\default"};
  if(command.Length>=1024)throw new InvalidOperationException("Command too long");
  try{
   p=Marshal.SecureStringToGlobalAllocUnicode(password);block=EnvironmentBlock(env,key,out size);
   Check(CreateProcessWithLogonW(user,domain,p,1,app,new StringBuilder(command),0x08000404,block,cwd,ref si,out pi),"StartUser/CreateProcessWithLogonW");Attach(pi,sid,true);return ProcessId;
  }finally{if(p!=IntPtr.Zero)Marshal.ZeroFreeGlobalAllocUnicode(p);ClearFree(block,size);}
 }
 public uint Wait(uint milliseconds){
  if(process==IntPtr.Zero)throw new InvalidOperationException("No child");
  uint status=WaitForSingleObject(process,milliseconds);if(status==258)return 259;Check(status==0);uint code;Check(GetExitCodeProcess(process,out code));return code;
 }
 public bool PrivateVisible {get{return G2WindowBoundary.Visible(station);}}
 public byte[] PrivateStationSecurity {get{return G2WindowBoundary.Read(station);}}
 public byte[] PrivateDesktopSecurity {get{return G2WindowBoundary.Read(desktop);}}
 public void SetPrivateStation(byte[] value){G2WindowBoundary.Set(station,value);}
 public void SetPrivateDesktop(byte[] value){G2WindowBoundary.Set(desktop,value);}
 public void Dispose(){
  if(job!=IntPtr.Zero){CloseHandle(job);job=IntPtr.Zero;}
  if(process!=IntPtr.Zero){WaitForSingleObject(process,10000);CloseHandle(process);process=IntPtr.Zero;}
  if(desktop!=IntPtr.Zero){CloseDesktop(desktop);desktop=IntPtr.Zero;}
  if(station!=IntPtr.Zero){CloseWindowStation(station);station=IntPtr.Zero;}
 }
}
