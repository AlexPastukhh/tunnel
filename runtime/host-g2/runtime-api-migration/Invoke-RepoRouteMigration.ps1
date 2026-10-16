#requires -Version 5.1
[CmdletBinding()]
param(
 [ValidateSet('Preview','Apply','Rollback')][string]$Mode='Preview',
 [string]$BackupPath,[string]$ExpectedBackupSHA256
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if([Environment]::OSVersion.Platform -ne [System.PlatformID]::Win32NT){throw 'Production wrapper requires Windows'}
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
if($id.User.Value -ne 'S-1-5-21-303538662-3368424508-2654684973-1001'){throw 'Run only as owner alexa; no elevation is requested'}
$bundle='C:\Users\alexa\Repos\tunnel\runtime\host-g2\runtime-api-migration'
$corePath=Join-Path $bundle 'RepoRouteMigration.Core.ps1'
$corePin='46CEE432DE4460F744517FD2F0A49073DF41B28BB1BFE68F597877DA62856BF8'
if((Get-FileHash -LiteralPath $corePath -Algorithm SHA256).Hash -cne $corePin){throw 'Core source hash drift'}
$engine=[scriptblock]::Create([Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes($corePath)))
. $engine
$entries=@(
 [pscustomobject]@{Name='RepoRun';Live='C:\Users\alexa\chatgpt-repo-mode\run-tunnel.ps1';Candidate=($bundle+'\repo-run-tunnel.ps1');Before='3877266C3C97BECC82045BE16D994981EB4F8973353B285236DF9CAAC158A5A3';After='52848CDA49FECB4D78589E9979781A28D114A92F694CF75BC66EA6D4412EB93B'},
 [pscustomobject]@{Name='RepoControl';Live='C:\Users\alexa\chatgpt-repo-mode\control.ps1';Candidate=($bundle+'\repo-control.ps1');Before='E80E209B4758B194D2BCC7DCAFDFB83D296289E29A543F192E6726538641AE34';After='605F9D54A0A35FF3011DC44356A733F975A8993F1225FF53378A6B7880A193C5'}
)
if($Mode -ne 'Rollback'){
 $runtime='C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe'
 if((Get-FileHash -LiteralPath $runtime -Algorithm SHA256).Hash -cne 'A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A'){throw 'Installed runtime hash drift'}
 foreach($e in $entries){
  $errors=$null;$tokens=$null
  $null=[Management.Automation.Language.Parser]::ParseFile($e.Candidate,[ref]$tokens,[ref]$errors)
  if($errors.Count){throw 'Candidate PowerShell parse failed'}
 }
}
$backupRoot=Join-Path $env:LOCALAPPDATA 'FortisRepoApiMigration'
try {
 $result=Invoke-RepoMigrationCore -Mode $Mode -Entries $entries -BackupRoot $backupRoot -BackupPath $BackupPath -ExpectedBackupSHA256 $ExpectedBackupSHA256
 [pscustomobject]@{
  Check='REPO_ONLY_GUARDED_FILE_MIGRATION';Utc=[DateTime]::UtcNow.ToString('o')
  Mode=$Mode;OwnerSid=$id.User.Value;CoreSHA256=$corePin;FileResult=$result
  Scope='EXACT_REPO_RUN_AND_CONTROL_ONLY';InstalledRuntimeChanged=$false
  RuntimeRestarted=$false;RuntimeBoundaryAccepted=$false
  HostOrG2Changed=$false;ContainerStopped=$false;ProfileOrKeyChanged=$false;AclOrNetworkChanged=$false
  Note='File state is not live runtime acceptance. Apply/Rollback never restart a process.'
 }|ConvertTo-Json -Depth 8
} catch {
 [pscustomobject]@{
  Check='REPO_ONLY_GUARDED_FILE_MIGRATION';Mode=$Mode;State='STOPPED_INSPECT_ACTUAL_STATE'
  BackupPath=$_.Exception.Data['BackupPath'];BackupSHA256=$_.Exception.Data['BackupSHA256']
  RuntimeRestarted=$false;Error=$_.Exception.Message
 }|ConvertTo-Json -Depth 5
 throw
}
