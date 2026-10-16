#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][int]$ExpectedGuestSession)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
$session=[Diagnostics.Process]::GetCurrentProcess().SessionId
if($id.User.Value -ne 'S-1-5-21-303538662-3368424508-2654684973-1009' -or $session -ne $ExpectedGuestSession -or $session -le 0 -or @($id.Groups | Where-Object Value -eq 'S-1-5-32-544').Count){throw 'Exact ordinary guest session required'}
if([IntPtr]::Size -ne 8){throw 'x64 process required'}
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.ComponentModel;
public static class FortisG2PssCalibration {
 [StructLayout(LayoutKind.Sequential)] struct FT { public uint Low,High; }
 [StructLayout(LayoutKind.Sequential,Size=48)] struct Extra { public long Reserved; }
 [StructLayout(LayoutKind.Sequential)] struct Entry {
  public IntPtr Handle; public uint Flags,ObjectType; public FT CaptureTime;
  public uint Attributes,GrantedAccess,HandleCount,PointerCount,PagedPoolCharge,NonPagedPoolCharge;
  public FT CreationTime; public ushort TypeNameLength; public IntPtr TypeName;
  public ushort ObjectNameLength; public IntPtr ObjectName; public Extra TypeSpecificInformation;
 }
 [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
 [DllImport("kernel32.dll")] static extern uint PssCaptureSnapshot(IntPtr p,uint flags,uint context,out IntPtr snapshot);
 [DllImport("kernel32.dll")] static extern uint PssFreeSnapshot(IntPtr p,IntPtr snapshot);
 [DllImport("kernel32.dll")] static extern uint PssWalkMarkerCreate(IntPtr allocator,out IntPtr marker);
 [DllImport("kernel32.dll")] static extern uint PssWalkMarkerFree(IntPtr marker);
 [DllImport("kernel32.dll")] static extern uint PssWalkSnapshot(IntPtr snapshot,int info,IntPtr marker,IntPtr buffer,uint size);
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern IntPtr CreateEventW(IntPtr security,bool manual,bool initial,string name);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool CloseHandle(IntPtr h);
 [DllImport("user32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern IntPtr OpenWindowStationW(string name,bool inherit,uint rights);
 [DllImport("user32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern IntPtr OpenDesktopW(string name,uint flags,bool inherit,uint rights);
 [DllImport("user32.dll",SetLastError=true)] static extern bool CloseWindowStation(IntPtr h);
 [DllImport("user32.dll",SetLastError=true)] static extern bool CloseDesktop(IntPtr h);
 public sealed class Result {
  public int EntrySize,Entries; public bool Completed,EventSeen,StationSeen,DesktopSeen;
  public string StationType,StationName,DesktopType,DesktopName,Error;
  public uint CaptureStatus,WalkStatus,MarkerFreeStatus,SnapshotFreeStatus;
  public bool EventClosed,StationClosed,DesktopClosed;
 }
 static string Text(IntPtr ptr,ushort bytes) {
  if(ptr==IntPtr.Zero || bytes==0) return "";
  if(bytes%2!=0 || bytes>32766) throw new InvalidOperationException("Invalid metadata length");
  return Marshal.PtrToStringUni(ptr,bytes/2);
 }
 public static Result Run() {
  Result r=new Result(); IntPtr station=IntPtr.Zero,desktop=IntPtr.Zero,ev=IntPtr.Zero;
  IntPtr snapshot=IntPtr.Zero,marker=IntPtr.Zero,buffer=IntPtr.Zero;
  try {
   r.EntrySize=Marshal.SizeOf(typeof(Entry));
   if(r.EntrySize!=136 || Marshal.OffsetOf(typeof(Entry),"TypeName").ToInt32()!=64 || Marshal.OffsetOf(typeof(Entry),"ObjectName").ToInt32()!=80) throw new InvalidOperationException("Unexpected x64 ABI");
   station=OpenWindowStationW("WinSta0",false,1);
   if(station==IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error(),"Own station fixture");
   desktop=OpenDesktopW("Default",0,false,1);
   if(desktop==IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error(),"Own desktop fixture");
   ev=CreateEventW(IntPtr.Zero,false,false,"Local\\FortisPssCalibration-"+Guid.NewGuid().ToString("N"));
   if(ev==IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error(),"Own event fixture");
   r.CaptureStatus=PssCaptureSnapshot(GetCurrentProcess(),12,0,out snapshot);
   if(r.CaptureStatus!=0) throw new Win32Exception((int)r.CaptureStatus,"Capture own handle metadata");
   uint status=PssWalkMarkerCreate(IntPtr.Zero,out marker);
   if(status!=0) throw new Win32Exception((int)status,"Create walk marker");
   buffer=Marshal.AllocHGlobal(r.EntrySize);
   for(int i=0;i<16384;i++) {
    r.WalkStatus=PssWalkSnapshot(snapshot,2,marker,buffer,(uint)r.EntrySize);
    if(r.WalkStatus==259){r.Completed=true;break;}
    if(r.WalkStatus!=0) throw new Win32Exception((int)r.WalkStatus,"Walk handles");
    Entry entry=(Entry)Marshal.PtrToStructure(buffer,typeof(Entry)); r.Entries++;
    // Inspect names only for our deliberately opened synthetic fixtures.
    if(entry.Handle==ev) r.EventSeen=true;
    if(entry.Handle==station){
     r.StationSeen=true; r.StationType=Text(entry.TypeName,entry.TypeNameLength);
     if((entry.Flags&2)!=0) r.StationName=Text(entry.ObjectName,entry.ObjectNameLength);
    }
    if(entry.Handle==desktop){
     r.DesktopSeen=true; r.DesktopType=Text(entry.TypeName,entry.TypeNameLength);
     if((entry.Flags&2)!=0) r.DesktopName=Text(entry.ObjectName,entry.ObjectNameLength);
    }
   }
   if(!r.Completed) throw new InvalidOperationException("Bounded walk exceeded");
  } catch(Exception e) { r.Error=e.GetType().Name+": "+e.Message; }
  finally {
   if(buffer!=IntPtr.Zero) Marshal.FreeHGlobal(buffer);
   if(marker!=IntPtr.Zero) r.MarkerFreeStatus=PssWalkMarkerFree(marker);
   if(snapshot!=IntPtr.Zero) r.SnapshotFreeStatus=PssFreeSnapshot(GetCurrentProcess(),snapshot);
   r.EventClosed=ev==IntPtr.Zero || CloseHandle(ev);
   r.DesktopClosed=desktop==IntPtr.Zero || CloseDesktop(desktop);
   r.StationClosed=station==IntPtr.Zero || CloseWindowStation(station);
  }
  return r;
 }
}
'@
$result=[FortisG2PssCalibration]::Run()
$calibrated=$result.Completed -and !$result.Error -and $result.EventSeen -and $result.StationSeen -and $result.DesktopSeen -and $result.StationType -ieq 'WindowStation' -and $result.DesktopType -ieq 'Desktop' -and $result.StationName -ieq ('\Sessions\'+$session+'\Windows\WindowStations\WinSta0') -and $result.DesktopName -in @('\Default',('\Sessions\'+$session+'\Windows\WindowStations\WinSta0\Default')) -and $result.EventClosed -and $result.DesktopClosed -and $result.StationClosed -and $result.MarkerFreeStatus -eq 0 -and $result.SnapshotFreeStatus -eq 0
[pscustomobject]@{
 Check='G2_PSS_OWN_GUI_HANDLE_CALIBRATION';Utc=[DateTime]::UtcNow.ToString('o')
 GuestSid=$id.User.Value;GuestSession=$session;Pid=$PID;CaptureFlags=12
 Result=$result;GuiInventoryMethodCalibrated=$calibrated
 Scope='SELF_ONLY_METHOD_CALIBRATION';OtherProcessesCaptured=0;MemoryContentsCaptured=$false
 OwnerContentReads=0;ClipboardOperations=0;InputInjection=0;AclWrites=0;StationDesktopSwitches=0
}|ConvertTo-Json -Depth 6
