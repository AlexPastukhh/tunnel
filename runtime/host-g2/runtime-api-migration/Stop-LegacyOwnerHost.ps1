#requires -Version 5.1
[CmdletBinding()]
param([ValidateSet('Preview','Stop')][string]$Mode='Preview')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$owner='S-1-5-21-303538662-3368424508-2654684973-1001'
if([Security.Principal.WindowsIdentity]::GetCurrent().User.Value -ne $owner){throw 'Owner SID required'}
$runtime='C:\Tools\tunnel-client\tunnel-client.exe'
$launcher='C:\Users\alexa\Documents\prot\Start-Desktop-Commander-Secure-Tunnel.ps1'
if((Get-FileHash -LiteralPath $runtime -Algorithm SHA256).Hash -cne '1946DE55A038313A9B9B2458D05FE1719FA9CF1F20A94DD5F38FC26A98BFDD42'){throw 'Legacy EXE drift'}
if((Get-FileHash -LiteralPath $launcher -Algorithm SHA256).Hash -cne '0F644D4239E60886354EB83B6438CC888D8BDF3202B944B0304508E7C1336DFE'){throw 'Recovery launcher drift'}
$expected=@(
 @{Id=13520;Name='tunnel-client';Parent=18904;Created='2026-10-15T18:57:19.7775467Z'},
 @{Id=16092;Name='cmd';Parent=13520;Created='2026-10-15T18:57:20.0262353Z'},
 @{Id=24724;Name='node';Parent=16092;Created='2026-10-15T18:57:20.0652942Z'}
)
$handles=@()
try {
 foreach($e in $expected){
  $p=[Diagnostics.Process]::GetProcessById($e.Id)
  $null=$p.Handle
  $handles+=$p
  if($p.ProcessName -cne $e.Name -or $p.SessionId -ne 1 -or $p.StartTime.ToUniversalTime().Ticks -ne ([DateTime]::Parse($e.Created).ToUniversalTime().Ticks)){throw 'Selected process fingerprint drift'}
  $m=Get-CimInstance Win32_Process -Filter ('ProcessId='+$e.Id) -Property ProcessId,ParentProcessId,ExecutablePath,CommandLine
  if($m.ParentProcessId -ne $e.Parent -or (Invoke-CimMethod -InputObject $m -MethodName GetOwnerSid).Sid -ne $owner){throw 'Selected process ancestry/owner drift'}
  if($e.Id -eq 13520 -and ($m.ExecutablePath -ine $runtime -or $m.CommandLine -notmatch '(?i)(?:^|\s)run\s+--profile\s+desktop-commander(?:\s|$)')){throw 'Selected HOST profile/path drift'}
 }
 $rows=@($handles|ForEach-Object {[pscustomobject]@{Pid=$_.Id;Name=$_.ProcessName;CreatedUtc=$_.StartTime.ToUniversalTime().ToString('o')}})
 $state=[ordered]@{Check='E43_SELECTED_LEGACY_HOST_STOP';Utc=[DateTime]::UtcNow.ToString('o');Mode=$Mode;Rows=$rows;HeldProcessHandles=$true;RawArgvPrinted=$false;Scope='ONLY_13520_16092_24724';KillAttempted=@();Completed=$false}
 if($Mode -eq 'Preview'){$state|ConvertTo-Json -Depth 5;return}
 $journal='C:\Users\alexa\Repos\tunnel\docs\G3_LEGACY_HOST_STOP_ATTEMPT_2026-10-16.json'
 if(Test-Path -LiteralPath $journal){throw 'Existing stop journal; inspect actual effect before retry'}
 function Save-State {
  $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($state|ConvertTo-Json -Depth 5))
  $f=[IO.File]::Open($journal,[IO.FileMode]::Create,[IO.FileAccess]::Write,[IO.FileShare]::Read)
  try{$f.Write($bytes,0,$bytes.Length);$f.Flush($true)}finally{$f.Dispose()}
 }
 Save-State
 # Each Process object has already opened its original OS handle; no fresh PID-based kill.
 foreach($p in $handles){
  if(!$p.HasExited){
   $state.KillAttempted+=@($p.Id)
   Save-State
   $p.Kill()
  }
 }
 $state.Completed=$true;$state.Utc=[DateTime]::UtcNow.ToString('o')
 Save-State
} finally {
 foreach($p in $handles){$p.Dispose()}
}
