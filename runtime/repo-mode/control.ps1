param([ValidateSet('Menu','Status','OpenPanel','Start','StopAccess','StopContainer')][string]$Action='Menu')
$ErrorActionPreference='Stop'
$repoId='tunnel_6ac9e4dc9e688191ae1838e858424e8d'
$containerName='fortis-repo-test'

function Get-RepoTunnel {
 foreach ($p in (Get-CimInstance Win32_Process -Filter "Name = 'tunnel-client.exe'")) {
  foreach ($c in (Get-NetTCPConnection -OwningProcess $p.ProcessId -State Listen -ErrorAction SilentlyContinue)) {
   if ($c.LocalAddress -ne '127.0.0.1') { continue }
   $base='http://127.0.0.1:'+[string]$c.LocalPort
   try {
    $metrics=(Invoke-WebRequest ($base+'/metrics') -UseBasicParsing -TimeoutSec 3).Content
    if (!$metrics.Contains($repoId)) {continue}
    [PSCustomObject]@{pid=$p.ProcessId;port=$c.LocalPort;panelUrl=$base+'/ui';tunnelId=$repoId}
   } catch { }
  }
 }
}

function Get-RepoStatus {
 $raw=docker inspect $containerName 2>$null
 if ($LASTEXITCODE -ne 0) {throw 'Repo container not found or Docker unavailable'}
 $d=($raw | ConvertFrom-Json)[0]
 $binds=0;if ($null -ne $d.HostConfig.Binds) {$binds=@($d.HostConfig.Binds).Count}
 $ports=0;if ($null -ne $d.HostConfig.PortBindings) {$ports=@($d.HostConfig.PortBindings.PSObject.Properties).Count}
 [PSCustomObject]@{
  tunnel=@(Get-RepoTunnel)
  container=$containerName;containerId=$d.Id;running=$d.State.Running;user=$d.Config.User
  network=$d.HostConfig.NetworkMode;rootReadOnly=$d.HostConfig.ReadonlyRootfs
  hostBindMountCount=@($d.Mounts | Where-Object Type -eq 'bind').Count;publishedPortCount=$ports;restartPolicy=$d.HostConfig.RestartPolicy.Name
  workspace=@($d.Mounts | Where-Object Type -ne 'tmpfs' | ForEach-Object {[PSCustomObject]@{type=$_.Type;name=$_.Name;source=$_.Source;destination=$_.Destination;readWrite=$_.RW}})
 }
}

function Stop-RepoAccess {
 foreach ($t in @(Get-RepoTunnel)) {
  # Rediscover the exact ID/PID immediately before stopping; never target HOST.
  $stillRepo=@(Get-RepoTunnel | Where-Object pid -eq $t.pid)
  if ($stillRepo.Count -ne 1) {throw 'Repo process identity changed; inspect before stopping'}
  Stop-Process -Id $t.pid
 }
 Write-Output 'Repo Tunnel stopped. Host workspace files and the Docker volume remain unchanged.'
}

function Invoke-Control([string]$SelectedAction) {
 switch ($SelectedAction) {
  'Status' {Get-RepoStatus | ConvertTo-Json -Depth 6}
  'OpenPanel' {
   $t=@(Get-RepoTunnel)
   if ($t.Count -ne 1) {throw 'A single running Repo Tunnel is required to open its panel'}
   Start-Process $t[0].panelUrl
  }
  'Start' {
   if (@(Get-RepoTunnel).Count -ne 0) {throw 'Repo Tunnel is already running'}
   $runner=Join-Path $PSScriptRoot 'run-tunnel.ps1'
   Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoProfile','-File',('"'+$runner+'"'))
  }
  'StopAccess' {Stop-RepoAccess}
  'StopContainer' {
   $state=Get-RepoStatus
   if ($state.containerId -ne (Get-Content -LiteralPath (Join-Path $PSScriptRoot 'workspace-config.json') -Raw | ConvertFrom-Json).containerId) {throw 'Repo container identity changed; re-verify before stopping'}
   Stop-RepoAccess
   docker stop --time 10 $state.containerId
   if ($LASTEXITCODE -ne 0) {throw 'Repo container stop failed'}
   Write-Output 'Repo container stopped. Host workspace files and its volume were not deleted.'
  }
 }
}

if ($MyInvocation.InvocationName -eq '.') {return}
if ($Action -ne 'Menu') {Invoke-Control $Action;exit}
while ($true) {
 Write-Host "`nFORTIS REPO - LOCAL CONTROL"
 Write-Host '1 Status | 2 Tunnel panel | 3 Start Repo | 4 Stop access | 5 Stop container | 0 Exit'
 $choice=Read-Host 'Action'
 if ($choice -eq '0') {break}
 $actions=@{'1'='Status';'2'='OpenPanel';'3'='Start';'4'='StopAccess';'5'='StopContainer'}
 if (!$actions.ContainsKey($choice)) {continue}
 try {Invoke-Control $actions[$choice]} catch {Write-Host $_.Exception.Message -ForegroundColor Yellow}
}
