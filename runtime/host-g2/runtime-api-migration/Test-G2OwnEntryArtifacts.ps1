#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][int]$McpNodePid,[Parameter(Mandatory=$true)][ValidatePattern('^[A-Fa-f0-9]{64}$')][string]$SourceSHA256)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
if($identity.User.Value -ne 'S-1-5-21-303538662-3368424508-2654684973-1009'){throw 'Exact guest SID1009 required'}
$session=[Diagnostics.Process]::GetCurrentProcess().SessionId
$native=@'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
public static class FortisG2ArgvV1 {
    [DllImport("shell32.dll",SetLastError=true,CharSet=CharSet.Unicode)]
    static extern IntPtr CommandLineToArgvW(string command,out int count);
    [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr h);
    public static string[] Parse(string command){
        int count;IntPtr argv=CommandLineToArgvW(command,out count);
        if(argv==IntPtr.Zero)throw new Win32Exception(Marshal.GetLastWin32Error());
        try{var result=new string[count];for(int i=0;i<count;i++)result[i]=Marshal.PtrToStringUni(Marshal.ReadIntPtr(argv,i*IntPtr.Size));return result;}
        finally{LocalFree(argv);}
    }
}
'@
Add-Type -TypeDefinition $native
$node=Get-CimInstance Win32_Process -Filter ("ProcessId="+$McpNodePid) -Property ProcessId,ParentProcessId,Name,SessionId
if(!$node -or $node.Name -ne 'node.exe' -or $node.SessionId -ne $session){throw 'MCP Node identity/session drift'}
$python=Get-CimInstance Win32_Process -Filter ("ProcessId="+$node.ParentProcessId) -Property ProcessId,ParentProcessId,Name,SessionId,CommandLine
if(!$python -or $python.Name -ne 'python.exe' -or $python.SessionId -ne $session){throw 'Own Python parent unavailable'}
$owner=Invoke-CimMethod -InputObject $python -MethodName GetOwnerSid
if($owner.ReturnValue -ne 0 -or $owner.Sid -ne $identity.User.Value){throw 'Python owner mismatch'}
$argv=[FortisG2ArgvV1]::Parse([string]$python.CommandLine)
$artifacts=@();$pathCandidates=0
foreach($argument in $argv){
    if(!$argument.EndsWith('.py',[StringComparison]::OrdinalIgnoreCase)){continue}
    if([IO.Path]::GetFileName($argument) -ine 'g2-stdio-gate.py'){continue}
    $pathCandidates++
    if(![IO.Path]::IsPathRooted($argument)){continue}
    $path=[IO.Path]::GetFullPath($argument)
    $approved=$path.StartsWith('C:\Users\Public\Documents\FortisHostG1Probe\',[StringComparison]::OrdinalIgnoreCase) -or $path.StartsWith('C:\Users\FortisHostG1\AppData\Local\FortisHostG2\',[StringComparison]::OrdinalIgnoreCase)
    if(!$approved){continue}
    if(!(Test-Path -LiteralPath $path -PathType Leaf)){throw 'Own gate argument path does not exist'}
    $artifacts+=[pscustomobject]@{Path=$path;SHA256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash;Bytes=(Get-Item -LiteralPath $path).Length}
}
[pscustomobject]@{
    Check='G2_OWN_ENTRY_ARTIFACTS';Utc=[DateTime]::UtcNow.ToString('o');ProbeSourceSHA256=$SourceSHA256.ToUpperInvariant()
    GuestSid=$identity.User.Value;Session=$session;McpNodePid=$node.ProcessId;PythonPid=$python.ProcessId
    ArgvParser='CommandLineToArgvW';ArgumentCount=$argv.Count;GatePathCandidates=$pathCandidates;Artifacts=$artifacts
    InlinePythonArgument=($argv -contains '-c');RawCommandLinePrinted=$false;ProfileContentsRead=$false
    OwnerProcessQueries=0;RuntimeRestarted=$false
}|ConvertTo-Json -Depth 4
