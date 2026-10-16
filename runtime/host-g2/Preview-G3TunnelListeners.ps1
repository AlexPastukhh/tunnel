# G3 source-only owner local listener inventory. No HTTP requests, credentials, process control or mutations.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$ownerSid='S-1-5-21-303538662-3368424508-2654684973-1001'
$guestSid='S-1-5-21-303538662-3368424508-2654684973-1009'
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
$session=[Diagnostics.Process]::GetCurrentProcess().SessionId
if($id.User.Value -ne $ownerSid -or $session -eq 0){throw 'Owner alexa in an interactive session required'}
$processes=@(Get-CimInstance Win32_Process -Filter "Name='tunnel-client.exe' OR Name='tunnel-client-runtime.exe'" -ErrorAction Stop)
$tcp=@(Get-NetTCPConnection -State Listen -ErrorAction Stop)
$records=@(foreach($proc in $processes){
 $pidNum=[int]$proc.ProcessId
 $who='UNVERIFIED'
 $ownerLookup='UNKNOWN'
 try{
  $r=Invoke-CimMethod -InputObject $proc -MethodName GetOwnerSid -ErrorAction Stop
  if($r.ReturnValue -eq 0 -and $r.Sid){
   if($r.Sid -eq $ownerSid){$who='OWNER'}elseif($r.Sid -eq $guestSid){$who='GUEST'}else{$who='OTHER'}
   $ownerLookup='OK'
  } else {$ownerLookup='NONZERO_OR_EMPTY'}
 }catch{$ownerLookup='FAILED'}
 $listening=@($tcp|Where-Object{[int]$_.OwningProcess -eq $pidNum}|Sort-Object LocalAddress,LocalPort|ForEach-Object{
  [pscustomobject]@{LocalAddress=[string]$_.LocalAddress;LocalPort=[int]$_.LocalPort}
 })
 [pscustomobject]@{
  ProcessId=$pidNum;Name=[string]$proc.Name;SessionId=[int]$proc.SessionId
  IdentityClass=$who;OwnerLookup=$ownerLookup
  Listening=$listening
 }
})
[pscustomobject]@{
 Kind='G3_TUNNEL_LISTENER_PREVIEW';Schema=1;ActorSid=$id.User.Value;ActorSession=$session
 SnapshotUtc=[DateTime]::UtcNow.ToString('o')
 Scope='tunnel-client.exe and tunnel-client-runtime.exe only; no network requests'
 ProcessCount=$records.Count;Processes=$records
 AclWrites=0;ProcessStarts=0;ProcessStops=0;HttpRequests=0;SecretValuesRead=$false
}|ConvertTo-Json -Depth 6
