# Source-only G3 diagnostic. Guest Session 3; current window station and accessible station names.
# Does NOT create/open/switch/close window stations or desktops; no ACL change.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
$session=[Diagnostics.Process]::GetCurrentProcess().SessionId
$admin=(New-Object Security.Principal.WindowsPrincipal($id)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$expected='S-1-5-21-303538662-3368424508-2654684973-1009'
if($id.User.Value -ne $expected -or $session -ne 3 -or $admin){throw 'Guest SID1009 / Session3 / non-admin required'}
if('FortisG3ReadOnlyStations' -as [type]){throw 'Use fresh guest PowerShell'}
$cs=@'
using System;
using System.Text;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.ComponentModel;
public static class FortisG3ReadOnlyStations {
 [DllImport("user32.dll",SetLastError=true)] static extern IntPtr GetProcessWindowStation();
 [DllImport("user32.dll",EntryPoint="GetUserObjectInformationW",CharSet=CharSet.Unicode,SetLastError=true)]
 static extern bool GetUserObjectName(IntPtr handle,int index,StringBuilder value,uint length,out uint needed);
 [DllImport("user32.dll",EntryPoint="GetUserObjectInformationW",SetLastError=true)]
 static extern bool GetUserObjectFlags(IntPtr handle,int index,IntPtr value,uint length,out uint needed);
 [UnmanagedFunctionPointer(CallingConvention.Winapi,CharSet=CharSet.Unicode)]
 delegate bool StationCallback([MarshalAs(UnmanagedType.LPWStr)] string name,IntPtr data);
 [DllImport("user32.dll",EntryPoint="EnumWindowStationsW",CharSet=CharSet.Unicode,SetLastError=true)]
 static extern bool EnumWindowStations(StationCallback callback,IntPtr data);
 static void Check(bool ok,string name){if(!ok){int e=Marshal.GetLastWin32Error();throw new Win32Exception(e,name+" failed Win32 "+e);}}
 public static string[] Inspect(){
  var result=new List<string>();
  IntPtr current=GetProcessWindowStation();
  if(current==IntPtr.Zero)throw new Win32Exception(Marshal.GetLastWin32Error(),"GetProcessWindowStation");
  uint needed=0;var name=new StringBuilder(512);
  Check(GetUserObjectName(current,2,name,(uint)name.Capacity*2,out needed),"CurrentStationName");
  IntPtr ptr=Marshal.AllocHGlobal(12);
  bool visible=false;
  try{
   Check(GetUserObjectFlags(current,1,ptr,12,out needed),"CurrentStationFlags");
   visible=(Marshal.ReadInt32(ptr,8)&1)!=0;
  }finally{Marshal.FreeHGlobal(ptr);}
  result.Add(name.ToString());result.Add(visible?"true":"false");
  var stations=new List<string>();
  StationCallback callback=(value,data)=>{if(stations.Count<32)stations.Add(value);return true;};
  bool ok=EnumWindowStations(callback,IntPtr.Zero);
  int error=ok?0:Marshal.GetLastWin32Error();
  result.Add(ok?"true":"false");result.Add(error.ToString());
  result.AddRange(stations);
  return result.ToArray();
 }
}
'@
Add-Type -TypeDefinition $cs -ErrorAction Stop
$got=[FortisG3ReadOnlyStations]::Inspect()
[pscustomobject]@{
 Sid=$id.User.Value;Session=$session;Admin=$admin
 CurrentStationName=$got[0];CurrentStationVisible=[bool]::Parse($got[1])
 EnumerationAllowed=[bool]::Parse($got[2]);EnumerationWin32=[int]::Parse($got[3])
 AccessibleStationNames=@($got|Select-Object -Skip 4)
 Creates=0;AclWrites=0;DesktopReads=0;OwnerSessionTouched=$false
}|ConvertTo-Json -Compress -Depth 3
