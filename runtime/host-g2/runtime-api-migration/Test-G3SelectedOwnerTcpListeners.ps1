#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$CapturedSHA256)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
$session=[Diagnostics.Process]::GetCurrentProcess().SessionId
if($id.User.Value -ne 'S-1-5-21-303538662-3368424508-2654684973-1001' -or $session -ne 1){throw 'Exact owner metadata observer required'}
if($CapturedSHA256 -notmatch '^[A-F0-9]{64}$'){throw 'Captured hash required'}
$targets=@(
 [pscustomobject]@{Role='TransitionalOwnerHost';Pid=13520;Name='tunnel-client.exe';Created='2026-10-15T18:57:19.7775460Z';Path='C:\Tools\tunnel-client\tunnel-client.exe';SHA256='1946DE55A038313A9B9B2458D05FE1719FA9CF1F20A94DD5F38FC26A98BFDD42';KnownPort=8080},
 [pscustomobject]@{Role='RetainedOwnerRepo';Pid=22488;Name='tunnel-client.exe';Created='2026-10-15T18:59:53.4046800Z';Path='C:\Tools\tunnel-client\tunnel-client.exe';SHA256='1946DE55A038313A9B9B2458D05FE1719FA9CF1F20A94DD5F38FC26A98BFDD42';KnownPort=59183},
 [pscustomobject]@{Role='SelectedOwnerDesktopCommander';Pid=24724;Name='node.exe';Created='2026-10-15T18:57:20.0652940Z';Path='C:\Tools\desktop-commander-runtime\node.exe';SHA256='2FFE3ACC0458FDDE999F50D11809BBE7C9B7EF204DCF17094E325D26ACE101D8';KnownPort=0}
)
$hashes=@{};$rows=@()
$listeners=@(Get-NetTCPConnection -State Listen -ErrorAction Stop|Where-Object {$_.OwningProcess -in @($targets.Pid)}|Select-Object LocalAddress,LocalPort,OwningProcess)
foreach($target in $targets){
 $p=Get-CimInstance Win32_Process -Property ProcessId,ParentProcessId,Name,SessionId,CreationDate,ExecutablePath -Filter ('ProcessId='+$target.Pid)
 if(!$p){throw ('Selected original process absent: '+$target.Role)}
 $sid=Invoke-CimMethod -InputObject $p -MethodName GetOwnerSid
 $created=$p.CreationDate.ToUniversalTime().ToString('o')
 if($sid.ReturnValue -ne 0 -or $sid.Sid -ne $id.User.Value -or $p.SessionId -ne 1 -or $p.Name -ne $target.Name -or $created -cne $target.Created -or $p.ExecutablePath -ine $target.Path){throw ('Selected process fingerprint drift: '+$target.Role)}
 if(!$hashes.ContainsKey($target.Path)){$hashes[$target.Path]=(Get-FileHash -LiteralPath $target.Path -Algorithm SHA256).Hash}
 if($hashes[$target.Path] -cne $target.SHA256){throw ('Selected public executable hash drift: '+$target.Role)}
 $selected=@($listeners|Where-Object OwningProcess -eq $target.Pid)
 $rows+=[pscustomobject]@{
  Role=$target.Role;Pid=$p.ProcessId;Parent=$p.ParentProcessId;Name=$p.Name;Sid=$sid.Sid;Session=$p.SessionId;CreatedUtc=$created;ExeSHA256=$hashes[$target.Path]
  TcpListeners=@($selected|Select-Object LocalAddress,LocalPort)
  ExpectedKnownListenerPresent=if($target.KnownPort){@($selected|Where-Object {$_.LocalAddress -eq '127.0.0.1' -and $_.LocalPort -eq $target.KnownPort}).Count -eq 1}else{$null}
  UnexpectedTcpListeners=@($selected|Where-Object {$target.KnownPort -eq 0 -or $_.LocalAddress -ne '127.0.0.1' -or $_.LocalPort -ne $target.KnownPort}|Select-Object LocalAddress,LocalPort)
 }
}
[pscustomobject]@{
 Check='SELECTED_OWNER_TCP_LISTENERS_METADATA_ONLY';Utc=[DateTime]::UtcNow.ToString('o')
 SourceSHA256=$CapturedSHA256;ObserverSid=$id.User.Value;ObserverSession=$session
 ObservationComplete=($rows.Count -eq 3);Rows=$rows
 SelectedNodeHasNoTcpListener=(@($rows|Where-Object Role -eq 'SelectedOwnerDesktopCommander')[0].TcpListeners.Count -eq 0)
 HttpRequests=0;PrivateContentReads=0;RawArgvRead=$false;EnvironmentRead=$false;ProfileContentsRead=$false
 AclWrites=0;RuntimeRestarted=$false;OwnerFilesChanged=0
 Limitations=@('Three exact existing process fingerprints only, one metadata snapshot','No named-pipe, other-process or future-listener exclusion','Known full-client API exposure not remediated; no mutating or sensitive body requests')
}|ConvertTo-Json -Depth 7
