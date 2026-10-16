
using System;
using System.Runtime.InteropServices;
public static class G3Access {
 [DllImport("advapi32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern IntPtr OpenSCManager(string machine,string database,uint access);
 [DllImport("advapi32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern IntPtr OpenService(IntPtr scm,string name,uint access);
 [DllImport("advapi32.dll")] static extern bool CloseServiceHandle(IntPtr h);
 [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern IntPtr CreateFile(string p,uint access,uint share,IntPtr security,uint disposition,uint flags,IntPtr template);
 [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
 [DllImport("advapi32.dll", CharSet=CharSet.Unicode, SetLastError=true)] static extern bool ConvertStringSecurityDescriptorToSecurityDescriptor(string s,uint revision,out IntPtr sd,out uint len);
 [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr p);
 [DllImport("advapi32.dll",SetLastError=true)] static extern bool DuplicateToken(IntPtr token,int level,out IntPtr duplicate);
 [StructLayout(LayoutKind.Sequential)] struct Map { public uint Read,Write,Execute,All; }
 [DllImport("advapi32.dll",SetLastError=true)] static extern bool AccessCheck(IntPtr sd,IntPtr token,uint desired,ref Map map,IntPtr privileges,ref uint len,out uint granted,out bool allowed);
 public static int Service(string name,uint right) {
  IntPtr scm=OpenSCManager(null,null,1); if(scm==IntPtr.Zero)return Marshal.GetLastWin32Error();
  try {IntPtr h=OpenService(scm,name,right); if(h==IntPtr.Zero)return Marshal.GetLastWin32Error();CloseServiceHandle(h);return 0;}
  finally {CloseServiceHandle(scm);}
 }
 public static int File(string path,uint right) {
  IntPtr h=CreateFile(path,right,7,IntPtr.Zero,3,0x02000000,IntPtr.Zero);
  if(h==new IntPtr(-1))return Marshal.GetLastWin32Error();CloseHandle(h);return 0;
 }
 public static string Sddl(string s,IntPtr primary,uint right) {
  IntPtr sd=IntPtr.Zero,t=IntPtr.Zero,priv=IntPtr.Zero; uint n;
  try {
   if(!ConvertStringSecurityDescriptorToSecurityDescriptor(s,1,out sd,out n))return "ERROR:"+Marshal.GetLastWin32Error();
   if(!DuplicateToken(primary,2,out t))return "ERROR:"+Marshal.GetLastWin32Error();
   Map m=new Map {Read=0x120089,Write=0x120116,Execute=0x1200a0,All=0x1f01ff};
   n=4096;priv=Marshal.AllocHGlobal((int)n);uint granted;bool allowed;
   if(!AccessCheck(sd,t,right,ref m,priv,ref n,out granted,out allowed))return "ERROR:"+Marshal.GetLastWin32Error();
   return allowed?"ALLOW":"DENY";
  } finally {if(priv!=IntPtr.Zero)Marshal.FreeHGlobal(priv);if(t!=IntPtr.Zero)CloseHandle(t);if(sd!=IntPtr.Zero)LocalFree(sd);}
 }
}