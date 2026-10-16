#requires -Version 5.1
[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$CorePath,
 [Parameter(Mandatory=$true)][string]$ExpectedCoreSHA256,
 [Parameter(Mandatory=$true)][string]$FixtureParent
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if((Get-FileHash -LiteralPath $CorePath -Algorithm SHA256).Hash -cne $ExpectedCoreSHA256){throw 'Test core pin mismatch'}
. ([scriptblock]::Create([Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes($CorePath))))
$null=Assert-RmOrdinaryPath $FixtureParent
if(![IO.Directory]::Exists($FixtureParent)){throw 'Existing ordinary fixture parent required'}
$nonce=[guid]::NewGuid().ToString('N')
$root=Join-Path $FixtureParent ('repo-migration-test-'+$nonce)
if([IO.Directory]::Exists($root)){throw 'Fixture collision'}
$null=[IO.Directory]::CreateDirectory($root)
$marker=Join-Path $root '.fortis-synthetic-fixture'
[IO.File]::WriteAllText($marker,$nonce)
$script:checks=@();$cleanup=$false;$failure=$null
function Assert-Test([bool]$Value,[string]$Name) {
 if(!$Value){throw ('Assertion failed: '+$Name)}
 $script:checks+=[pscustomobject]@{Name=$Name;Pass=$true}
}
function Expect-Refusal([scriptblock]$Action,[string]$Name) {
 $refused=$false
 try {& $Action|Out-Null}catch {$refused=$true}
 Assert-Test $refused $Name
}
function New-Fixture([string]$Name) {
 $dir=Join-Path $root $Name;$null=[IO.Directory]::CreateDirectory($dir)
 $entries=@()
 foreach($kind in @('RepoRun','RepoControl')){
  $live=Join-Path $dir ($kind+'.live.ps1');$candidate=Join-Path $dir ($kind+'.candidate.ps1')
  $before=[Text.Encoding]::UTF8.GetBytes('FORTIS_SYNTHETIC_BEFORE_'+$kind)
  $after=[Text.Encoding]::UTF8.GetBytes('FORTIS_SYNTHETIC_AFTER_'+$kind)
  [IO.File]::WriteAllBytes($live,$before);[IO.File]::WriteAllBytes($candidate,$after)
  $entries+=[pscustomobject]@{Name=$kind;Live=$live;Candidate=$candidate;Before=(Get-RmSha $before);After=(Get-RmSha $after)}
 }
 return [pscustomobject]@{Entries=$entries;BackupRoot=(Join-Path $dir 'backups');Directory=$dir}
}
function Assert-Pair($Fixture,[string]$Expected,[string]$Name) {
 $ok=$true
 foreach($e in $Fixture.Entries){
  $hash=(Get-FileHash -LiteralPath $e.Live -Algorithm SHA256).Hash
  if($hash -cne $e.$Expected){$ok=$false}
 }
 Assert-Test $ok $Name
}
try {
 $f=New-Fixture 'standard'
 $p=Invoke-RepoMigrationCore -Entries $f.Entries -BackupRoot $f.BackupRoot
 Assert-Test ($p.Mode -eq 'Preview' -and $p.AllBefore -and $p.CandidatePinsMatch -and ![IO.Directory]::Exists($f.BackupRoot)) 'DefaultPreview_NoBackupOrWrites'
 Assert-Pair $f 'Before' 'Preview_PreservesBothTargets'
 $originalCandidate=[IO.File]::ReadAllBytes($f.Entries[0].Candidate)
 [IO.File]::WriteAllText($f.Entries[0].Candidate,'SYNTHETIC_CANDIDATE_DRIFT')
 Expect-Refusal {Invoke-RepoMigrationCore -Mode Apply -Entries $f.Entries -BackupRoot $f.BackupRoot} 'Apply_RefusesCandidateDrift'
 Assert-Pair $f 'Before' 'CandidateDrift_PreservesBothTargets'
 Assert-Test (![IO.Directory]::Exists($f.BackupRoot)) 'CandidateDrift_NoBackupCreated'
 [IO.File]::WriteAllBytes($f.Entries[0].Candidate,$originalCandidate)
 $a=Invoke-RepoMigrationCore -Mode Apply -Entries $f.Entries -BackupRoot $f.BackupRoot
 Assert-Test ($a.State -eq 'APPLIED' -and $a.FilesChanged -eq 2 -and $a.BackupCreated -and !$a.RuntimeRestarted) 'Apply_TwoFiles_ZeroRestarts'
 Assert-Pair $f 'After' 'Apply_ExactAfterBytes'
 $backupOriginal=[IO.File]::ReadAllBytes($a.BackupPath)
 Assert-Test ((Get-RmSha $backupOriginal) -ceq $a.BackupSHA256) 'Backup_HashReadback'
 $backupObject=[Text.Encoding]::UTF8.GetString($backupOriginal)|ConvertFrom-Json
 Assert-Test ($backupObject.Entries.Count -eq 2 -and (Get-RmSha ([Convert]::FromBase64String($backupObject.Entries[0].Bytes))) -ceq $f.Entries[0].Before) 'Backup_ScopeAndOriginalBytes'
 Assert-Test (([IO.File]::ReadAllText($a.JournalPath)).Contains('Apply_COMPLETE')) 'Apply_DurableCompletionJournal'
 $again=Invoke-RepoMigrationCore -Mode Apply -Entries $f.Entries -BackupRoot $f.BackupRoot
 Assert-Test ($again.State -eq 'ALREADY_AFTER_NO_BACKUP_PROVEN' -and $again.FilesChanged -eq 0 -and !$again.BackupCreated) 'RepeatedApply_Idempotent_NoNewBackupProof'
 [IO.File]::WriteAllText($a.BackupPath,'SYNTHETIC_BACKUP_TAMPER')
 Expect-Refusal {Invoke-RepoMigrationCore -Mode Rollback -Entries $f.Entries -BackupRoot $f.BackupRoot -BackupPath $a.BackupPath -ExpectedBackupSHA256 $a.BackupSHA256} 'Rollback_RefusesBackupTamper'
 Assert-Pair $f 'After' 'BackupTamper_PreservesTargets'
 [IO.File]::WriteAllBytes($a.BackupPath,$backupOriginal)
 $outside=Join-Path $root 'outside-sentinel.txt';[IO.File]::WriteAllText($outside,'FORTIS_SYNTHETIC_SENTINEL')
 $backupObject.Entries[0].Live=$outside
 $altered=[Text.Encoding]::UTF8.GetBytes(($backupObject|ConvertTo-Json -Depth 6))
 [IO.File]::WriteAllBytes($a.BackupPath,$altered)
 Expect-Refusal {Invoke-RepoMigrationCore -Mode Rollback -Entries $f.Entries -BackupRoot $f.BackupRoot -BackupPath $a.BackupPath -ExpectedBackupSHA256 (Get-RmSha $altered)} 'Rollback_RefusesValidHashWrongTargetScope'
 Assert-Test ([IO.File]::ReadAllText($outside) -ceq 'FORTIS_SYNTHETIC_SENTINEL') 'WrongBackupScope_PreservesOutsideSentinel'
 [IO.File]::WriteAllBytes($a.BackupPath,$backupOriginal)
 [IO.File]::WriteAllText($f.Entries[0].Live,'SYNTHETIC_FOREIGN_EDIT')
 $foreign=(Get-FileHash -LiteralPath $f.Entries[0].Live -Algorithm SHA256).Hash
 Expect-Refusal {Invoke-RepoMigrationCore -Mode Rollback -Entries $f.Entries -BackupRoot $f.BackupRoot -BackupPath $a.BackupPath -ExpectedBackupSHA256 $a.BackupSHA256} 'Rollback_RefusesForeignLiveEdit'
 Assert-Test ((Get-FileHash -LiteralPath $f.Entries[0].Live -Algorithm SHA256).Hash -ceq $foreign) 'ForeignEdit_NotOverwritten'
 [IO.File]::WriteAllBytes($f.Entries[0].Live,$originalCandidate)
 $held=$f.Entries[0].Candidate+'.held'
 [IO.File]::Move($f.Entries[0].Candidate,$held)
 $b=Invoke-RepoMigrationCore -Mode Rollback -Entries $f.Entries -BackupRoot $f.BackupRoot -BackupPath $a.BackupPath -ExpectedBackupSHA256 $a.BackupSHA256
 Assert-Test ($b.State -eq 'RESTORED' -and $b.FilesChanged -eq 2) 'Rollback_DoesNotRequireCandidateOrRuntime'
 Assert-Pair $f 'Before' 'Rollback_ExactBeforeBytes'
 [IO.File]::Move($held,$f.Entries[0].Candidate)
 $b2=Invoke-RepoMigrationCore -Mode Rollback -Entries $f.Entries -BackupRoot $f.BackupRoot -BackupPath $a.BackupPath -ExpectedBackupSHA256 $a.BackupSHA256
 Assert-Test ($b2.State -eq 'ALREADY_BEFORE' -and $b2.FilesChanged -eq 0) 'RepeatedRollback_Idempotent'
 Assert-Test ((Get-FileHash -LiteralPath $a.BackupPath -Algorithm SHA256).Hash -ceq $a.BackupSHA256) 'Rollback_PreservesImmutableBackup'
 $f2=New-Fixture 'partial'
 $script:rmTestOriginalWrite=(Get-Item Function:\Write-RmContent).ScriptBlock
 $script:rmTestFaultTarget=$f2.Entries[0].Live
 $caught=$null
 try {
  Set-Item Function:\Write-RmContent -Value {
   param([IO.FileStream]$Stream,[byte[]]$Bytes)
   & $script:rmTestOriginalWrite $Stream $Bytes
   if($Stream.Name -eq $script:rmTestFaultTarget){throw 'SYNTHETIC_FAULT_AFTER_FIRST_TARGET_WRITE'}
  }
  try {Invoke-RepoMigrationCore -Mode Apply -Entries $f2.Entries -BackupRoot $f2.BackupRoot|Out-Null}catch {$caught=$_.Exception}
 } finally {Set-Item Function:\Write-RmContent -Value $script:rmTestOriginalWrite}
 Assert-Test ($null -ne $caught -and $null -ne $caught.Data['BackupPath'] -and $null -ne $caught.Data['BackupSHA256']) 'PartialFailure_ReturnsRecordedBackupIdentity'
 $partial=Invoke-RepoMigrationCore -Entries $f2.Entries -BackupRoot $f2.BackupRoot
 Assert-Test ($partial.Rows[0].State -eq 'AFTER' -and $partial.Rows[1].State -eq 'BEFORE') 'PartialFailure_ActualMixedStateObserved'
 Expect-Refusal {Invoke-RepoMigrationCore -Mode Apply -Entries $f2.Entries -BackupRoot $f2.BackupRoot} 'PartialPair_ApplyRefusesBlindRetry'
 $recovered=Invoke-RepoMigrationCore -Mode Rollback -Entries $f2.Entries -BackupRoot $f2.BackupRoot -BackupPath $caught.Data['BackupPath'] -ExpectedBackupSHA256 $caught.Data['BackupSHA256']
 Assert-Test ($recovered.FilesChanged -eq 1) 'PartialRollback_OnlyChangedFileRestored'
 Assert-Pair $f2 'Before' 'PartialRollback_BothBefore'
 if([Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT){
 $f3=New-Fixture 'contention'
 $lock=[IO.File]::Open($f3.Entries[1].Live,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::Read)
 try {Expect-Refusal {Invoke-RepoMigrationCore -Mode Apply -Entries $f3.Entries -BackupRoot $f3.BackupRoot} 'ConcurrentWriter_ApplyRefused'}finally{$lock.Dispose()}
 Assert-Pair $f3 'Before' 'Contention_NoTargetWrites'
 Assert-Test (![IO.Directory]::Exists($f3.BackupRoot)) 'Contention_NoBackupCreated'
 $release=[IO.File]::Open($f3.Entries[0].Live,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None);$release.Dispose()
 Assert-Test $true 'Failure_ReleasesPreviouslyAcquiredTargetHandle'
 } else {
  $script:checks+=[pscustomobject]@{Name='Windows_FileShare_Contention';Pass=$null;Skipped=$true;Reason='Windows file sharing semantics require Windows acceptance'}
 }
 $scopeFixture=New-Fixture 'scope'
 $scopeEntries=@($scopeFixture.Entries[0])
 Expect-Refusal {Invoke-RepoMigrationCore -Mode Apply -Entries $scopeEntries -BackupRoot $scopeFixture.BackupRoot} 'OneFileScope_Refused'
 $expectedCount=if([Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT){31}else{28}
 $testSuccess=$checks.Count -eq $expectedCount
 Assert-Test $testSuccess 'ExpectedAssertionsComplete'
} catch {$failure=$_.Exception.Message}
if(!$failure){
 try {
  if([IO.File]::ReadAllText($marker) -cne $nonce){throw 'Cleanup marker mismatch'}
  $items=@(Get-ChildItem -LiteralPath $root -Force -Recurse -ErrorAction Stop)
  if($items.Count -gt 128 -or @($items|Where-Object {($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0}).Count){throw 'Cleanup bounds/reparse refusal'}
  if((Get-Item -LiteralPath $root).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Cleanup root reparse refusal'}
  [IO.Directory]::Delete($root,$true);$cleanup=![IO.Directory]::Exists($root)
 } catch {$failure=$_.Exception.Message}
}
[pscustomobject]@{
 Check='REPO_MIGRATION_SYNTHETIC_FAILURE_AND_RECOVERY';Utc=[DateTime]::UtcNow.ToString('o')
 CoreSHA256=$ExpectedCoreSHA256;PowerShell=$PSVersionTable.PSVersion.ToString();Platform=$PSVersionTable.PSEdition
 FixtureRoot=$root;Checks=$checks;CheckCount=$checks.Count;Cleanup=$cleanup
 Passed=(!$failure -and $cleanup);Error=$failure
 LiveLaunchersChanged=0;RuntimeRestarted=$false;ProductionWrapperApplyCalled=$false
}|ConvertTo-Json -Depth 6
if($failure){exit 1}
