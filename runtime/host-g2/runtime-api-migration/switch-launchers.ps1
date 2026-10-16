param(
 [ValidateSet('Preview','Apply','Rollback')][string]$Mode='Preview',
 [string]$BackupPath
)
$ErrorActionPreference='Stop'
$OwnerSid='S-1-5-21-303538662-3368424508-2654684973-1001'
if([Security.Principal.WindowsIdentity]::GetCurrent().User.Value -ne $OwnerSid){throw 'Run only as alexa; no elevation is requested'}
$PlanPath=Join-Path $PSScriptRoot 'migration-plan.json'
if((Get-FileHash -LiteralPath $PlanPath -Algorithm SHA256).Hash -ne '9EB03A985E71FDC32944DCDD8D327008C989C3091E0A0BB46B90EA4A8A0773D8'){throw 'Migration plan changed'}
$Plan=Get-Content -LiteralPath $PlanPath -Raw|ConvertFrom-Json
$Runtime='C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe'
if((Get-FileHash -LiteralPath $Runtime -Algorithm SHA256).Hash -ne $Plan.runtimeSha256){throw 'Runtime changed'}
function Get-Sha([byte[]]$Bytes){
 $sha=[Security.Cryptography.SHA256]::Create()
 try {return ([BitConverter]::ToString($sha.ComputeHash($Bytes))).Replace('-','')}finally{$sha.Dispose()}
}
function Write-Guarded([string]$Path,[string]$Expected,[byte[]]$Bytes){
 $stream=[IO.File]::Open($Path,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read)
 try {
  $old=New-Object byte[] $stream.Length
  $offset=0;while($offset -lt $old.Length){$n=$stream.Read($old,$offset,$old.Length-$offset);if($n -eq 0){throw 'Short read'};$offset+=$n}
  if((Get-Sha $old) -ne $Expected){throw ('Live file changed: '+$Path)}
  $stream.Position=0;$stream.Write($Bytes,0,$Bytes.Length);$stream.SetLength($Bytes.Length);$stream.Flush($true)
 }finally{$stream.Dispose()}
 if((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ne (Get-Sha $Bytes)){throw ('Readback failed: '+$Path)}
}
$Rows=@(foreach($e in $Plan.entries){
 $candidate=Join-Path $PSScriptRoot $e.candidate
 if((Get-FileHash -LiteralPath $candidate -Algorithm SHA256).Hash -ne $e.afterSha256){throw 'Candidate changed'}
 $current=(Get-FileHash -LiteralPath $e.live -Algorithm SHA256).Hash
 [pscustomobject]@{entry=$e;candidate=$candidate;current=$current;state=$(if($current -eq $e.beforeSha256){'BEFORE'}elseif($current -eq $e.afterSha256){'AFTER'}else{'DRIFT'})}
})
if(@($Rows|Where-Object state -eq 'DRIFT').Count){throw 'Live launcher drift; inspect before writing'}
if($Mode -eq 'Preview'){
 $Rows|ForEach-Object{[pscustomobject]@{Live=$_.entry.live;Candidate=$_.candidate;State=$_.state}}|ConvertTo-Json -Compress
 Write-Output 'Preview only. No files, processes, ACL or profiles changed.'
 return
}
if($Mode -eq 'Apply'){
 if(@($Rows|Where-Object state -ne 'AFTER').Count -eq 0){Write-Output 'Already applied. No restart performed.';return}
 if(@($Rows|Where-Object state -ne 'BEFORE').Count){throw 'Partial application detected; use the recorded backup'}
 $root=Join-Path $env:LOCALAPPDATA 'FortisG3ApiMigration'
 $dir=Join-Path $root ((Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')+'-'+[guid]::NewGuid().ToString('N'))
 New-Item -ItemType Directory -Path $dir|Out-Null
 $saved=@(foreach($r in $Rows){$bytes=[IO.File]::ReadAllBytes($r.entry.live);if((Get-Sha $bytes) -ne $r.entry.beforeSha256){throw 'Live file changed before backup'};[pscustomobject]@{live=$r.entry.live;beforeSha256=$r.entry.beforeSha256;afterSha256=$r.entry.afterSha256;bytes=[Convert]::ToBase64String($bytes)}})
 $backup=Join-Path $dir 'launchers-before.json'
 [IO.File]::WriteAllText($backup,([pscustomobject]@{planSha256='9EB03A985E71FDC32944DCDD8D327008C989C3091E0A0BB46B90EA4A8A0773D8';at=[DateTime]::UtcNow.ToString('o');entries=$saved}|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
 Write-Output ('Backup: '+$backup)
 foreach($r in $Rows){Write-Guarded $r.entry.live $r.entry.beforeSha256 ([IO.File]::ReadAllBytes($r.candidate));Write-Output ('Applied: '+$r.entry.live)}
 Write-Output 'Three launchers changed. No tunnels/services/containers restarted. Profiles, credentials and ACL unchanged.'
 return
}
if(!$BackupPath){throw 'Rollback requires the exact recorded BackupPath'}
$approvedRoot=[IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'FortisG3ApiMigration'))+[IO.Path]::DirectorySeparatorChar
$fullBackup=[IO.Path]::GetFullPath($BackupPath)
if(!$fullBackup.StartsWith($approvedRoot,[StringComparison]::OrdinalIgnoreCase)){throw 'Backup must be under the owner migration backup directory'}
$b=Get-Content -LiteralPath $fullBackup -Raw|ConvertFrom-Json
if($b.planSha256 -ne '9EB03A985E71FDC32944DCDD8D327008C989C3091E0A0BB46B90EA4A8A0773D8' -or @($b.entries).Count -ne 3){throw 'Unexpected backup'}
$restore=@(foreach($e in $Plan.entries){
 $s=@($b.entries|Where-Object live -eq $e.live)
 if($s.Count -ne 1 -or $s[0].beforeSha256 -ne $e.beforeSha256 -or $s[0].afterSha256 -ne $e.afterSha256){throw 'Backup scope mismatch'}
 $bytes=[Convert]::FromBase64String($s[0].bytes)
 if((Get-Sha $bytes) -ne $e.beforeSha256){throw 'Backup content changed'}
 $row=@($Rows|Where-Object {$_.entry.live -eq $e.live})[0]
 [pscustomobject]@{live=$e.live;bytes=$bytes;current=$row.current;state=$row.state}
})
foreach($r in $restore){if($r.state -eq 'AFTER'){Write-Guarded $r.live $r.current $r.bytes;Write-Output ('Restored: '+$r.live)}}
Write-Output 'Launcher rollback complete. Backup and runtime retained. No restart performed.'
