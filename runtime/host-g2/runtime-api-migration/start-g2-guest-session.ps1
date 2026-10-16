#requires -Version 5.1
# Source preparation only. Preview is read-only; LaunchTest starts only the existing G2 profile.
[CmdletBinding()]
param(
    [ValidateSet('Validate','Preview','LaunchTest')][string]$Mode='Preview',
    [ValidatePattern('^[A-Fa-f0-9]{64}$')][string]$CapturedSHA256
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$launcherHash=$CapturedSHA256
if(!$launcherHash){
    if(!$PSCommandPath){throw 'Captured execution requires verified CapturedSHA256'}
    $launcherHash=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
}
$launcherHash=$launcherHash.ToUpperInvariant()
$native=@'
using System;
using System.Text;
using System.ComponentModel;
using System.Runtime.InteropServices;
public static class FortisG2GuestEntryContextV1 {
    public const string TemplateSHA256="__G2_TEMPLATE_SHA256__";
    [DllImport("wtsapi32.dll",EntryPoint="WTSQuerySessionInformationW",CharSet=CharSet.Unicode,SetLastError=true)]
    static extern bool WtsInfo(IntPtr server,uint session,int kind,out IntPtr buffer,out uint bytes);
    [DllImport("wtsapi32.dll")] static extern void WTSFreeMemory(IntPtr buffer);
    [DllImport("user32.dll",SetLastError=true)] static extern IntPtr GetProcessWindowStation();
    [DllImport("user32.dll")] static extern IntPtr GetThreadDesktop(uint thread);
    [DllImport("kernel32.dll")] static extern uint GetCurrentThreadId();
    [DllImport("user32.dll",EntryPoint="GetUserObjectInformationW",CharSet=CharSet.Unicode,SetLastError=true)]
    static extern bool ObjectName(IntPtr h,int kind,StringBuilder buffer,uint bytes,out uint needed);
    [DllImport("user32.dll",EntryPoint="GetUserObjectInformationW",SetLastError=true)]
    static extern bool ObjectFlags(IntPtr h,int kind,IntPtr buffer,uint bytes,out uint needed);
    static void Check(bool ok,string stage){if(!ok){int e=Marshal.GetLastWin32Error();throw new Win32Exception(e,stage+" Win32="+e);}}
    static string WtsText(uint session,int kind){
        IntPtr buffer=IntPtr.Zero;uint bytes;
        try{Check(WtsInfo(IntPtr.Zero,session,kind,out buffer,out bytes),"Own WTS query "+kind);
            if(buffer==IntPtr.Zero||bytes<2||bytes>4096||(bytes&1)!=0)throw new InvalidOperationException("Invalid own WTS string");
            return Marshal.PtrToStringUni(buffer,(int)bytes/2).TrimEnd('\0');
        }finally{if(buffer!=IntPtr.Zero)WTSFreeMemory(buffer);}
    }
    static string Name(IntPtr h){uint needed;var b=new StringBuilder(512);Check(ObjectName(h,2,b,1024,out needed),"Own user object name");return b.ToString();}
    public static string[] Read(uint session){
        IntPtr station=GetProcessWindowStation(),desktop=GetThreadDesktop(GetCurrentThreadId());
        Check(station!=IntPtr.Zero&&desktop!=IntPtr.Zero,"Own station/desktop handles");
        IntPtr flags=Marshal.AllocHGlobal(12);uint needed;bool visible;
        try{Check(ObjectFlags(station,1,flags,12,out needed),"Own station flags");visible=(Marshal.ReadInt32(flags,8)&1)!=0;}
        finally{Marshal.FreeHGlobal(flags);}
        // Query only our process session, not the owner session or the active-console session.
        return new string[]{WtsText(session,5),WtsText(session,7),Name(station),Name(desktop),visible?"true":"false"};
    }
}
'@
$templateHasher=[Security.Cryptography.SHA256]::Create()
try{$templateHash=([BitConverter]::ToString($templateHasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($native)))).Replace('-','')}
finally{$templateHasher.Dispose()}
if('FortisG2GuestEntryContextV1' -as [type]){
    if([FortisG2GuestEntryContextV1]::TemplateSHA256 -cne $templateHash){throw 'Native source changed: use fresh PowerShell'}
}else{Add-Type -TypeDefinition $native.Replace('__G2_TEMPLATE_SHA256__',$templateHash) -ErrorAction Stop}

function Assert-G2GuestContext {
    param([Parameter(Mandatory=$true)]$Context)
    if($Context.TokenSid -ne 'S-1-5-21-303538662-3368424508-2654684973-1009'){throw 'Exact G2 SID1009 required'}
    if($Context.AdminGroupPresent -or $Context.Impersonating){throw 'Non-admin primary guest context required'}
    if($Context.SessionId -le 0){throw 'Interactive guest session required'}
    if($Context.SessionOwnerSid -ne $Context.TokenSid){throw 'Session belongs to another user: use guest logon, not Run as'}
    if($Context.Station -ine 'WinSta0' -or $Context.Desktop -ine 'Default' -or !$Context.StationVisible){throw 'Own interactive WinSta0/Default required'}
}
function Get-G2SessionTunnels {
    param([int]$GuestSession)
    $filter="(Name='tunnel-client.exe' OR Name='tunnel-client-runtime.exe') AND SessionId=$GuestSession"
    @(Get-CimInstance Win32_Process -Filter $filter -Property ProcessId,Name,SessionId -ErrorAction Stop |
        Select-Object ProcessId,Name,SessionId)
}
function New-G2StartInfo {
    param([string]$RuntimePath,[string]$ProfileDirectory,[string]$Workspace,[string]$Key)
    if($ProfileDirectory.Contains('"') -or $ProfileDirectory.EndsWith('\')){throw 'Invalid profile directory quoting'}
    $info=New-Object Diagnostics.ProcessStartInfo
    $info.FileName=$RuntimePath
    $info.UseShellExecute=$false
    $info.CreateNoWindow=$false
    $info.WorkingDirectory=$Workspace
    $info.Arguments='run --profile fortis-host-g2-test --profile-dir "'+$ProfileDirectory+'" --control-plane.api-key env:CONTROL_PLANE_API_KEY --harpoon.additional-transport='
    $info.EnvironmentVariables['CONTROL_PLANE_API_KEY']=$Key
    $info.EnvironmentVariables['DESKTOP_COMMANDER_DISABLE_MCP_UI']='1'
    return $info
}
if($Mode -eq 'Validate'){
    [pscustomobject]@{Mode=$Mode;SourceSHA256=$launcherHash;NativeTemplateSHA256=$templateHash;CSharpCompiled=$true;NativeCallsExecuted=$false;RuntimeStarted=$false}|ConvertTo-Json -Compress
    return
}
if($env:OS -ne 'Windows_NT' -or ![Environment]::Is64BitProcess){throw 'Windows x64 PowerShell required'}
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
if($identity.User.Value -ne 'S-1-5-21-303538662-3368424508-2654684973-1009'){throw 'Run inside FortisHostG1 guest logon'}
$impersonation=[Security.Principal.WindowsIdentity]::GetCurrent($true)
try{$impersonating=$null -ne $impersonation}finally{if($null -ne $impersonation){$impersonation.Dispose()}}
$adminGroup=@($identity.Groups|Where-Object Value -eq 'S-1-5-32-544').Count -gt 0
if($adminGroup -or $impersonating){throw 'Ordinary guest primary logon required'}
$session=[Diagnostics.Process]::GetCurrentProcess().SessionId
$own=[FortisG2GuestEntryContextV1]::Read([uint32]$session)
if(!$own[0] -or !$own[1]){throw 'Own WTS logon user/domain unavailable'}
$account=[Security.Principal.NTAccount]::new($own[1],$own[0])
$sessionSid=$account.Translate([Security.Principal.SecurityIdentifier]).Value
$context=[pscustomobject]@{TokenSid=$identity.User.Value;AdminGroupPresent=$adminGroup;Impersonating=$impersonating;SessionId=$session;SessionOwnerSid=$sessionSid;Station=$own[2];Desktop=$own[3];StationVisible=[bool]::Parse($own[4])}
Assert-G2GuestContext $context
$runtime='C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe'
$runtimeHash='A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A'
if((Get-FileHash -LiteralPath $runtime -Algorithm SHA256).Hash -cne $runtimeHash){throw 'Runtime artifact hash mismatch'}
$localApp=[Environment]::GetFolderPath([Environment+SpecialFolder]::LocalApplicationData)
if(!$localApp){throw 'Own LocalAppData unavailable'}
$stateRoot=Join-Path $localApp 'FortisHostG2'
$profileDir=Join-Path $stateRoot 'profiles'
$profileFile=Join-Path $profileDir 'fortis-host-g2-test.yaml'
$workspace=Join-Path $stateRoot 'Workspace'
if(!(Test-Path -LiteralPath $profileFile -PathType Leaf)){throw 'Existing own G2 profile missing; no init/provision performed'}
if(!(Test-Path -LiteralPath $workspace -PathType Container)){throw 'Existing own G2 Workspace missing; inspect baseline'}
$existing=@(Get-G2SessionTunnels $session)
$preview=[pscustomobject]@{
    Mode=$Mode;SourceSHA256=$launcherHash;Context=$context;RuntimeSHA256=$runtimeHash
    Profile='fortis-host-g2-test';ProfileExists=$true;ProfileContentsRead=$false;Workspace=$workspace
    ExistingSessionTunnels=$existing;DuplicateScope='CURRENT_GUEST_SESSION_PLUS_NEW_ENTRY_LOCK'
    LegacyG2InOtherSessions='NOT_INSPECTED_NOT_EXCLUDED';OwnerProcessQueries=0
    LaunchTestPrerequisitesPass=($existing.Count -eq 0);ExclusiveLock='ACQUIRED_ONLY_IN_LAUNCHTEST'
    RuntimeStarted=$false;WindowsAcceptance='PENDING'
}
if($Mode -eq 'Preview'){$preview|ConvertTo-Json -Depth 5;return}
if($existing.Count){throw 'Tunnel process exists in this guest session; inspect existing G2 before starting another'}
$lockDirectory=Join-Path $stateRoot 'launcher-locks'
$null=[IO.Directory]::CreateDirectory($lockDirectory)
$lock=$null;$child=$null
try{
    $lock=[IO.File]::Open((Join-Path $lockDirectory 'fortis-host-g2-test.lock'),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
    if(@(Get-G2SessionTunnels $session).Count){throw 'Tunnel appeared in this guest session; launch cancelled'}
    $key=$null;$pointer=[IntPtr]::Zero;$info=$null
    try{
        $key=Read-Host 'Enter only the separate G2 test runtime key locally' -AsSecureString
        if($key.Length -eq 0){throw 'Empty G2 key'}
        $pointer=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($key)
        $info=New-G2StartInfo $runtime $profileDir $workspace ([Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer))
        $child=[Diagnostics.Process]::Start($info)
        if($null -eq $child){throw 'G2 child process not created'}
    }finally{
        if($null -ne $info){$info.EnvironmentVariables.Remove('CONTROL_PLANE_API_KEY')}
        if($pointer -ne [IntPtr]::Zero){[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)}
        if($null -ne $key){$key.Dispose()}
    }
    if(!$child.HasExited -and $child.SessionId -ne $session){$child.Kill();throw 'Own child has unexpected session; stopped only this child'}
    [pscustomobject]@{Mode='LaunchTestStarted';SourceSHA256=$launcherHash;Pid=$child.Id;GuestSession=$session;Profile='fortis-host-g2-test';ParentEnvironmentChanged=$false;ProductionAccepted=$false}|ConvertTo-Json -Compress
    $child.WaitForExit()
    if($child.ExitCode -ne 0){throw ('G2 runtime exited with code '+$child.ExitCode)}
}finally{
    if($null -ne $child){$child.Dispose()}
    if($null -ne $lock){$lock.Dispose()}
}
