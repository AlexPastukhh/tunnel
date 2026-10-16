param(
 [ValidateSet('Preview')][string]$Mode='Preview',
 [string]$SourceDirectory='C:\Users\alexa\Repos\tunnel\runtime\host-g2\window-isolation'
)
$ErrorActionPreference='Stop'
$G2Sid='S-1-5-21-303538662-3368424508-2654684973-1009'
$OwnerSid='S-1-5-21-303538662-3368424508-2654684973-1001'
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
$principal=New-Object Security.Principal.WindowsPrincipal($identity)
if($identity.User.Value -ne $OwnerSid){throw 'Preview must run as owner alexa, not as G2'}
$session=[Diagnostics.Process]::GetCurrentProcess().SessionId
if($session -eq 0){throw 'Run locally in the owner interactive session'}
if(('G2WindowBoundary' -as [type]) -or ('G2ProcessInventory' -as [type])){throw 'Use a fresh PowerShell process'}
function Get-BytesHash([byte[]]$Bytes){
 $sha=[Security.Cryptography.SHA256]::Create()
 try{return ([BitConverter]::ToString($sha.ComputeHash($Bytes))).Replace('-','')}finally{$sha.Dispose()}
}
$components=@{
 'WindowBoundaryProbe.cs'='29CF0CFA83412084F3573747DEAD73BAFC90E3121B34FE1C9EEF0BB347F838B2'
 'ProcessInventory.cs'='6A59D74F1C6261DAF44E04BA1830D559543879A9F0BCFB4E8C32D5AB36BACDD3'
}
foreach($name in $components.Keys){
 $bytes=[IO.File]::ReadAllBytes((Join-Path $SourceDirectory $name))
 if((Get-BytesHash $bytes) -ne $components[$name]){throw ('Component changed: '+$name)}
 Add-Type -TypeDefinition ([Text.Encoding]::UTF8.GetString($bytes))
}
$station=[G2WindowBoundary]::GetProcessWindowStation()
$desktop=[G2WindowBoundary]::DesktopHandle()
if([G2WindowBoundary]::Name($station) -ne 'WinSta0' -or [G2WindowBoundary]::Name($desktop) -ne 'Default'){throw 'Unexpected owner station/desktop'}
$objects=@()
foreach($s in @(@{Kind='Station';Handle=$station;Mask=0xf037f;Desktop=$false},@{Kind='Desktop';Handle=$desktop;Mask=0xf01ff;Desktop=$true})){
 $before=[G2WindowBoundary]::Read($s.Handle)
 $after=[G2WindowBoundary]::Deny($before,$G2Sid,$s.Mask,$false)
 $objects += [pscustomobject]@{Kind=$s.Kind;Name=[G2WindowBoundary]::Name($s.Handle);BeforeHash=(Get-BytesHash $before);ProposedHash=(Get-BytesHash $after);OwnerWriteDacBefore=[G2WindowBoundary]::Access($before,262144,$s.Desktop);OwnerWriteDacAfter=[G2WindowBoundary]::Access($after,262144,$s.Desktop);DenySid=$G2Sid;DenyMask=('0x'+$s.Mask.ToString('X'))}
}
$debugEntered=$false
try{
 if($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){[Diagnostics.Process]::EnterDebugMode();$debugEntered=$true}
 $inventory=@([G2ProcessInventory]::ForSid($G2Sid,$session))
}finally{if($debugEntered){[Diagnostics.Process]::LeaveDebugMode()}}
$unknown=@($inventory|Where-Object{$_ -like 'UNKNOWN:*'})
$g2=@($inventory|Where-Object{$_ -notlike 'UNKNOWN:*'})
[pscustomobject]@{At=[DateTime]::UtcNow.ToString('o');Mode=$Mode;Sid=$identity.User.Value;Admin=$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator);Session=$session;Objects=$objects;G2Processes=$g2;UnknownProcesses=$unknown;InventoryComplete=($unknown.Count -eq 0);AclWrites=0;ProcessesStopped=0;ClipboardRead=$false;ScreenRead=$false;SecretsPrompted=$false}|ConvertTo-Json -Depth 6
