#requires -Version 5.1
[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][int]$ExpectedGuestSession,
 [Parameter(Mandatory=$true)][string]$OwnerWitnessBase64
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
$session=[Diagnostics.Process]::GetCurrentProcess().SessionId
if($id.User.Value -ne 'S-1-5-21-303538662-3368424508-2654684973-1009' -or $session -ne $ExpectedGuestSession -or $session -le 0 -or @($id.Groups | Where-Object Value -eq 'S-1-5-32-544').Count){throw 'Exact ordinary guest session required'}
if($OwnerWitnessBase64.Length -gt 8192){throw 'Witness too large'}
$w=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($OwnerWitnessBase64)) | ConvertFrom-Json
$pin='8F1BC80CA8A2C9625B32340203ABA5AEFEDFBB0BC244AA2C5E1FF7CDBC90B222'
$age=[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()-[long]$w.CreatedUnixSeconds
if($w.Schema -ne 3 -or $w.SourceSHA256 -cne $pin -or $w.Sid -ne 'S-1-5-21-303538662-3368424508-2654684973-1001' -or $w.Session -le 0 -or $w.Session -eq $session -or $age -lt 0 -or $age -gt 120){throw 'Invalid/stale owner metadata witness'}
$ownerPath='\Sessions\'+[int]$w.Session+'\Windows\WindowStations\WinSta0'
if($w.StationPath -ine $ownerPath -or $w.DesktopName -ine 'Default' -or $w.DesktopObjectName -notin @('\Default',($ownerPath+'\Default'))){throw 'Invalid owner object names'}
$p=Join-Path ([Environment]::GetFolderPath('CommonDocuments')) 'Fortis-G3-SessionGuiBoundary-8F1BC80C.ps1'
$b=[IO.File]::ReadAllBytes($p)
$sha=[Security.Cryptography.SHA256]::Create()
try{$hash=([BitConverter]::ToString($sha.ComputeHash($b))).Replace('-','')}finally{$sha.Dispose()}
if($hash -cne $pin){throw 'Helper hash mismatch'}
$null=& ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($b))) -Mode Validate -CapturedSHA256 $hash
$own=[FortisG3SessionBoundary]::OwnObjects()
$ownPath='\Sessions\'+$session+'\Windows\WindowStations\WinSta0'
if($own.Station -ine 'WinSta0' -or $own.Desktop -ine 'Default' -or $own.StationPath -ine $ownPath){throw 'Own objects not established'}
$cases=@(
 @('Station','ACCESSCLIPBOARD',4),@('Station','READSCREEN',512),
 @('Station','WRITE_DAC',262144),@('Station','WRITE_OWNER',524288),
 @('Desktop','READOBJECTS',1),@('Desktop','HOOKCONTROL',8),
 @('Desktop','WRITEOBJECTS',128),@('Desktop','SWITCHDESKTOP',256),
 @('Desktop','WRITE_DAC_WITH_READ_WRITE',262273),@('Desktop','WRITE_OWNER_WITH_READ_WRITE',524417)
)
$rows=@()
foreach($case in $cases){
 $desktop=$case[0] -eq 'Desktop'
 $name=if($desktop){'Default'}else{$null}
 $positive=[FortisG3SessionBoundary]::NativeOpen($ownPath,$name,[uint32]$case[2])
 $negative=[FortisG3SessionBoundary]::NativeOpen($ownerPath,$name,[uint32]$case[2])
 $ownNameOk=if($desktop){$positive.RootResolvedPath -ieq $ownPath -and $positive.ResolvedPath -in @('\Default',($ownPath+'\Default'))}else{$positive.ResolvedPath -ieq $ownPath}
 $ownPass=$positive.Opened -and $positive.Closed -and $positive.RootClosed -and !$positive.MethodError -and $ownNameOk
 $verdict='INCONCLUSIVE'
 if($ownPass -and $negative.Closed -and $negative.RootClosed -and !$negative.MethodError){
  if($negative.Opened){
   $ownerNameOk=if($desktop){$negative.RootResolvedPath -ieq $ownerPath -and $negative.ResolvedPath -in @('\Default',($ownerPath+'\Default'))}else{$negative.ResolvedPath -ieq $ownerPath}
   if($ownerNameOk){$verdict='OWNER_CAPABILITY_OPENED'}else{$verdict='INCONCLUSIVE_TARGET_NAME'}
  }
  elseif($negative.FailureStage -eq 'TARGET' -and $negative.Win32 -eq 5){$verdict='DENY_ACCESS_5'}
  elseif($desktop -and $negative.FailureStage -eq 'STATION_ROOT' -and $negative.RootWin32 -eq 5){$verdict='BLOCKED_AT_STATION_ROOT_5'}
 }
 $rows += [pscustomobject]@{Object=$case[0];Right=$case[1];Mask=$case[2];OwnPositivePass=$ownPass;Verdict=$verdict;Own=$positive;Owner=$negative}
}
[pscustomobject]@{
 Check='G2_OWNER_GUI_FRESH_OPEN_CAPABILITIES';Utc=[DateTime]::UtcNow.ToString('o')
 GuestSid=$id.User.Value;GuestSession=$session;OwnerSession=$w.Session;OwnerWitnessPid=$w.Pid;OwnerWitnessCreated=$w.ProcessCreated
 HelperSHA256=$hash;WitnessAgeSeconds=$age;GuestObjects=$own;Rows=$rows
 Overall='PROVISIONAL_UNTIL_OWNER_CHANNEL_AFTER_CHECK'
 ForeignProcessQueriesFromGuest=0;OwnerContentReads=0;ClipboardOperations=0;Captures=0;InputInjection=0;AclWrites=0;StationDesktopSwitches=0
 ExistingHandlesInventoried=$false;ClipboardBridgesChecked=$false
}|ConvertTo-Json -Depth 7
