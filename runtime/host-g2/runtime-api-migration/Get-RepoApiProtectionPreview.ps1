#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$CapturedSHA256)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
if($id.User.Value -ne 'S-1-5-21-303538662-3368424508-2654684973-1001' -or [Diagnostics.Process]::GetCurrentProcess().SessionId -ne 1){throw 'Exact owner observer required'}
if($CapturedSHA256 -notmatch '^[A-F0-9]{64}$'){throw 'Captured source hash required'}
$bundle='C:\Users\alexa\Repos\tunnel\runtime\host-g2\runtime-api-migration'
$entries=@(
 [pscustomobject]@{Name='RepoRun';Live='C:\Users\alexa\chatgpt-repo-mode\run-tunnel.ps1';Candidate=($bundle+'\repo-run-tunnel.ps1');Before='3877266C3C97BECC82045BE16D994981EB4F8973353B285236DF9CAAC158A5A3';After='52848CDA49FECB4D78589E9979781A28D114A92F694CF75BC66EA6D4412EB93B'},
 [pscustomobject]@{Name='RepoControl';Live='C:\Users\alexa\chatgpt-repo-mode\control.ps1';Candidate=($bundle+'\repo-control.ps1');Before='E80E209B4758B194D2BCC7DCAFDFB83D296289E29A543F192E6726538641AE34';After='605F9D54A0A35FF3011DC44356A733F975A8993F1225FF53378A6B7880A193C5'}
)
$files=@()
foreach($entry in $entries){
 $live=(Get-FileHash -LiteralPath $entry.Live -Algorithm SHA256).Hash
 $candidate=(Get-FileHash -LiteralPath $entry.Candidate -Algorithm SHA256).Hash
 if($candidate -cne $entry.After){throw ('Candidate drift: '+$entry.Name)}
 if($live -cne $entry.Before){throw ('Live BEFORE drift: '+$entry.Name)}
 foreach($path in @($entry.Live,$entry.Candidate)){
  $errors=$null;$tokens=$null
  $null=[Management.Automation.Language.Parser]::ParseFile($path,[ref]$tokens,[ref]$errors)
  if($errors.Count){throw ('PowerShell parse failed: '+$entry.Name)}
 }
 $files+=[pscustomobject]@{Name=$entry.Name;Live=$entry.Live;Candidate=$entry.Candidate;LiveSHA256=$live;CandidateSHA256=$candidate;State='BEFORE';WindowsParserPass=$true}
}
$runtime='C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe'
$runtimeHash=(Get-FileHash -LiteralPath $runtime -Algorithm SHA256).Hash
if($runtimeHash -cne 'A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A'){throw 'Installed runtime drift'}
$p=Get-CimInstance Win32_Process -Property ProcessId,ParentProcessId,Name,SessionId,CreationDate,ExecutablePath -Filter 'ProcessId=22488'
if(!$p -or $p.Name -ne 'tunnel-client.exe' -or $p.SessionId -ne 1 -or $p.CreationDate.ToUniversalTime().ToString('o') -cne '2026-10-15T18:59:53.4046800Z' -or $p.ExecutablePath -ine 'C:\Tools\tunnel-client\tunnel-client.exe'){throw 'Repo process fingerprint drift'}
$o=Invoke-CimMethod -InputObject $p -MethodName GetOwnerSid
if($o.ReturnValue -ne 0 -or $o.Sid -ne $id.User.Value){throw 'Repo owner SID drift'}
$fullHash=(Get-FileHash -LiteralPath $p.ExecutablePath -Algorithm SHA256).Hash
if($fullHash -cne '1946DE55A038313A9B9B2458D05FE1719FA9CF1F20A94DD5F38FC26A98BFDD42'){throw 'Full client drift'}
$listeners=@(Get-NetTCPConnection -State Listen -OwningProcess $p.ProcessId -ErrorAction Stop|Select-Object LocalAddress,LocalPort)
[pscustomobject]@{
 Check='REPO_API_PROTECTION_PREVIEW_ONLY';Utc=[DateTime]::UtcNow.ToString('o');SourceSHA256=$CapturedSHA256
 Files=$files;InstalledRuntimeSHA256=$runtimeHash
 RepoProcess=[pscustomobject]@{Pid=$p.ProcessId;Sid=$o.Sid;Session=$p.SessionId;CreatedUtc=$p.CreationDate.ToUniversalTime().ToString('o');ExeSHA256=$fullHash;TcpListeners=$listeners;ProfileMappingEvidence='E25 exact unchanged fingerprint'}
 PreviewComplete=$true;ReadyForApply=$false;Mode='PREVIEW_ONLY_NO_APPLY_OR_ROLLBACK_IMPLEMENTATION'
 Unresolved=@('Read-surface privacy assessment: readyz raw errors, metrics paths, bounded health details','Actual retained Repo runtime-only Docker/MCP compatibility not yet verified','Protection choice and independent two-file apply/rollback not implemented')
 ProposedFileCount=2;ActualFilesChanged=0;BackupCreated=$false;HttpRequests=0;RuntimeRestarted=$false
 ProfilesRead=$false;KeysRead=$false;ArgvRead=$false;EnvironmentRead=$false
 Scope='REPO_ONLY; OWNER_HOST_AND_G2_NOT_CHANGED'
}|ConvertTo-Json -Depth 7
