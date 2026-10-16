#requires -Version 5.1
# Internal two-file engine. Production paths and authorization belong to the pinned wrapper.
Set-StrictMode -Version Latest
function Get-RmSha([byte[]]$Bytes) {
 $s=[Security.Cryptography.SHA256]::Create()
 try {([BitConverter]::ToString($s.ComputeHash($Bytes))).Replace('-','')} finally {$s.Dispose()}
}
function Assert-RmOrdinaryPath([string]$Path) {
 $full=[IO.Path]::GetFullPath($Path)
 if(![IO.Path]::IsPathRooted($Path)){throw 'Absolute path required'}
 $cursor=$full
 while($cursor){
  if([IO.File]::Exists($cursor) -or [IO.Directory]::Exists($cursor)){
   if(([IO.File]::GetAttributes($cursor) -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'Reparse path refused'}
  } else {
   # GetAttributes also detects dangling links instead of treating them as new paths.
   try {
    $a=[IO.File]::GetAttributes($cursor)
    if(($a -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'Reparse path refused'}
   } catch [IO.FileNotFoundException] {} catch [IO.DirectoryNotFoundException] {}
  }
  $parent=[IO.Path]::GetDirectoryName($cursor)
  if(!$parent -or $parent -eq $cursor){break}
  $cursor=$parent
 }
 return $full
}
function Read-RmStream([IO.Stream]$Stream) {
 if($Stream.Length -gt 131072){throw 'Selected script/record exceeds bounded size'}
 $b=New-Object byte[] ([int]$Stream.Length)
 $Stream.Position=0;$offset=0
 while($offset -lt $b.Length){
  $n=$Stream.Read($b,$offset,$b.Length-$offset)
  if($n -le 0){throw 'Short file read'}
  $offset+=$n
 }
 return ,$b
}
function Read-RmFile([string]$Path) {
 $null=Assert-RmOrdinaryPath $Path
 $f=[IO.File]::Open($Path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)
 try {return ,(Read-RmStream $f)} finally {$f.Dispose()}
}
function Write-RmContent([IO.FileStream]$Stream,[byte[]]$Bytes) {
 $Stream.Position=0;$Stream.Write($Bytes,0,$Bytes.Length);$Stream.SetLength($Bytes.Length);$Stream.Flush($true)
 if((Get-RmSha (Read-RmStream $Stream)) -cne (Get-RmSha $Bytes)){throw 'Write read-back mismatch'}
}
function New-RmRecord([string]$Path,[byte[]]$Bytes) {
 $null=Assert-RmOrdinaryPath $Path
 $f=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
 try {Write-RmContent $f $Bytes} finally {$f.Dispose()}
}
function Add-RmJournal([IO.FileStream]$Stream,[string]$Stage) {
 $text=([pscustomobject]@{Utc=[DateTime]::UtcNow.ToString('o');Stage=$Stage}|ConvertTo-Json -Compress)+[char]10
 $b=[Text.Encoding]::UTF8.GetBytes($text)
 $Stream.Position=$Stream.Length;$Stream.Write($b,0,$b.Length);$Stream.Flush($true)
}
function Invoke-RepoMigrationCore {
 [CmdletBinding()]
 param(
  [ValidateSet('Preview','Apply','Rollback')][string]$Mode='Preview',
  [Parameter(Mandatory=$true)][object[]]$Entries,
  [Parameter(Mandatory=$true)][string]$BackupRoot,
  [string]$BackupPath,[string]$ExpectedBackupSHA256
 )
 $ErrorActionPreference='Stop'
 $plan='FORTIS_REPO_RUNTIME_ONLY_20261016_V1'
 if($Entries.Count -ne 2 -or (($Entries.Name -join '|') -cne 'RepoRun|RepoControl')){throw 'Exact two-entry Repo scope required'}
 $backupRootFull=Assert-RmOrdinaryPath $BackupRoot
 $rootPrefix=$backupRootFull.TrimEnd([IO.Path]::DirectorySeparatorChar,[IO.Path]::AltDirectorySeparatorChar)+[IO.Path]::DirectorySeparatorChar
 $seen=@{};$prepared=@();$handles=@();$journal=$null;$recordPath=$null;$recordHash=$null
 foreach($e in $Entries){
  if($e.Before -cnotmatch '^[A-F0-9]{64}$' -or $e.After -cnotmatch '^[A-F0-9]{64}$' -or $e.Before -ceq $e.After){throw 'Invalid fixed hash contract'}
  $live=Assert-RmOrdinaryPath $e.Live
  $candidate=Assert-RmOrdinaryPath $e.Candidate
  foreach($p in @($live,$candidate)){
   if($seen.ContainsKey($p)){throw 'Duplicate source/target path'}
   $seen[$p]=$true
   if($p.StartsWith($rootPrefix,[StringComparison]::OrdinalIgnoreCase)){throw 'Source/target inside backup root refused'}
  }
  $candidateBytes=$null;$candidateMatch=$null
  if($Mode -ne 'Rollback'){
   $candidateBytes=Read-RmFile $candidate
   $candidateMatch=(Get-RmSha $candidateBytes) -ceq $e.After
   if($Mode -eq 'Apply' -and !$candidateMatch){throw 'Candidate hash drift'}
  }
  $prepared+=@{Name=$e.Name;Live=$live;Before=$e.Before;After=$e.After;CandidateBytes=$candidateBytes;CandidateMatch=$candidateMatch}
 }
 $restore=$null
 if($Mode -eq 'Rollback'){
  if(!$BackupPath -or $ExpectedBackupSHA256 -cnotmatch '^[A-F0-9]{64}$'){throw 'Rollback requires recorded path and SHA256'}
  $recordPath=Assert-RmOrdinaryPath $BackupPath
  if(!$recordPath.StartsWith($rootPrefix,[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetFileName($recordPath) -cne 'backup.json'){throw 'Backup outside fixed root/scope'}
  $raw=Read-RmFile $recordPath;$recordHash=Get-RmSha $raw
  if($recordHash -cne $ExpectedBackupSHA256){throw 'Backup hash drift'}
  $b=[Text.Encoding]::UTF8.GetString($raw)|ConvertFrom-Json
  if($b.Schema -ne 1 -or $b.Plan -cne $plan -or @($b.Entries).Count -ne 2){throw 'Backup schema/scope mismatch'}
  $restore=@()
  for($i=0;$i -lt 2;$i++){
   $e=$prepared[$i];$saved=$b.Entries[$i]
   if($saved.Name -cne $e.Name -or $saved.Live -cne $e.Live -or $saved.Before -cne $e.Before -or $saved.After -cne $e.After){throw 'Backup target/hash contract mismatch'}
   $bytes=[Convert]::FromBase64String($saved.Bytes)
   if((Get-RmSha $bytes) -cne $e.Before){throw 'Backup content drift'}
   $restore+=@{Bytes=$bytes}
  }
 }
 try {
  # All target handles stay held across preflight, backup, writes and read-back.
  foreach($e in $prepared){
   $access=if($Mode -eq 'Preview'){[IO.FileAccess]::Read}else{[IO.FileAccess]::ReadWrite}
   $f=[IO.File]::Open($e.Live,[IO.FileMode]::Open,$access,[IO.FileShare]::Read)
   $handles+=,$f
   $bytes=Read-RmStream $f;$hash=Get-RmSha $bytes
   $e.OldBytes=$bytes;$e.Current=$hash
   $e.State=if($hash -ceq $e.Before){'BEFORE'}elseif($hash -ceq $e.After){'AFTER'}else{'DRIFT'}
  }
  if($Mode -eq 'Preview'){
   return [pscustomobject]@{Mode=$Mode;Rows=@($prepared|ForEach-Object {[pscustomobject]@{Name=$_.Name;Live=$_.Live;State=$_.State;CurrentSHA256=$_.Current;CandidateMatches=$_.CandidateMatch}});AllBefore=(@($prepared|Where-Object {$_.State -ne 'BEFORE'}).Count -eq 0);CandidatePinsMatch=(@($prepared|Where-Object {!$_.CandidateMatch}).Count -eq 0);FilesChanged=0;BackupCreated=$false;RuntimeRestarted=$false}
  }
  if(@($prepared|Where-Object {$_.State -eq 'DRIFT'}).Count){throw 'Unknown live drift; no overwrite permitted'}
  if($Mode -eq 'Apply'){
   if(@($prepared|Where-Object {$_.State -eq 'AFTER'}).Count -eq 2){
    return [pscustomobject]@{Mode=$Mode;State='ALREADY_AFTER_NO_BACKUP_PROVEN';FilesChanged=0;BackupCreated=$false;RuntimeRestarted=$false}
   }
   if(@($prepared|Where-Object {$_.State -ne 'BEFORE'}).Count){throw 'Known partial pair; use recorded rollback'}
   if(![IO.Directory]::Exists($backupRootFull)){$null=[IO.Directory]::CreateDirectory($backupRootFull)}
   $null=Assert-RmOrdinaryPath $backupRootFull
   $dir=Join-Path $backupRootFull ([guid]::NewGuid().ToString('N'))
   if([IO.Directory]::Exists($dir)){throw 'Backup nonce collision'}
   $null=[IO.Directory]::CreateDirectory($dir);$null=Assert-RmOrdinaryPath $dir
   $recordPath=Join-Path $dir 'backup.json'
   $saved=@($prepared|ForEach-Object {[pscustomobject]@{Name=$_.Name;Live=$_.Live;Before=$_.Before;After=$_.After;Bytes=[Convert]::ToBase64String($_.OldBytes)}})
   $record=[pscustomobject]@{Schema=1;Plan=$plan;CreatedUtc=[DateTime]::UtcNow.ToString('o');Entries=$saved}
   $raw=[Text.Encoding]::UTF8.GetBytes(($record|ConvertTo-Json -Depth 6))
   New-RmRecord $recordPath $raw
   $recordHash=Get-RmSha (Read-RmFile $recordPath)
   if($recordHash -cne (Get-RmSha $raw)){throw 'Backup read-back failed'}
  }
  if($Mode -eq 'Rollback' -and @($prepared|Where-Object {$_.State -eq 'AFTER'}).Count -eq 0){
   return [pscustomobject]@{Mode=$Mode;State='ALREADY_BEFORE';FilesChanged=0;BackupCreated=$false;BackupPath=$recordPath;BackupSHA256=$recordHash;RuntimeRestarted=$false}
  }
  $journalPath=Join-Path (Split-Path -Parent $recordPath) ('journal-'+[guid]::NewGuid().ToString('N')+'.jsonl')
  $journal=[IO.File]::Open($journalPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
  Add-RmJournal $journal ($Mode+'_PREPARED')
  $changed=0
  for($i=0;$i -lt 2;$i++){
   $e=$prepared[$i]
   if($Mode -eq 'Rollback' -and $e.State -eq 'BEFORE'){continue}
   $bytes=if($Mode -eq 'Apply'){$e.CandidateBytes}else{$restore[$i].Bytes}
   Write-RmContent $handles[$i] $bytes;$changed++
   Add-RmJournal $journal ($e.Name+'_VERIFIED')
  }
  Add-RmJournal $journal ($Mode+'_COMPLETE')
  return [pscustomobject]@{Mode=$Mode;State=if($Mode -eq 'Apply'){'APPLIED'}else{'RESTORED'};FilesChanged=$changed;BackupCreated=($Mode -eq 'Apply');BackupPath=$recordPath;BackupSHA256=$recordHash;JournalPath=$journalPath;RuntimeRestarted=$false}
 } catch {
  if($journal){try{Add-RmJournal $journal 'STOPPED_INSPECT_ACTUAL_STATE'}catch{}}
  $failure=[InvalidOperationException]::new('Repo migration stopped; inspect actual state before retrying. '+$_.Exception.Message)
  if($recordPath){$failure.Data['BackupPath']=$recordPath}
  if($recordHash){$failure.Data['BackupSHA256']=$recordHash}
  throw $failure
 } finally {
  if($journal){$journal.Dispose()}
  foreach($f in $handles){$f.Dispose()}
 }
}
