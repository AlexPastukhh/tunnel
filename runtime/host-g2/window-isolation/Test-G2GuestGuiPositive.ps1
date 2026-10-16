#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][int]$ExpectedGuestSession)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
$session=[Diagnostics.Process]::GetCurrentProcess().SessionId
if($id.User.Value -ne 'S-1-5-21-303538662-3368424508-2654684973-1009' -or $session -ne $ExpectedGuestSession -or $session -le 0 -or @($id.Groups|Where-Object Value -eq 'S-1-5-32-544').Count){throw 'Exact ordinary guest session required'}
$p=Join-Path ([Environment]::GetFolderPath('CommonDocuments')) 'Fortis-G3-SessionGuiBoundary-8F1BC80C.ps1'
$bytes=[IO.File]::ReadAllBytes($p)
$sha=[Security.Cryptography.SHA256]::Create()
try{$hash=([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','')}finally{$sha.Dispose()}
if($hash -cne '8F1BC80CA8A2C9625B32340203ABA5AEFEDFBB0BC244AA2C5E1FF7CDBC90B222'){throw 'Pinned own GUI helper differs'}
$null=& ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($bytes))) -Mode Validate -CapturedSHA256 $hash
$objects=[FortisG3SessionBoundary]::OwnObjects()
$expected='\Sessions\'+$session+'\Windows\WindowStations\WinSta0'
if($objects.Station -ine 'WinSta0' -or $objects.Desktop -ine 'Default' -or $objects.StationPath -ine $expected){throw 'Own guest WinSta0/Default not established'}
$gui=[FortisG3SessionBoundary]::GuestGui($false)
[pscustomobject]@{
 Check='G2_OWN_GUI_CLIPBOARD_POSITIVE';Utc=[DateTime]::UtcNow.ToString('o');Sid=$id.User.Value;Session=$session;HelperSHA256=$hash
 OwnObjects=$objects;Gui=$gui;OwnWindowPass=($gui.WindowCreated -and $gui.WindowVisible -and $gui.WindowDestroyed)
 ClipboardPass=($gui.Clipboard -eq 'ROUNDTRIP_EXACT_MARKER' -and $gui.ClipboardCleanup -eq 'EMPTIED_OWN_MARKER')
 ExistingClipboardReplacementAllowed=$false;OwnerContentReads=0;OwnerProbesExecuted=0;Captures=0;InputInjection=0
}|ConvertTo-Json -Depth 5
