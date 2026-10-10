$ErrorActionPreference='Stop'
$script:events=[Collections.Generic.List[string]]::new()
$script:repoOnline=$true
$script:changedContainer=$false
function Get-CimInstance {param($Filter) @([PSCustomObject]@{ProcessId=1001},[PSCustomObject]@{ProcessId=1002})}
function Get-NetTCPConnection {param($OwningProcess,$State,$ErrorAction) [PSCustomObject]@{LocalAddress='127.0.0.1';LocalPort=(9000+$OwningProcess)}}
function Invoke-WebRequest {
 param($Uri,[switch]$UseBasicParsing,$TimeoutSec)
 if ($Uri -eq 'http://127.0.0.1:10001/metrics') {return [PSCustomObject]@{Content='tunnel_6ac4a7249a4081918eb0881c870acf07'}}
 if ($Uri -eq 'http://127.0.0.1:10002/metrics' -and $script:repoOnline) {return [PSCustomObject]@{Content='tunnel_6ac9e4dc9e688191ae1838e858424e8d'}}
 throw 'Offline test endpoint'
}
function Stop-Process {param($Id) $script:events.Add('stop-process:'+ $Id)}
function Start-Process {param($FilePath,$ArgumentList) $script:events.Add('start-process:'+ $FilePath)}
function docker {
 if ($args[0] -eq 'inspect') {
  $id='c6d7be9fe6eb4138a9dc47db3f82c32c377007c2d461c1f03ad37fe9bb3d074a'
  if ($script:changedContainer) {$id='unrelated-container'}
  $global:LASTEXITCODE=0
  return (@{Id=$id;State=@{Running=$true};Config=@{User='1000:1000'};HostConfig=@{Binds=$null;PortBindings=@{};NetworkMode='none';ReadonlyRootfs=$true;RestartPolicy=@{Name='no'}};Mounts=@()} | ConvertTo-Json -Depth 6)
 }
 if ($args[0] -eq 'stop') {$script:events.Add('docker-stop:'+ $args[-1]);$global:LASTEXITCODE=0;return}
 throw 'Unexpected Docker action in test'
}
function Check($Condition,[string]$Message) {if (!$Condition) {throw $Message}}
. (Join-Path $PSScriptRoot 'control.ps1')

Invoke-Control 'StopAccess'
Check ($script:events.Count -eq 1 -and $script:events[0] -eq 'stop-process:1002') 'StopAccess must target Repo only'
$script:events.Clear()
Invoke-Control 'StopContainer'
Check ($script:events.Count -eq 2) 'StopContainer must stop Tunnel and container'
Check ($script:events[0] -eq 'stop-process:1002') 'HOST must remain untouched'
Check ($script:events[1] -eq 'docker-stop:c6d7be9fe6eb4138a9dc47db3f82c32c377007c2d461c1f03ad37fe9bb3d074a') 'Stop immutable verified container ID only'
$script:events.Clear();$script:changedContainer=$true;$caught=$false
try {Invoke-Control 'StopContainer'} catch {$caught=$true}
Check ($caught -and $script:events.Count -eq 0) 'Changed container must be rejected before stopping access'
$script:changedContainer=$false;$caught=$false
try {Invoke-Control 'Start'} catch {$caught=$true}
Check ($caught -and $script:events.Count -eq 0) 'Duplicate Repo start must be rejected'
Invoke-Control 'OpenPanel'
Check ($script:events[0] -eq 'start-process:http://127.0.0.1:10002/ui') 'Open exact Repo loopback panel'
$script:events.Clear();$script:repoOnline=$false
Invoke-Control 'Start'
Check ($script:events.Count -eq 1 -and $script:events[0] -eq 'start-process:powershell.exe') 'Offline Repo start must open the local runner'
Write-Output 'Passed: Repo-only stop, exact container identity, changed-target rejection, duplicate-start guard, panel selection, runner launch. Process/network actions mocked; live services unchanged.'
