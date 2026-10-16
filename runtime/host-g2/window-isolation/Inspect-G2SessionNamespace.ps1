# Owner-only read-only security descriptor diagnostic for current session BaseNamedObjects.
# No ACL writes, object enumeration, SID1009 login, secrets, browser or runtime.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$expectedOwnerSid='S-1-5-21-303538662-3368424508-2654684973-1001'
$actor=[Security.Principal.WindowsIdentity]::GetCurrent()
$admin=([Security.Principal.WindowsPrincipal]::new($actor)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$session=[Diagnostics.Process]::GetCurrentProcess().SessionId
if($actor.User.Value -ne $expectedOwnerSid -or !$admin -or $session -eq 0){throw 'Fresh local elevated owner PowerShell required'}
if('FortisSessionNamespaceAudit' -as [type]){throw 'Use a fresh PowerShell process'}
$native=@'
using System;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
public static class FortisSessionNamespaceAudit {
 [StructLayout(LayoutKind.Sequential)] struct UnicodeString {
  public ushort Length, MaximumLength; public IntPtr Buffer;
 }
 [StructLayout(LayoutKind.Sequential)] struct ObjectAttributes {
  public int Length; public IntPtr RootDirectory, ObjectName;
  public uint Attributes; public IntPtr SecurityDescriptor, SecurityQualityOfService;
 }
 [DllImport("ntdll.dll")] static extern int NtOpenDirectoryObject(out IntPtr handle,uint access,ref ObjectAttributes attrs);
 [DllImport("ntdll.dll")] static extern int NtQuerySecurityObject(IntPtr handle,uint info,IntPtr descriptor,uint size,out uint needed);
 [DllImport("ntdll.dll")] static extern int NtClose(IntPtr handle);
 static string Hex(int status) {return "0x"+unchecked((uint)status).ToString("X8");}
 public static string[] Read(int session) {
  // Exact current-session object directory only; never user-supplied path.
  string name=@"\Sessions\"+session+@"\BaseNamedObjects";
  IntPtr text=IntPtr.Zero,us=IntPtr.Zero,handle=IntPtr.Zero,sd=IntPtr.Zero;
  try {
   text=Marshal.StringToHGlobalUni(name);
   UnicodeString u=new UnicodeString {
    Length=checked((ushort)(name.Length*2)),
    MaximumLength=checked((ushort)((name.Length+1)*2)),
    Buffer=text
   };
   us=Marshal.AllocHGlobal(Marshal.SizeOf(typeof(UnicodeString)));
   Marshal.StructureToPtr(u,us,false);
   ObjectAttributes o=new ObjectAttributes {
    Length=Marshal.SizeOf(typeof(ObjectAttributes)),
    ObjectName=us, Attributes=0x40
   };
   int status=NtOpenDirectoryObject(out handle,0x00020000,ref o); // READ_CONTROL
   if(status!=0) return new string[]{Hex(status),null};
   sd=Marshal.AllocHGlobal(65536);
   uint needed;
   status=NtQuerySecurityObject(handle,4,sd,65536,out needed); // DACL_SECURITY_INFORMATION only
   if(status!=0) return new string[]{Hex(status),null};
   if(needed<20||needed>65536) throw new InvalidOperationException("Unexpected descriptor size");
   byte[] bytes=new byte[needed];Marshal.Copy(sd,bytes,0,(int)needed);
   var descriptor=new RawSecurityDescriptor(bytes,0);
   return new string[]{"0x00000000",descriptor.GetSddlForm(AccessControlSections.Access)};
  } finally {
   if(sd!=IntPtr.Zero) Marshal.FreeHGlobal(sd);
   if(handle!=IntPtr.Zero) NtClose(handle);
   if(us!=IntPtr.Zero) Marshal.FreeHGlobal(us);
   if(text!=IntPtr.Zero) Marshal.FreeHGlobal(text);
  }
 }
}
'@
Add-Type -TypeDefinition $native -ErrorAction Stop
$read=[FortisSessionNamespaceAudit]::Read($session)
[pscustomobject]@{
 At=[DateTime]::UtcNow.ToString('o')
 ActorSid=$actor.User.Value
 Admin=$admin
 Session=$session
 Path=('\Sessions\'+$session+'\BaseNamedObjects')
 NtQueryStatus=$read[0]
 DaclSddl=$read[1]
 AclWrites=0
 ObjectsEnumerated=0
 GuestPasswordPrompted=$false
}|ConvertTo-Json -Compress -Depth 4
