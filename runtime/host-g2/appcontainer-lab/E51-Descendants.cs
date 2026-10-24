// E51: synthetic G2 descendant AppContainer proof, bounded Windows Job cleanup.
using System;
using System.Text;
using System.Threading;
using System.Runtime.InteropServices;
public class FortisG2E51 {
 [StructLayout(LayoutKind.Sequential)]public struct SI{public int cb;public IntPtr a,b,c;public int x,y,w,h,q,r,k,f;public short s,s2;public IntPtr p,i,o,e;}
 [StructLayout(LayoutKind.Sequential)]public struct SX{public SI si;public IntPtr attrs;}
 [StructLayout(LayoutKind.Sequential)]public struct SC{public IntPtr sid,caps;public uint count,res;}
 [StructLayout(LayoutKind.Sequential)]public struct PI{public IntPtr process,thread;public uint pid,tid;}
 [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)]public struct PE{
  public uint size,usage,pid;public IntPtr heap;public uint mod,threads,parent;public int pri;public uint flags;
  [MarshalAs(UnmanagedType.ByValTStr,SizeConst=260)]public string name;
 }
 [StructLayout(LayoutKind.Sequential)]public struct JB{public long t1,t2;public uint flags;public IntPtr m1,m2;public uint active;public IntPtr affinity;public uint priority,schedule;}
 [StructLayout(LayoutKind.Sequential)]public struct JI{public ulong a,b,c,d,e,f;}
 [StructLayout(LayoutKind.Sequential)]public struct JE{public JB basic;public JI io;public IntPtr a,b,c,d;}
 [DllImport("userenv.dll",CharSet=CharSet.Unicode)]static extern int CreateAppContainerProfile(string n,string d,string ds,IntPtr p,uint count,out IntPtr sid);
 [DllImport("userenv.dll",CharSet=CharSet.Unicode)]static extern int DeleteAppContainerProfile(string name);
 [DllImport("advapi32.dll",SetLastError=true)]static extern bool EqualSid(IntPtr a,IntPtr b);
 [DllImport("advapi32.dll",SetLastError=true)]static extern bool OpenProcessToken(IntPtr p,uint access,out IntPtr token);
 [DllImport("advapi32.dll",SetLastError=true)]static extern bool GetTokenInformation(IntPtr token,int klass,IntPtr buf,int len,out int needed);
 [DllImport("kernel32.dll",SetLastError=true)]static extern bool InitializeProcThreadAttributeList(IntPtr a,int c,int f,ref IntPtr sz);
 [DllImport("kernel32.dll",SetLastError=true)]static extern bool UpdateProcThreadAttribute(IntPtr a,uint f,IntPtr k,IntPtr v,IntPtr n,IntPtr prev,IntPtr ret);
 [DllImport("kernel32.dll")]static extern void DeleteProcThreadAttributeList(IntPtr a);
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)]static extern bool CreateProcessW(string exe,StringBuilder cmd,IntPtr pa,IntPtr ta,bool inh,uint flags,IntPtr env,string cwd,ref SX si,out PI pi);
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)]static extern IntPtr CreateJobObjectW(IntPtr a,string n);
 [DllImport("kernel32.dll",SetLastError=true)]static extern bool SetInformationJobObject(IntPtr job,int klass,ref JE info,int size);
 [DllImport("kernel32.dll",SetLastError=true)]static extern bool AssignProcessToJobObject(IntPtr job,IntPtr process);
 [DllImport("kernel32.dll",SetLastError=true)]static extern uint ResumeThread(IntPtr thread);
 [DllImport("kernel32.dll",SetLastError=true)]static extern uint WaitForSingleObject(IntPtr p,uint ms);
 [DllImport("kernel32.dll",SetLastError=true)]static extern bool GetExitCodeProcess(IntPtr p,out uint code);
 [DllImport("kernel32.dll",SetLastError=true)]static extern bool TerminateProcess(IntPtr p,uint code);
 [DllImport("kernel32.dll")]static extern bool CloseHandle(IntPtr h);
 [DllImport("kernel32.dll")]static extern IntPtr LocalFree(IntPtr h);
 [DllImport("kernel32.dll",SetLastError=true)]static extern IntPtr CreateToolhelp32Snapshot(uint f,uint pid);
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true,EntryPoint="Process32FirstW")]static extern bool First(IntPtr s,ref PE e);
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true,EntryPoint="Process32NextW")]static extern bool Next(IntPtr s,ref PE e);
 [DllImport("kernel32.dll",SetLastError=true)]static extern IntPtr OpenProcess(uint access,bool inherit,uint pid);
 static uint Child(uint p,string name) {
  IntPtr s=CreateToolhelp32Snapshot(2,0);if(s==new IntPtr(-1))return 0;
  try{PE e=new PE();e.size=(uint)Marshal.SizeOf(typeof(PE));
   if(!First(s,ref e))return 0;
   do{if(e.parent==p && string.Equals(e.name,name,StringComparison.OrdinalIgnoreCase))return e.pid;
   e.size=(uint)Marshal.SizeOf(typeof(PE));}while(Next(s,ref e));return 0;
  }finally{CloseHandle(s);}
 }
 static string Witness(IntPtr process,IntPtr expected) {
  if(process==IntPtr.Zero || process==new IntPtr(-1))return "PROCESS_OPEN_FAILED";
  IntPtr tok=IntPtr.Zero,buf=IntPtr.Zero;
  try{
   if(!OpenProcessToken(process,8,out tok))return "TOKEN_OPEN_ERROR="+Marshal.GetLastWin32Error();
   buf=Marshal.AllocHGlobal(4);int size=0;
   if(!GetTokenInformation(tok,29,buf,4,out size))return "IS_AC_ERROR="+Marshal.GetLastWin32Error();
   bool yes=Marshal.ReadInt32(buf)!=0;Marshal.FreeHGlobal(buf);buf=IntPtr.Zero;
   GetTokenInformation(tok,31,IntPtr.Zero,0,out size);
   if(size<IntPtr.Size||size>4096)return "SID_LENGTH_ERROR="+size;
   buf=Marshal.AllocHGlobal(size);
   if(!GetTokenInformation(tok,31,buf,size,out size))return "SID_QUERY_ERROR="+Marshal.GetLastWin32Error();
   IntPtr candidate=Marshal.ReadIntPtr(buf);
   bool equal=candidate!=IntPtr.Zero&&EqualSid(candidate,expected);
   return "IS_APPCONTAINER="+yes+" SID_MATCH="+equal+" VERDICT="+(yes&&equal?"PASS":"FAIL");
  }finally{if(buf!=IntPtr.Zero)Marshal.FreeHGlobal(buf);if(tok!=IntPtr.Zero)CloseHandle(tok);}
 }
 public static string Run(){
  string name="FortisG2E51_"+Guid.NewGuid().ToString("N");IntPtr sid=IntPtr.Zero,attr=IntPtr.Zero,cap=IntPtr.Zero,job=IntPtr.Zero;
  bool made=false,init=false;PI parent=new PI();var log=new StringBuilder();
  try{
   int hr=CreateAppContainerProfile(name,name,"Synthetic descendant witness",IntPtr.Zero,0,out sid);
   if(hr!=0)return "PROFILE_ERROR="+hr;made=true;
   IntPtr size=IntPtr.Zero;InitializeProcThreadAttributeList(IntPtr.Zero,1,0,ref size);
   if(size.ToInt64()<16||size.ToInt64()>65536)return "ATTRIBUTE_SIZE_ERROR";
   attr=Marshal.AllocHGlobal(size);if(!InitializeProcThreadAttributeList(attr,1,0,ref size))return "ATTR_INIT_ERROR="+Marshal.GetLastWin32Error();init=true;
   cap=Marshal.AllocHGlobal(Marshal.SizeOf(typeof(SC)));Marshal.StructureToPtr(new SC{sid=sid},cap,false);
   if(!UpdateProcThreadAttribute(attr,0,(IntPtr)0x20009,cap,(IntPtr)Marshal.SizeOf(typeof(SC)),IntPtr.Zero,IntPtr.Zero))
    return "ATTR_UPDATE_ERROR="+Marshal.GetLastWin32Error();
   job=CreateJobObjectW(IntPtr.Zero,null);if(job==IntPtr.Zero)return "JOB_CREATE_ERROR="+Marshal.GetLastWin32Error();
   JE jl=new JE();jl.basic.flags=0x2000;
   if(!SetInformationJobObject(job,9,ref jl,Marshal.SizeOf(typeof(JE))))return "JOB_LIMIT_ERROR="+Marshal.GetLastWin32Error();
   SX si=new SX();si.si.cb=Marshal.SizeOf(typeof(SX));si.attrs=attr;
   string ps=Environment.GetFolderPath(Environment.SpecialFolder.System)+"\\WindowsPowerShell\\v1.0\\powershell.exe";
   string node=Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles)+"\\nodejs\\node.exe";
   string js="const cp=require('child_process');const p=cp.spawn(process.execPath,['-e','setTimeout(()=>process.exit(74),7000)'],{stdio:'ignore'});p.on('error',e=>process.exit(e.code==='EACCES'?67:e.code==='ENOENT'?68:65));setTimeout(()=>process.exit(46),9000);";
   var cmd=new StringBuilder("\""+node+"\" -e \""+js+"\"");
   if(!CreateProcessW(node,cmd,IntPtr.Zero,IntPtr.Zero,false,0x08080004,IntPtr.Zero,null,ref si,out parent))
    return "PARENT_CREATE_ERROR="+Marshal.GetLastWin32Error();
   if(!AssignProcessToJobObject(job,parent.process))return "JOB_ASSIGN_ERROR="+Marshal.GetLastWin32Error();
   log.AppendLine("JOB_ATTACHED_BEFORE_RESUME=True");
   log.AppendLine("PARENT_"+Witness(parent.process,sid));
   if(ResumeThread(parent.thread)==uint.MaxValue)return log+"RESUME_ERROR="+Marshal.GetLastWin32Error();
   uint nodePid=0,grandPid=0;
   for(int i=0;i<30;i++){Thread.Sleep(200);nodePid=parent.pid;
     grandPid=Child(nodePid,"node.exe");
     if(grandPid!=0)break;}
   log.AppendLine("NODE_PARENT_FOUND="+(nodePid!=0));
   if(nodePid!=0){IntPtr h=OpenProcess(0x1000,false,nodePid);
     try{log.AppendLine("NODE_"+Witness(h,sid));}finally{if(h!=IntPtr.Zero)CloseHandle(h);}}
   log.AppendLine("GRANDCHILD_FOUND="+(grandPid!=0));
   if(grandPid!=0){IntPtr h=OpenProcess(0x1000,false,grandPid);
     try{log.AppendLine("GRANDCHILD_"+Witness(h,sid));}finally{if(h!=IntPtr.Zero)CloseHandle(h);}}
   uint w=WaitForSingleObject(parent.process,12000);
   if(w!=0)log.AppendLine("PARENT_TIMEOUT="+w);
   else{uint code=0;if(GetExitCodeProcess(parent.process,out code))log.AppendLine("PARENT_EXIT="+code+" EXPECTED_46="+(code==46));
   else log.AppendLine("EXIT_READ_ERROR="+Marshal.GetLastWin32Error());}
   return log.ToString();
  }finally{
   // Closing job terminates any still running descendants.
   if(job!=IntPtr.Zero)CloseHandle(job);
   else if(parent.process!=IntPtr.Zero){TerminateProcess(parent.process,99);WaitForSingleObject(parent.process,1000);}
   if(parent.thread!=IntPtr.Zero)CloseHandle(parent.thread);
   if(parent.process!=IntPtr.Zero)CloseHandle(parent.process);
   if(init)DeleteProcThreadAttributeList(attr);
   if(attr!=IntPtr.Zero)Marshal.FreeHGlobal(attr);
   if(cap!=IntPtr.Zero)Marshal.FreeHGlobal(cap);
   if(sid!=IntPtr.Zero)LocalFree(sid);
   if(made)Console.WriteLine("PROFILE_CLEANUP_HRESULT="+DeleteAppContainerProfile(name));
  }
 }
}
