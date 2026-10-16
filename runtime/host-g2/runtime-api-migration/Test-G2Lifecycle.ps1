#requires -Version 5.1
[CmdletBinding()]
param(
 [ValidateSet('Capture','Verify')][string]$Mode='Capture',
 [Parameter(Mandatory=$true)][int]$ExpectedGuestSession,
 [Parameter(Mandatory=$true)][int]$RuntimePid,
 [Parameter(Mandatory=$true)][int]$PythonPid,
 [Parameter(Mandatory=$true)][int]$NodePid,
 [string]$BaselinePath,[string]$BaselineSHA256
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
$session=[Diagnostics.Process]::GetCurrentProcess().SessionId
if($id.User.Value -ne 'S-1-5-21-303538662-3368424508-2654684973-1009' -or $session -ne $ExpectedGuestSession -or $session -le 0 -or @($id.Groups|Where-Object Value -eq 'S-1-5-32-544').Count){throw 'Exact ordinary guest session required'}
function Get-OwnMetadata($p){
 $o=Invoke-CimMethod -InputObject $p -MethodName GetOwnerSid
 if($o.ReturnValue -ne 0 -or $o.Sid -ne $id.User.Value -or $p.SessionId -ne $session){throw 'Own process SID/session mismatch'}
 [pscustomobject]@{Pid=$p.ProcessId;Parent=$p.ParentProcessId;Name=$p.Name;Sid=$o.Sid;Session=$p.SessionId;CreatedUtc=$p.CreationDate.ToUniversalTime().ToString('o')}
}
function Hash-Bytes([byte[]]$b){
 $sha=[Security.Cryptography.SHA256]::Create()
 try{([BitConverter]::ToString($sha.ComputeHash($b))).Replace('-','')}finally{$sha.Dispose()}
}
$exePins=@{'tunnel-client-runtime.exe'='A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A';'python.exe'='31FE10B4ED82A2F960AF0EF9931F46A4B84FF286F8B6FFD9DEE098CF4F10F17F';'node.exe'='2FFE3ACC0458FDDE999F50D11809BBE7C9B7EF204DCF17094E325D26ACE101D8'}
$chain=@()
foreach($item in @(@($RuntimePid,'tunnel-client-runtime.exe'),@($PythonPid,'python.exe'),@($NodePid,'node.exe'))){
 $p=Get-CimInstance Win32_Process -Filter ('ProcessId='+$item[0])
 if(!$p -or $p.Name -ne $item[1]){throw 'G2 chain drift'}
 if((Get-FileHash -LiteralPath $p.ExecutablePath -Algorithm SHA256).Hash -cne $exePins[$p.Name]){throw 'Actual process executable hash mismatch'}
 $chain+=Get-OwnMetadata $p
}
if($chain[1].Parent -ne $RuntimePid -or $chain[2].Parent -ne $PythonPid){throw 'G2 parent chain mismatch'}
$runtime='C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe'
$runtimeHash='A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A'
if((Get-FileHash -LiteralPath $runtime -Algorithm SHA256).Hash -cne $runtimeHash){throw 'Runtime artifact drift'}
$workspace=[IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'FortisHostG2\Workspace'))
if(!(Test-Path -LiteralPath $workspace -PathType Container) -or ((Get-Item -LiteralPath $workspace).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Own ordinary workspace required'}
if($Mode -eq 'Capture'){
 $all=@(Get-CimInstance Win32_Process -Filter ('SessionId='+$session))
 $chosen=@($all|Where-Object ProcessId -eq $RuntimePid)
 do{
  $ids=@($chosen|ForEach-Object ProcessId)
  $more=@($all|Where-Object {$_.ParentProcessId -in $ids -and $_.ProcessId -notin $ids -and $_.ProcessId -ne $PID})
  $chosen+=$more
  if($chosen.Count -gt 64){throw 'More than 64 descendants; inspect scope before capture'}
 }while($more.Count)
 $metadata=@($chosen|ForEach-Object {Get-OwnMetadata $_})
 foreach($pidExpected in @($RuntimePid,$PythonPid,$NodePid)){if($pidExpected -notin @($metadata|ForEach-Object Pid)){throw 'Capture missed chain process'}}
 $net=@(Get-NetTCPConnection -State Listen -ErrorAction Stop|Where-Object {$_.OwningProcess -in @($metadata|ForEach-Object Pid)}|Select-Object OwningProcess,LocalAddress,LocalPort)
 $baseline=[pscustomobject]@{Schema=1;Check='G2_LIFECYCLE_BASELINE';Utc=[DateTime]::UtcNow.ToString('o');Sid=$id.User.Value;Session=$session;RuntimeSHA256=$runtimeHash;Chain=$chain;Processes=$metadata;Listeners=$net;ObserverExcludedPid=$PID;Scope='CURRENT_RUNTIME_DESCENDANTS_SNAPSHOT';OwnerProcessesQueried=0;ProcessesStopped=0}
 $b=[Text.Encoding]::UTF8.GetBytes(($baseline|ConvertTo-Json -Depth 7))
 $path=Join-Path $workspace ('g2-lifecycle-baseline-'+[guid]::NewGuid().ToString('N')+'.json')
 $f=[IO.File]::Open($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
 try{$f.Write($b,0,$b.Length);$f.Flush($true)}finally{$f.Dispose()}
 $hash=Hash-Bytes $b
 if((Hash-Bytes ([IO.File]::ReadAllBytes($path))) -cne $hash){throw 'Baseline readback failed'}
 [pscustomobject]@{Mode=$Mode;BaselinePath=$path;BaselineSHA256=$hash;Baseline=$baseline;StopExecuted=$false;RecoveryAcceptance='PENDING_USER_STOP_AND_PINNED_RESTART'}|ConvertTo-Json -Depth 8
 return
}
if(!$BaselinePath -or $BaselineSHA256 -notmatch '^[A-Fa-f0-9]{64}$'){throw 'Exact baseline path and hash required'}
$path=[IO.Path]::GetFullPath($BaselinePath)
if(!$path.StartsWith($workspace+'\',[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetFileName($path) -notmatch '^g2-lifecycle-baseline-[a-f0-9]{32}\.json$'){throw 'Baseline outside own approved workspace'}
$info=Get-Item -LiteralPath $path
if($info.Length -gt 65536 -or ($info.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Unexpected baseline file'}
$b=[IO.File]::ReadAllBytes($path)
if((Hash-Bytes $b) -ine $BaselineSHA256){throw 'Baseline hash differs'}
$baseline=[Text.Encoding]::UTF8.GetString($b)|ConvertFrom-Json
if($baseline.Schema -ne 1 -or $baseline.Sid -ne $id.User.Value -or $baseline.RuntimeSHA256 -cne $runtimeHash){throw 'Baseline context mismatch'}
$old=@()
foreach($entry in $baseline.Processes){
 $p=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$entry.Pid)
 $same=$null -ne $p -and $p.CreationDate.ToUniversalTime().ToString('o') -ceq $entry.CreatedUtc
 $status=if($same){'ORIGINAL_STILL_ALIVE'}elseif($p){'PID_REUSED_ORIGINAL_GONE'}else{'ORIGINAL_GONE'}
 $old+=[pscustomobject]@{Pid=$entry.Pid;Name=$entry.Name;OriginalCreatedUtc=$entry.CreatedUtc;Status=$status}
}
$fresh=$chain[0].CreatedUtc -cne $baseline.Chain[0].CreatedUtc
[pscustomobject]@{
 Check='G2_LIFECYCLE_VERIFY';Utc=[DateTime]::UtcNow.ToString('o');Sid=$id.User.Value;Session=$session
 BaselinePath=$path;BaselineSHA256=(Hash-Bytes $b);OldProcesses=$old;CurrentChain=$chain;NewRuntime=$fresh
 OldSnapshotProcessesGone=(@($old|Where-Object Status -eq 'ORIGINAL_STILL_ALIVE').Count -eq 0)
 Passed=($fresh -and @($old|Where-Object Status -eq 'ORIGINAL_STILL_ALIVE').Count -eq 0)
 Scope='BASELINE_PROCESSES_EXITED_NEW_PINNED_GUEST_CHAIN_ALIVE'
 FutureDescendantsCovered=$false;ForcedFailureCaseTested=$false;ProcessesStopped=0;RuntimeRestartedByProbe=$false;OwnerPrivateContentReads=0
}|ConvertTo-Json -Depth 7
