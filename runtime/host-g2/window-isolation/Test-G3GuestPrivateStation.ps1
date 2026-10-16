# Guest-only Windows Session 3 private station/desktop allocation and cleanup smoke test.
# Does not launch a child, change existing ACLs, or access owner objects.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$actor=[Security.Principal.WindowsIdentity]::GetCurrent()
$session=[Diagnostics.Process]::GetCurrentProcess().SessionId
$admin=(New-Object Security.Principal.WindowsPrincipal($actor)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$expectedSid='S-1-5-21-303538662-3368424508-2654684973-1009'
if($actor.User.Value -ne $expectedSid -or $session -ne 3 -or $admin){throw 'Exact non-admin SID1009 in guest Session 3 required'}
if('FortisG3GuestPrivateStation' -as [type]){throw 'Use fresh guest PowerShell'}
$source=@'
using System;
using System.Text;
using System.Runtime.InteropServices;
using System.ComponentModel;
public static class FortisG3GuestPrivateStation {
 [StructLayout(LayoutKind.Sequential)] struct SA {public int Length;public IntPtr Descriptor;public int Inherit;}
 [DllImport("advapi32.dll",CharSet=CharSet.Unicode,SetLastError=true)]
 static extern bool ConvertStringSecurityDescriptorToSecurityDescriptor(string s,uint revision,out IntPtr descriptor,out uint length);
 [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr ptr);
 [DllImport("user32.dll",CharSet=CharSet.Unicode,SetLastError=true)]
 static extern IntPtr CreateWindowStation(string name,uint flags,uint access,ref SA sa);
 [DllImport("user32.dll",SetLastError=true)] static extern IntPtr GetProcessWindowStation();
 [DllImport("user32.dll",SetLastError=true)] static extern bool SetProcessWindowStation(IntPtr station);
 [DllImport("user32.dll",SetLastError=true)] static extern bool CloseWindowStation(IntPtr station);
 [DllImport("user32.dll",CharSet=CharSet.Unicode,SetLastError=true)]
 static extern IntPtr CreateDesktop(string name,IntPtr device,IntPtr mode,uint flags,uint access,ref SA sa);
 [DllImport("user32.dll",SetLastError=true)] static extern bool CloseDesktop(IntPtr desktop);
 [DllImport("user32.dll",CharSet=CharSet.Unicode,SetLastError=true)]
 static extern bool GetUserObjectInformation(IntPtr obj,int index,StringBuilder b,uint length,out uint needed);
 [DllImport("user32.dll",SetLastError=true)]
 static extern bool GetUserObjectInformation(IntPtr obj,int index,IntPtr b,uint length,out uint needed);
 static void Check(bool ok,string op){if(!ok){int code=Marshal.GetLastWin32Error();throw new Win32Exception(code,op+" failed (Win32 "+code+")");}}
 static string Name(IntPtr handle) {
  var b=new StringBuilder(256);uint needed;
  Check(GetUserObjectInformation(handle,2,b,512,out needed),"GetUserObjectInformation/name");
  return b.ToString();
 }
 static bool Visible(IntPtr handle){
  IntPtr b=Marshal.AllocHGlobal(12);
  try{uint n;Check(GetUserObjectInformation(handle,1,b,12,out n),"GetUserObjectInformation/flags");return (Marshal.ReadInt32(b,8)&1)!=0;}
  finally{Marshal.FreeHGlobal(b);}
 }
 public static string Probe(string guestSid) {
  IntPtr original=GetProcessWindowStation(),station=IntPtr.Zero,desktop=IntPtr.Zero,sd=IntPtr.Zero;
  if(original==IntPtr.Zero)throw new InvalidOperationException("No original guest process station");
  bool switched=false,restored=false,desktopClosed=false,stationClosed=false,visible=true;
  string stationName=null,desktopName=null;
  try {
   uint n;
   string stationAcl="D:P(A;;0xf037f;;;SY)(A;;0xf037f;;;"+guestSid+")";
   Check(ConvertStringSecurityDescriptorToSecurityDescriptor(stationAcl,1,out sd,out n),"Station SDDL");
   var sa=new SA{Length=Marshal.SizeOf(typeof(SA)),Descriptor=sd,Inherit=0};
   // Standard users cannot specify Window Station names (Microsoft CreateWindowStationW).
   // NULL uses an OS-derived logon-session name; CREATE_ONLY fails on an existing object.
   station=CreateWindowStation(null,1,0xf037f,ref sa);
   Check(station!=IntPtr.Zero,"Create private window station");
   stationName=Name(station);visible=Visible(station);
   if(visible||stationName.Equals("WinSta0",StringComparison.OrdinalIgnoreCase))throw new InvalidOperationException("Interactive station refused");
   Check(SetProcessWindowStation(station),"Set private station");switched=true;
   LocalFree(sd);sd=IntPtr.Zero;
   string desktopAcl="D:P(A;;0xf01ff;;;SY)(A;;0xf01ff;;;"+guestSid+")";
   Check(ConvertStringSecurityDescriptorToSecurityDescriptor(desktopAcl,1,out sd,out n),"Desktop SDDL");
   sa.Descriptor=sd;
   desktop=CreateDesktop("default",IntPtr.Zero,IntPtr.Zero,0,0xf01ff,ref sa);
   Check(desktop!=IntPtr.Zero,"Create private desktop");
   desktopName=Name(desktop);
   if(desktopName!="default")throw new InvalidOperationException("Wrong private desktop name");
  } finally {
   if(switched){restored=SetProcessWindowStation(original);}
   else restored=true;
   if(restored){
    if(desktop!=IntPtr.Zero)desktopClosed=CloseDesktop(desktop);else desktopClosed=true;
    if(station!=IntPtr.Zero)stationClosed=CloseWindowStation(station);else stationClosed=true;
   }
   if(sd!=IntPtr.Zero)LocalFree(sd);
  }
  if(!restored||!desktopClosed||!stationClosed)throw new InvalidOperationException("Private station/desktop cleanup failed; do not retry");
  return stationName+"|"+desktopName+"|"+visible+"|"+restored+"|"+desktopClosed+"|"+stationClosed;
 }
}
'@
Add-Type -TypeDefinition $source -ErrorAction Stop
$parts=([FortisG3GuestPrivateStation]::Probe($expectedSid)).Split('|')
[pscustomobject]@{
 Sid=$actor.User.Value;Session=$session;Admin=$admin
 Station=$parts[0];Desktop=$parts[1];Visible=[bool]::Parse($parts[2])
 GuestProcessStationRestored=[bool]::Parse($parts[3])
 PrivateDesktopClosed=[bool]::Parse($parts[4])
 PrivateStationClosed=[bool]::Parse($parts[5])
 Result='PASS';OwnerAclWrites=0;OwnerObjectsTouched=0
}|ConvertTo-Json -Compress
