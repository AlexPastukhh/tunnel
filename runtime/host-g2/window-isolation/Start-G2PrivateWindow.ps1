param(
 [ValidateSet('Preview','Namespace','Diagnose','Launch','Rollback')][string]$Mode='Preview',
 [string]$BackupPath,
 [string]$SourceDirectory='C:\Users\alexa\Repos\tunnel\runtime\host-g2\window-isolation'
)
$ErrorActionPreference='Stop'
$OwnerSid='S-1-5-21-303538662-3368424508-2654684973-1001'
$G2Sid='S-1-5-21-303538662-3368424508-2654684973-1009'
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
$admin=(New-Object Security.Principal.WindowsPrincipal($id)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$session=[Diagnostics.Process]::GetCurrentProcess().SessionId
if($id.User.Value -ne $OwnerSid -or $session -eq 0){throw 'Run locally as owner alexa in the owner session'}
if($Mode -ne 'Preview' -and !$admin){throw 'Namespace/Diagnose/Launch/Rollback require a fresh elevated owner PowerShell'}
if('G2WindowBoundary' -as [type]){throw 'Use a fresh PowerShell process'}
$pins=@{
 'WindowBoundaryProbe.cs'='29CF0CFA83412084F3573747DEAD73BAFC90E3121B34FE1C9EEF0BB347F838B2'
 'ProcessInventory.cs'='6A59D74F1C6261DAF44E04BA1830D559543879A9F0BCFB4E8C32D5AB36BACDD3'
 'G2WindowSupervisor.cs'='E63C215501DE2F5D5AA19FF569C107014E77E04BDAF287906B362B21A0CFEFE0'
 'WindowPolicy.ps1'='02486600F12D2A3E29FBA4ABFF8440320B2BCA289EB93BCBB120743C0329CA50'
 'private-station-node-probe.js'='8B2C8FB84EA94F7226BE4A43F28E6483720F2C7F7A26866C20624DBBC6DAE2D1'
 'G2WindowMeta.cs'='BFAFAB4805B7210B11768C591E4FD5B672322514B1E53B5F5EF9382EF1B238AA'
}
$source=@()
$captured=@{}
foreach($name in $pins.Keys){
 $b=[IO.File]::ReadAllBytes((Join-Path $SourceDirectory $name));$sha=[Security.Cryptography.SHA256]::Create()
 try{$h=([BitConverter]::ToString($sha.ComputeHash($b))).Replace('-','')}finally{$sha.Dispose()}
 if($h -ne $pins[$name]){throw ('Component changed: '+$name)}
 $captured[$name]=[Text.Encoding]::UTF8.GetString($b)
}
foreach($n in @('WindowBoundaryProbe.cs','ProcessInventory.cs','G2WindowSupervisor.cs')){$source += $captured[$n]}
$imports=@($source|ForEach-Object{[regex]::Matches($_,'(?m)^using [^\r\n]+;')|ForEach-Object{$_.Value}}|Select-Object -Unique)
$body=@($source|ForEach-Object{[regex]::Replace($_,'(?m)^using [^\r\n]+;\r?\n','')})
Add-Type -TypeDefinition (($imports -join "`n")+"`n"+($body -join "`n"))
. ([scriptblock]::Create($captured['WindowPolicy.ps1']))
$station=[G2WindowBoundary]::GetProcessWindowStation();$desktop=[G2WindowBoundary]::DesktopHandle()
if([G2WindowBoundary]::Name($station) -ne 'WinSta0' -or [G2WindowBoundary]::Name($desktop) -ne 'Default'){throw 'Unexpected owner objects'}
$handles=@($station,$desktop)
$changes=@((New-G2Change $station 'Station' $G2Sid 0xf037f),(New-G2Change $desktop 'Desktop' $G2Sid 0xf01ff))
$approved=@('65FE8DB21AB625C1A8877A090002D3B6AF6ABB9261F11EE50BE090F2C42F1DCA','A571929DFA64CA5FC1B593E125A9204D207757FBB50F7AA5221013BB43396F17')
$forecast=@(for($i=0;$i -lt 2;$i++){[G2WindowBoundary]::Access((Convert-G2SddlBytes $changes[$i].DesiredSddl),262144,($i -eq 1))})
if(@($forecast|Where-Object{$_ -ne 'ALLOW'}).Count){throw 'Owner WRITE_DAC would be lost'}
$inventory=@(Get-G2Inventory $G2Sid $session)
if($Mode -eq 'Preview'){
 [pscustomobject]@{At=[DateTime]::UtcNow.ToString('o');Mode=$Mode;Admin=$admin;Session=$session;Objects=$changes;OwnerWriteDacAfter=$forecast;G2OrUnknownProcesses=$inventory;AclWrites=0;CredentialsPrompted=$false}|ConvertTo-Json -Depth 7
 return
}
Assert-G2Absent $G2Sid $session
if($Mode -eq 'Rollback'){
 if(!$BackupPath){throw 'BackupPath required'}
 $trustedBackupDir='C:\Users\alexa\AppData\Local\FortisHostG2WindowAclBackup'
 $BackupPath=[IO.Path]::GetFullPath($BackupPath)
 if([IO.Path]::GetDirectoryName($BackupPath) -ne $trustedBackupDir -or [IO.Path]::GetFileName($BackupPath) -notmatch '^window-dacl-\d{8}T\d{9}Z-[a-f0-9]{32}\.json$'){throw 'Backup outside owner-only scope'}
 if((Get-Item -LiteralPath $trustedBackupDir).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse backup directory rejected'}
 $backupAcl=Get-Acl -LiteralPath $trustedBackupDir
 if($backupAcl.Owner -ne ((New-Object Security.Principal.SecurityIdentifier($OwnerSid)).Translate([Security.Principal.NTAccount]).Value)){throw 'Unexpected backup owner'}
 foreach($rule in $backupAcl.Access){if($rule.AccessControlType -eq 'Allow' -and $rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value -notin @($OwnerSid,'S-1-5-18','S-1-5-32-544')){throw 'Backup directory has untrusted access'}}
 $item=Get-Item -LiteralPath $BackupPath
 if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse backup rejected'}
 $saved=Get-Content -LiteralPath $BackupPath -Raw|ConvertFrom-Json
 if($saved.Schema -ne 1 -or $saved.OwnerSid -ne $OwnerSid -or $saved.G2Sid -ne $G2Sid -or $saved.Session -ne $session -or $saved.Objects.Count -ne 2){throw 'Backup context mismatch'}
 for($i=0;$i -lt 2;$i++){if($saved.Objects[$i].Name -ne $changes[$i].Name -or $saved.Objects[$i].Kind -ne $changes[$i].Kind){throw 'Backup object mismatch'}}
 foreach($i in @(1,0)){$status=Undo-G2Change $handles[$i] $saved.Objects[$i];Write-Output ($saved.Objects[$i].Kind+': '+$status)}
 $saved.State='ROLLED_BACK';Save-G2Backup $saved $BackupPath
 return
}
if($Mode -eq 'Launch'){
 for($i=0;$i -lt 2;$i++){
  if($changes[$i].BeforeHash -ne $approved[$i]){throw 'Owner ACL changed; obtain a fresh reviewed Preview before Launch'}
 }
}
$runtime='C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe'
if((Get-FileHash -LiteralPath $runtime -Algorithm SHA256).Hash -ne 'A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A'){throw 'Runtime changed'}
$gate='C:\Users\Public\Documents\FortisHostG1Probe\RW\g2-stdio-gate.py'
if((Get-FileHash -LiteralPath $gate -Algorithm SHA256).Hash -ne '146E60B028276F871353A113571306002942461F0446E519A63B28DCC068418D'){throw 'G2 gate changed'}
$account=(New-Object Security.Principal.SecurityIdentifier($G2Sid)).Translate([Security.Principal.NTAccount]).Value.Split('\',2)
if($account.Count -ne 2){throw 'Unexpected account format'}
$profile='C:\Users\FortisHostG1';$workspace=$profile+'\AppData\Local\FortisHostG2\Workspace'
$envG2=New-G2Environment $profile $account[1] $account[0]
$password=$null;$key=$null;$sup=$null;$saved=$null;$nonceRoot=$null;$pipe=$null
try{
 $password=Read-Host ('Enter the Windows password of '+($account -join '\')+' locally') -AsSecureString
 [G2WindowSupervisor]::ValidateAccount($account[1],$account[0],$password,$G2Sid)
 $bootstrap='C:\Tools\tunnel-client\g2-window-bootstrap'
 if(!(Test-Path -LiteralPath $bootstrap)){$null=New-Item -ItemType Directory -Path $bootstrap}
 if((Get-Item -LiteralPath $bootstrap).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse bootstrap rejected'}
 $nonceRoot=Join-Path $bootstrap ('preflight-'+[Guid]::NewGuid().ToString('N'))
 if(Test-Path -LiteralPath $nonceRoot){throw 'Preflight path exists'}
 $null=New-Item -ItemType Directory -Path $nonceRoot
 $nodeFile=Join-Path $nonceRoot 'probe.js';$harnessFile=Join-Path $nonceRoot 'probe.ps1';$pipeName='FortisG2Probe-'+[Guid]::NewGuid().ToString('N')
 [IO.File]::WriteAllText($nodeFile,$captured['private-station-node-probe.js'])
 $harness='$ErrorActionPreference=''Stop''
$client=$null;$writer=$null;$exit=3;$stage=''PipeConnect''
try{
 $client=New-Object IO.Pipes.NamedPipeClientStream(''.'',''__PIPE_NAME__'',''Out'')
 $client.Connect(5000)
 $writer=New-Object IO.StreamWriter($client,([Text.UTF8Encoding]::new($false)));$writer.AutoFlush=$true
}catch{if($client){$client.Dispose()};exit 94}
function Send-G2Frame($frame){$writer.WriteLine(($frame|ConvertTo-Json -Depth 10 -Compress))}
try{
 Send-G2Frame ([pscustomobject]@{Kind=''Progress'';Stage=''Connected''})
 $stage=''WindowMetadata''
 Send-G2Frame ([pscustomobject]@{Kind=''Progress'';Stage=$stage})
 Add-Type -TypeDefinition @''
__META__
''@
 $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
 $admin=(New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
 $station=[G2WindowMeta]::Name();$visible=[G2WindowMeta]::Visible()
 $stage=''NodeCliEdge''
 Send-G2Frame ([pscustomobject]@{Kind=''Progress'';Stage=$stage})
 $nodeOutput= & ''C:\Tools\desktop-commander-runtime\node.exe'' ''__NODE_FILE__''
 $exit=$LASTEXITCODE
 $body=($nodeOutput -join [Environment]::NewLine)|ConvertFrom-Json
 $result=[pscustomobject]@{Sid=$sid;Admin=$admin;Station=$station;Visible=$visible;Node=$body;Exit=$exit}
 Send-G2Frame ([pscustomobject]@{Kind=''Result'';Result=$result})
}catch{
 $e=$_.Exception.GetBaseException()
 Send-G2Frame ([pscustomobject]@{Kind=''Error'';Stage=$stage;Type=$e.GetType().FullName;Message=$e.Message.Substring(0,[Math]::Min(256,$e.Message.Length))})
 $exit=3
}finally{if($writer){$writer.Dispose()};if($client){$client.Dispose()}}
exit $exit'
 $harness=$harness.Replace('__META__',$captured['G2WindowMeta.cs']).Replace('__NODE_FILE__',$nodeFile).Replace('__PIPE_NAME__',$pipeName)
 [IO.File]::WriteAllText($harnessFile,$harness)
 $sup=New-Object G2WindowSupervisor($OwnerSid,$G2Sid,$true)
 $testEnv=$envG2.Clone();$testEnv.G2_EXPECTED_STATION=$sup.StationName
 if($Mode -eq 'Namespace'){$testEnv.G2_NAMESPACE_ONLY='1'}
 $app='C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
 $command=[G2WindowBoundary]::Quote($app)+' -NoProfile -NonInteractive -ExecutionPolicy Bypass -File '+[G2WindowBoundary]::Quote($harnessFile)
 $pipeSecurity=New-Object IO.Pipes.PipeSecurity
 $pipeSecurity.SetSecurityDescriptorSddlForm(('D:P(A;;GA;;;SY)(A;;GA;;;'+$OwnerSid+')(A;;GRGW;;;'+$G2Sid+')'))
 $pipe=New-Object IO.Pipes.NamedPipeServerStream($pipeName,'In',1,'Byte','Asynchronous',4096,0,$pipeSecurity)
 $testPid=$sup.StartUser($account[1],$account[0],$password,$G2Sid,$app,$command,$workspace,$testEnv,$null)
 $deadline=[DateTime]::UtcNow.AddSeconds(90);$testResult=$null;$lastStage='Connect'
 do{
  $connect=$pipe.BeginWaitForConnection($null,$null)
  try{
   while(!$connect.AsyncWaitHandle.WaitOne(200)){
    $childExit=$sup.Wait(0)
    if($childExit -ne 259){throw ('Private preflight child exited before pipe connection: 0x{0:X8}' -f $childExit)}
    if([DateTime]::UtcNow -ge $deadline){throw 'Private preflight pipe timeout; child still running'}
   }
   $pipe.EndWaitForConnection($connect)
  }finally{$connect.AsyncWaitHandle.Dispose()}
  if([G2WindowSupervisor]::PipeClientPid($pipe) -ne $testPid){$pipe.Disconnect();continue}
  $reader=New-Object IO.StreamReader($pipe,([Text.UTF8Encoding]::new($false)),$false,4096,$true)
  try{
   while(!$testResult){
    $readTask=$reader.ReadLineAsync()
    while(!$readTask.Wait(200)){
     $childExit=$sup.Wait(0)
     if($childExit -ne 259 -and !$readTask.Wait(500)){throw ('Private preflight child exited at '+$lastStage+': 0x{0:X8}' -f $childExit)}
     if([DateTime]::UtcNow -ge $deadline){throw ('Private preflight response timeout at '+$lastStage)}
    }
    $line=$readTask.Result
    if(!$line){$childExit=$sup.Wait(1000);throw ('Private preflight pipe closed at '+$lastStage+': 0x{0:X8}' -f $childExit)}
    if($line.Length -gt 16384){throw 'Private preflight response length invalid'}
    try{$frame=$line|ConvertFrom-Json}catch{throw 'Private preflight response malformed'}
    if($frame.Kind -eq 'Progress'){
     if($frame.Stage -notin @('Connected','WindowMetadata','NodeCliEdge')){throw 'Unknown preflight stage'}
     $lastStage=$frame.Stage;Write-Output ('Preflight: '+$lastStage);continue
    }
    if($frame.Kind -eq 'Error'){throw ('Private preflight failed at '+$frame.Stage+': '+$frame.Type+': '+$frame.Message)}
    if($frame.Kind -ne 'Result' -or !$frame.Result){throw 'Unknown preflight frame'}
    $testResult=$frame.Result
   }
  }finally{$reader.Dispose()}
  break
 }while([DateTime]::UtcNow -lt $deadline)
 if(!$testResult){throw 'Authenticated preflight response missing'}
 $testExit=$sup.Wait(10000)
 $pipe.Dispose();$pipe=$null
 $preflightReport=[pscustomobject]@{At=[DateTime]::UtcNow.ToString('o');ChildExit=$testExit;ExpectedSid=$G2Sid;ActualSid=$testResult.Sid;Admin=$testResult.Admin;Visible=$testResult.Visible;ExpectedStation=$sup.StationName;ActualStation=$testResult.Station;NodeExit=$testResult.Exit;Node=$testResult.Node}
 Write-Output 'Private preflight report (synthetic test only):'
 Write-Output ($preflightReport|ConvertTo-Json -Depth 10)
 if($Mode -in @('Namespace','Diagnose')){
  if($Mode -eq 'Namespace' -and ($testExit -ne 0 -or $testResult.Sid -ne $G2Sid -or $testResult.Admin -or $testResult.Visible -or $testResult.Station -ne $sup.StationName -or !$testResult.Node.pass)){throw 'Namespace diagnostic failed; owner ACL unchanged; review synthetic report'}
  Write-Output ($Mode+' completed; runtime key not prompted; owner ACL unchanged; no private runtime started.')
  return
 }
 if($testExit -ne 0 -or $testResult.Sid -ne $G2Sid -or $testResult.Admin -or $testResult.Visible -or $testResult.Station -ne $sup.StationName -or !$testResult.Node.pass){throw 'Private user Edge/CLI preflight failed; owner ACL unchanged; see synthetic report above'}
 $sup.Dispose();$sup=$null
 Assert-G2Absent $G2Sid $session
 $key=Read-Host 'Enter the separate G2 runtime key locally' -AsSecureString
 if(!$key.Length){throw 'Empty runtime key'}
 $backupDir='C:\Users\alexa\AppData\Local\FortisHostG2WindowAclBackup'
 if(!(Test-Path -LiteralPath $backupDir)){$null=New-Item -ItemType Directory -Path $backupDir}
 $dir=Get-Item -LiteralPath $backupDir
 if($dir.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Reparse backup directory rejected'}
 $acl=New-Object Security.AccessControl.DirectorySecurity
 $acl.SetAccessRuleProtection($true,$false);$acl.SetOwner((New-Object Security.Principal.SecurityIdentifier($OwnerSid)))
 foreach($sid in @($OwnerSid,'S-1-5-18','S-1-5-32-544')){$acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule((New-Object Security.Principal.SecurityIdentifier($sid)),'FullControl','ContainerInherit,ObjectInherit','None','Allow')))}
 $dir.SetAccessControl($acl)
 $BackupPath=Join-Path $backupDir ('window-dacl-'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')+'-'+[Guid]::NewGuid().ToString('N')+'.json')
 $saved=[pscustomobject]@{Schema=1;OwnerSid=$OwnerSid;G2Sid=$G2Sid;Session=$session;At=[DateTime]::UtcNow.ToString('o');State='PREPARED';Objects=$changes}
 Save-G2Backup $saved $BackupPath;Write-Output ('Backup: '+$BackupPath)
 for($i=0;$i -lt 2;$i++){Set-G2Change $handles[$i] $changes[$i];$saved.State='PARTIAL';Save-G2Backup $saved $BackupPath}
 $saved.State='APPLIED';Save-G2Backup $saved $BackupPath
 $sup=New-Object G2WindowSupervisor($OwnerSid,$G2Sid,$true)
 $runtimeArgs=' run --profile fortis-host-g2-test --profile-dir '+[G2WindowBoundary]::Quote($profile+'\AppData\Local\FortisHostG2\profiles')+' --control-plane.api-key env:CONTROL_PLANE_API_KEY --harpoon.additional-transport='
 $runtimePid=$sup.StartUser($account[1],$account[0],$password,$G2Sid,$runtime,([G2WindowBoundary]::Quote($runtime)+$runtimeArgs),$workspace,$envG2,$key)
 $password.Dispose();$password=$null;$key.Dispose();$key=$null
 Write-Output ('G2 private runtime started: PID='+$runtimePid+' station='+$sup.StationName+'; keep this owner console open')
 do{$exit=$sup.Wait(1000)}while($exit -eq 259)
 if($exit -ne 0){throw ('Runtime exited: '+$exit)}
 Write-Output 'G2 exited normally; owner station protection retained. Rollback requires zero G2 processes.'
}catch{
 $failure=$_.Exception.Message
 if($sup){$sup.Dispose();$sup=$null}
 if($saved){
  try{
   Assert-G2Absent $G2Sid $session
   foreach($i in @(1,0)){$null=Undo-G2Change $handles[$i] $saved.Objects[$i]}
   $saved.State='ROLLED_BACK_AFTER_FAILURE';Save-G2Backup $saved $BackupPath
   Write-Output 'Own transition changes rolled back after failure'
  }catch{Write-Output ('Rollback stopped; protection retained: '+$_.Exception.Message+'; backup='+$BackupPath)}
 }
 throw $failure
}finally{
 if($pipe){$pipe.Dispose()};if($sup){$sup.Dispose()};if($password){$password.Dispose()};if($key){$key.Dispose()}
 if($nonceRoot -and (Test-Path -LiteralPath $nonceRoot)){
  foreach($name in @('probe.js','probe.ps1')){$p=Join-Path $nonceRoot $name;if([IO.File]::Exists($p)){[IO.File]::Delete($p)}}
  try{[IO.Directory]::Delete($nonceRoot,$false)}catch{Write-Output ('Protected preflight directory left for inspection: '+$nonceRoot)}
 }
}
