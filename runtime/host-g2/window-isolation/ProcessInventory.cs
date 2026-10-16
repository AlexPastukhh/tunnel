using System;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Collections.Generic;
public static class G2ProcessInventory {
 [StructLayout(LayoutKind.Sequential)] struct Info {public uint Session,Pid;public IntPtr Name,Sid;}
 [DllImport("wtsapi32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool WTSEnumerateProcesses(IntPtr server,uint reserved,uint version,out IntPtr rows,out uint count);
 [DllImport("wtsapi32.dll")] static extern void WTSFreeMemory(IntPtr rows);
 [DllImport("kernel32.dll",SetLastError=true)] static extern IntPtr OpenProcess(uint access,bool inherit,uint pid);
 [DllImport("advapi32.dll",SetLastError=true)] static extern bool OpenProcessToken(IntPtr process,uint access,out IntPtr token);
 [DllImport("advapi32.dll",SetLastError=true)] static extern bool GetTokenInformation(IntPtr token,int kind,IntPtr data,uint length,out uint needed);
 [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
 static string TokenSid(uint pid){
  IntPtr p=OpenProcess(0x1000,false,pid),token=IntPtr.Zero,b=IntPtr.Zero;
  if(p==IntPtr.Zero)return "ERROR:"+Marshal.GetLastWin32Error();
  try{if(!OpenProcessToken(p,8,out token))return "ERROR:"+Marshal.GetLastWin32Error();uint n;GetTokenInformation(token,1,IntPtr.Zero,0,out n);b=Marshal.AllocHGlobal((int)n);
   if(!GetTokenInformation(token,1,b,n,out n))return "ERROR:"+Marshal.GetLastWin32Error();return new SecurityIdentifier(Marshal.ReadIntPtr(b)).Value;
  }finally{if(b!=IntPtr.Zero)Marshal.FreeHGlobal(b);if(token!=IntPtr.Zero)CloseHandle(token);CloseHandle(p);}
 }
 public static string[] ForSid(string sid,uint session){
  IntPtr rows;uint count;if(!WTSEnumerateProcesses(IntPtr.Zero,0,1,out rows,out count))throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
  try{var result=new List<string>();int size=Marshal.SizeOf(typeof(Info));for(int i=0;i<count;i++){Info p=(Info)Marshal.PtrToStructure(IntPtr.Add(rows,i*size),typeof(Info));if(p.Session!=session)continue;string actual=p.Sid==IntPtr.Zero?TokenSid(p.Pid):new SecurityIdentifier(p.Sid).Value;if(actual.StartsWith("ERROR:")){result.Add("UNKNOWN:"+p.Pid+":"+Marshal.PtrToStringUni(p.Name)+":"+actual);continue;}if(actual==sid)result.Add(p.Pid+":"+Marshal.PtrToStringUni(p.Name));}return result.ToArray();}finally{WTSFreeMemory(rows);}
 }
}
