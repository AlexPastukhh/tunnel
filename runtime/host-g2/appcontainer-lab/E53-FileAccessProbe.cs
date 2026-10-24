// E53 diagnostic: controlled metadata-only probes of known system Node executable. No owner files, data reads or real G2 runtime.
// Same command, cwd, environment and Windows Job for the ordinary and AppContainer cases.
// If a Job assignment fails, the still-suspended parent is terminated before closing handles.
using System;
using System.Text;
using System.Threading;
using System.Runtime.InteropServices;

public class FortisG2E53 {
 [StructLayout(LayoutKind.Sequential)] public struct SI {
  public int cb; public IntPtr reserved,desktop,title;
  public int x,y,dx,dy,xchars,ychars,fill,flags;
  public short show,reserved2; public IntPtr reservedBytes,stdin,stdout,stderr;
 }
 [StructLayout(LayoutKind.Sequential)] public struct SIX { public SI info; public IntPtr attributes; }
 [StructLayout(LayoutKind.Sequential)] public struct SEC_CAPS { public IntPtr sid,caps;public uint count,reserved; }
 [StructLayout(LayoutKind.Sequential)] public struct PI { public IntPtr process,thread;public uint pid,tid; }
 [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)] public struct PE {
  public uint size,usage,pid; public IntPtr heap;public uint module,threads,parent;public int priority;public uint flags;
  [MarshalAs(UnmanagedType.ByValTStr,SizeConst=260)]public string name;
 }
 [StructLayout(LayoutKind.Sequential)] public struct JobBasic {
  public long userTime,jobTime;public uint flags;
  public IntPtr minWorkingSet,maxWorkingSet;public uint active;
  public IntPtr affinity;public uint priority,scheduling;
 }
 [StructLayout(LayoutKind.Sequential)] public struct JobIO{public ulong a,b,c,d,e,f;}
 [StructLayout(LayoutKind.Sequential)] public struct JobExtended{
  public JobBasic basic;public JobIO io;
  public IntPtr processMemory,jobMemory,peakProcess,peakJob;
 }
 [DllImport("userenv.dll",CharSet=CharSet.Unicode)]static extern int CreateAppContainerProfile(string name,string display,string description,IntPtr caps,uint count,out IntPtr sid);
 [DllImport("userenv.dll",CharSet=CharSet.Unicode)]static extern int DeleteAppContainerProfile(string name);
 [DllImport("advapi32.dll",SetLastError=true)]static extern bool EqualSid(IntPtr a,IntPtr b);
 [DllImport("advapi32.dll",SetLastError=true)]static extern bool OpenProcessToken(IntPtr process,uint access,out IntPtr token);
 [DllImport("advapi32.dll",SetLastError=true)]static extern bool GetTokenInformation(IntPtr token,int klass,IntPtr buffer,int length,out int needed);
 [DllImport("kernel32.dll",SetLastError=true)]static extern bool InitializeProcThreadAttributeList(IntPtr attrs,int count,int flags,ref IntPtr bytes);
 [DllImport("kernel32.dll",SetLastError=true)]static extern bool UpdateProcThreadAttribute(IntPtr attrs,uint flags,IntPtr key,IntPtr value,IntPtr size,IntPtr prev,IntPtr result);
 [DllImport("kernel32.dll")]static extern void DeleteProcThreadAttributeList(IntPtr attrs);
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)]static extern bool CreateProcessW(string exe,StringBuilder command,IntPtr pa,IntPtr ta,bool inherit,uint flags,IntPtr env,string cwd,ref SIX info,out PI pi);
 [DllImport("kernel32.dll",SetLastError=true)]static extern IntPtr CreateJobObjectW(IntPtr sa,string name);
 [DllImport("kernel32.dll",SetLastError=true)]static extern bool SetInformationJobObject(IntPtr job,int klass,ref JobExtended info,int length);
 [DllImport("kernel32.dll",SetLastError=true)]static extern bool AssignProcessToJobObject(IntPtr job,IntPtr process);
 [DllImport("kernel32.dll",SetLastError=true)]static extern uint ResumeThread(IntPtr thread);
 [DllImport("kernel32.dll",SetLastError=true)]static extern uint WaitForSingleObject(IntPtr process,uint timeout);
 [DllImport("kernel32.dll",SetLastError=true)]static extern bool GetExitCodeProcess(IntPtr process,out uint exitCode);
 [DllImport("kernel32.dll",SetLastError=true)]static extern bool TerminateProcess(IntPtr process,uint code);
 [DllImport("kernel32.dll")]static extern bool CloseHandle(IntPtr h);
 [DllImport("kernel32.dll")]static extern IntPtr LocalFree(IntPtr p);
 [DllImport("kernel32.dll",SetLastError=true)]static extern IntPtr CreateToolhelp32Snapshot(uint flags,uint pid);
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true,EntryPoint="Process32FirstW")]static extern bool Process32First(IntPtr snap,ref PE pe);
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true,EntryPoint="Process32NextW")]static extern bool Process32Next(IntPtr snap,ref PE pe);
 [DllImport("kernel32.dll",SetLastError=true)]static extern IntPtr OpenProcess(uint access,bool inherit,uint pid);

 static uint FindChild(uint parent,string imageName){
  IntPtr snap=CreateToolhelp32Snapshot(2,0);
  if(snap==new IntPtr(-1))return 0;
  try{
   PE entry=new PE();entry.size=(uint)Marshal.SizeOf(typeof(PE));
   if(!Process32First(snap,ref entry))return 0;
   do{
    if(entry.parent==parent && string.Equals(entry.name,imageName,StringComparison.OrdinalIgnoreCase))
     return entry.pid;
    entry.size=(uint)Marshal.SizeOf(typeof(PE));
   }while(Process32Next(snap,ref entry));
   return 0;
  }finally{CloseHandle(snap);}
 }
 static string Inspect(IntPtr process,bool expectAppContainer,IntPtr expectedSid){
  if(process==IntPtr.Zero || process==new IntPtr(-1))return "PROCESS_NOT_OPENED";
  IntPtr token=IntPtr.Zero,buffer=IntPtr.Zero;
  try{
   if(!OpenProcessToken(process,8,out token))return "TOKEN_OPEN_ERROR="+Marshal.GetLastWin32Error();
   buffer=Marshal.AllocHGlobal(4);
   int bytes=0;
   if(!GetTokenInformation(token,29,buffer,4,out bytes))
    return "IS_APPCONTAINER_QUERY_ERROR="+Marshal.GetLastWin32Error();
   bool appContainer=Marshal.ReadInt32(buffer)!=0;
   Marshal.FreeHGlobal(buffer);buffer=IntPtr.Zero;
   bool sidMatch=false;
   if(appContainer){
    GetTokenInformation(token,31,IntPtr.Zero,0,out bytes);
    if(bytes<IntPtr.Size||bytes>4096)return "APP_SID_LENGTH_ERROR="+bytes;
    buffer=Marshal.AllocHGlobal(bytes);
    if(!GetTokenInformation(token,31,buffer,bytes,out bytes))
     return "APP_SID_QUERY_ERROR="+Marshal.GetLastWin32Error();
    IntPtr actual=Marshal.ReadIntPtr(buffer);
    sidMatch=expectedSid!=IntPtr.Zero&&actual!=IntPtr.Zero&&EqualSid(actual,expectedSid);
   }
   bool pass=appContainer==expectAppContainer && (expectAppContainer ? sidMatch:!appContainer);
   return "IS_APPCONTAINER="+appContainer+" SID_MATCH="+sidMatch+" EXPECT_AC="+expectAppContainer+" VERDICT="+(pass?"PASS":"FAIL");
  }finally{
   if(buffer!=IntPtr.Zero)Marshal.FreeHGlobal(buffer);
   if(token!=IntPtr.Zero)CloseHandle(token);
  }
 }
 public static string Scenario(bool isolated,int kind){
  string name="FortisG2E53_"+Guid.NewGuid().ToString("N");
  IntPtr sid=IntPtr.Zero,attrs=IntPtr.Zero,caps=IntPtr.Zero,job=IntPtr.Zero;
  bool profileCreated=false,attrsInitialized=false,assigned=false;
  PI parent=new PI();
  var log=new StringBuilder();
  try{
   if(isolated){
    int hr=CreateAppContainerProfile(name,name,"G2 E52 synthetic inheritance",IntPtr.Zero,0,out sid);
    if(hr!=0)return "PROFILE_CREATE_HRESULT=0x"+hr.ToString("X8");
    profileCreated=true;
    IntPtr bytes=IntPtr.Zero;
    InitializeProcThreadAttributeList(IntPtr.Zero,1,0,ref bytes);
    if(bytes.ToInt64()<16||bytes.ToInt64()>65536)return "ATTR_SIZE_ERROR="+bytes;
    attrs=Marshal.AllocHGlobal(bytes);
    if(!InitializeProcThreadAttributeList(attrs,1,0,ref bytes))
     return "ATTR_INIT_ERROR="+Marshal.GetLastWin32Error();
    attrsInitialized=true;
    caps=Marshal.AllocHGlobal(Marshal.SizeOf(typeof(SEC_CAPS)));
    Marshal.StructureToPtr(new SEC_CAPS{sid=sid},caps,false);
    if(!UpdateProcThreadAttribute(attrs,0,(IntPtr)0x20009,caps,(IntPtr)Marshal.SizeOf(typeof(SEC_CAPS)),IntPtr.Zero,IntPtr.Zero))
     return "ATTR_UPDATE_ERROR="+Marshal.GetLastWin32Error();
   }
   job=CreateJobObjectW(IntPtr.Zero,null);
   if(job==IntPtr.Zero)return "JOB_CREATE_ERROR="+Marshal.GetLastWin32Error();
   var limits=new JobExtended();limits.basic.flags=0x2000; // JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
   if(!SetInformationJobObject(job,9,ref limits,Marshal.SizeOf(typeof(JobExtended))))
    return "JOB_LIMIT_ERROR="+Marshal.GetLastWin32Error();
   string node=Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles)+"\\nodejs\\node.exe";
   string workDir=Environment.GetFolderPath(Environment.SpecialFolder.Windows);
   // Minimal script; all scripts and paths are embedded in process arguments, no file I/O.
   string js=@"const fs=require('fs');
const path=require('path');
const kind=Number(process.argv[2]);
const exe=process.execPath;
const root=process.env.SystemRoot;
const cases={
  0:()=>{process.exit(exe.toLowerCase().endsWith('node.exe')?20:27)},
  1:()=>{process.exit(fs.existsSync(exe)?20:21)},
  2:()=>{fs.statSync(exe)},
  3:()=>{fs.statSync(path.dirname(exe))},
  4:()=>{fs.statSync(process.cwd())},
  5:()=>{const fd=fs.openSync(exe,'r');fs.closeSync(fd)},
  6:()=>{if(!root)process.exit(25);fs.statSync(path.join(root,'System32','cmd.exe'))},
  7:()=>{if(!root)process.exit(25);fs.statSync(path.join(root,'System32','WindowsPowerShell','v1.0','powershell.exe'))},
  8:()=>{fs.realpathSync.native(exe)}
};
try{if(!(kind in cases))process.exit(26);cases[kind]();process.exit(20)}
catch(e){process.exit(e.code==='ENOENT'?21:e.code==='EACCES'?22:e.code==='EPERM'?23:24)}
";
   string jsB64=Convert.ToBase64String(Encoding.UTF8.GetBytes(js));
   var command=new StringBuilder("\""+node+"\" -e \"eval(Buffer.from(process.argv[1],'base64').toString('utf8'))\" "+jsB64+" "+kind);
   var si=new SIX();si.info.cb=isolated?Marshal.SizeOf(typeof(SIX)):Marshal.SizeOf(typeof(SI));
   si.attributes=attrs;
   uint flags=0x08000004|(isolated?0x00080000U:0U); // CREATE_NO_WINDOW | CREATE_SUSPENDED
   if(!CreateProcessW(node,command,IntPtr.Zero,IntPtr.Zero,false,flags,IntPtr.Zero,workDir,ref si,out parent))
    return "CREATE_NODE_WIN32="+Marshal.GetLastWin32Error();
   if(!AssignProcessToJobObject(job,parent.process)){
    int err=Marshal.GetLastWin32Error();
    TerminateProcess(parent.process,99);
    WaitForSingleObject(parent.process,1500);
    return "JOB_ASSIGN_ERROR="+err+" SUSPENDED_PARENT_TERMINATED=True";
   }
   assigned=true;
   log.AppendLine("JOB_ATTACHED_PRE_RESUME=True");
   string parentWitness=Inspect(parent.process,isolated,sid);
   log.AppendLine("PARENT_"+parentWitness);
   if(ResumeThread(parent.thread)==uint.MaxValue)
    return log+"RESUME_ERROR="+Marshal.GetLastWin32Error();
   uint waited=WaitForSingleObject(parent.process,8000);
   log.AppendLine("CASE="+kind);
   if(waited!=0)log.AppendLine("PROCESS_WAIT_FAILURE_OR_TIMEOUT="+waited);
   else{
    uint code=0;
    if(!GetExitCodeProcess(parent.process,out code))log.AppendLine("PROCESS_EXIT_QUERY_ERROR="+Marshal.GetLastWin32Error());
    else{
     string meaning=code==20?"OPERATION_SUCCESS":code==21?"NOT_FOUND_OR_INACCESSIBLE":code==22?"ACCESS_DENIED":code==23?"OPERATION_NOT_PERMITTED":code==24?"OTHER_EXCEPTION":code==25?"SYSTEMROOT_MISSING":code==26?"UNKNOWN_CASE":code==27?"UNEXPECTED_EXEC_PATH":"UNEXPECTED_OR_CRASH";
     log.AppendLine("PROCESS_EXIT="+code+" MEANING="+meaning);
    }
   }
   return log.ToString();
  }finally{
   // The suspended process must never survive a failed assignment.
   if(parent.process!=IntPtr.Zero&&!assigned){
    TerminateProcess(parent.process,99);WaitForSingleObject(parent.process,1500);
   }
   if(job!=IntPtr.Zero)CloseHandle(job); // kills all job descendants, including timeouts
   if(parent.thread!=IntPtr.Zero)CloseHandle(parent.thread);
   if(parent.process!=IntPtr.Zero)CloseHandle(parent.process);
   if(attrsInitialized)DeleteProcThreadAttributeList(attrs);
   if(attrs!=IntPtr.Zero)Marshal.FreeHGlobal(attrs);
   if(caps!=IntPtr.Zero)Marshal.FreeHGlobal(caps);
   if(sid!=IntPtr.Zero)LocalFree(sid);
   if(profileCreated)Console.WriteLine("SYNTHETIC_PROFILE_DELETE_HRESULT="+DeleteAppContainerProfile(name));
  }
 }
}