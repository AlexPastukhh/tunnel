param([ValidateSet('Preview','Restore')][string]$Mode = 'Preview')
# Local fallback for a temporary direct MCP test. Does not require an MCP connection.
# Do not use an elevated shell, and do not bypass an unexpected identity/hash mismatch.
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows PowerShell is required.' }
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($identity.Name -ine 'FORTIS_M\alexa') { throw 'Run as FORTIS_M\alexa.' }
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Use a normal, non-elevated PowerShell window.'
}
$control = 'C:\Users\alexa\chatgpt-repo-mode\control.ps1'
$runtime = 'C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe'
$docker = (Get-Command docker.exe -CommandType Application -ErrorAction Stop).Source
$container = 'fortis-repo-test'
$containerId = 'c6d7be9fe6eb4138a9dc47db3f82c32c377007c2d461c1f03ad37fe9bb3d074a'
function Assert-Hash([string]$File, [string]$Expected) {
    if ((Get-FileHash -LiteralPath $File -Algorithm SHA256).Hash -ine $Expected) {
        throw "Protected file changed: $File"
    }
}
Assert-Hash $control '605F9D54A0A35FF3011DC44356A733F975A8993F1225FF53378A6B7880A193C5'
Assert-Hash $runtime 'A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A'
$raw = & $docker inspect --type container -- $container 2>$null
if ($LASTEXITCODE -ne 0) { throw 'Docker inspect failed; nothing stopped.' }
$info = @($raw | ConvertFrom-Json)[0]
if ($info.Id -ne $containerId -or -not $info.State.Running) {
    throw 'Expected running Repo container not found; nothing stopped.'
}
if ($info.Config.User -ne '1000:1000' -or $info.HostConfig.Privileged -or
    -not $info.HostConfig.ReadonlyRootfs -or
    @($info.HostConfig.CapDrop) -notcontains 'ALL' -or
    @($info.HostConfig.SecurityOpt) -notcontains 'no-new-privileges') {
    throw 'Container security constraints changed; nothing stopped.'
}
if ($info.HostConfig.Memory -ne 1073741824 -or
    $info.HostConfig.NanoCpus -ne 2000000000 -or
    $info.HostConfig.PidsLimit -ne 256) {
    throw 'Container resource constraints changed; nothing stopped.'
}
if ($null -ne $info.HostConfig.PortBindings -and @($info.HostConfig.PortBindings.PSObject.Properties).Count -ne 0) {
    throw 'Container port bindings changed; nothing stopped.'
}
$networks = @($info.NetworkSettings.Networks.PSObject.Properties.Name)
if ($networks.Count -ne 1 -or $networks[0] -ne 'fortis-repo-egress') {
    throw 'Container network membership changed; nothing stopped.'
}
function Convert-MountPath([string]$Value) {
    ($Value -replace '\\','/' -replace '^/run/desktop/mnt/host/([a-zA-Z])/','$1:/').TrimEnd('/').ToLowerInvariant()
}
$mounts = @($info.Mounts | Where-Object { $_.Type -ne 'tmpfs' })
if ($mounts.Count -ne 3) { throw 'Container mounts changed; nothing stopped.' }
$roots = @{ '/workspace/repos'='C:\Users\alexa\Repos'; '/workspace/files'='C:\Users\alexa\Workfiles' }
foreach ($target in $roots.Keys) {
    $items = @($mounts | Where-Object { $_.Destination -eq $target })
    if ($items.Count -ne 1 -or $items[0].Type -ne 'bind' -or -not $items[0].RW -or
        (Convert-MountPath $items[0].Source) -ne (Convert-MountPath $roots[$target])) {
        throw 'Workspace bind changed; nothing stopped.'
    }
}
$volume = @($mounts | Where-Object { $_.Destination -eq '/workspace/repo' })
if ($volume.Count -ne 1 -or $volume[0].Type -ne 'volume' -or
    $volume[0].Name -ne 'fortis-repo-workspace' -or -not $volume[0].RW) {
    throw 'Internal Repo volume changed; nothing stopped.'
}
# Hash only the selected Bridge entry, not the contents of profiles/keys/logs.
$probe = "const fs=require('fs'),crypto=require('crypto');console.log(crypto.createHash('sha256').update(fs.readFileSync('/workspace/repo/.fortis/mcp-bridge.mjs')).digest('hex'))"
$bridgeHash = & $docker exec $container /usr/local/bin/node -e $probe 2>$null
if ($LASTEXITCODE -ne 0 -or
    $bridgeHash -ne '8389436658e22f213d9865a78872159e027ca33094999db64ca96b5a7c79fc21') {
    throw 'Installed Bridge fingerprint changed; nothing stopped.'
}
. $control
function Get-ProfileCandidates {
    @(Get-CimInstance Win32_Process -Filter "Name='tunnel-client-runtime.exe' OR Name='tunnel-client.exe'" |
        Where-Object { $_.CommandLine -match '(?i)--profile(?:=|\s+)"?repo-mode(?:\s|"|$)' })
}
$tunnels = @(Get-RepoTunnel)
$candidates = @(Get-ProfileCandidates)
if ($tunnels.Count -gt 1 -or $candidates.Count -gt 1) {
    throw 'Multiple Repo processes found; nothing stopped.'
}
if (($tunnels.Count -eq 0 -and $candidates.Count -ne 0) -or
    ($tunnels.Count -eq 1 -and
     ($candidates.Count -ne 1 -or $candidates[0].ProcessId -ne $tunnels[0].pid))) {
    throw 'Repo profile identity differs from the verified tunnel; nothing stopped.'
}
foreach ($tunnel in $tunnels) {
    $process = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $tunnel.pid)
    if ($process.ExecutablePath -ine $runtime -or
        (Invoke-CimMethod -InputObject $process -MethodName GetOwnerSid).Sid -ne $identity.User.Value -or
        $process.CreationDate.ToUniversalTime().ToString('o') -ne $tunnel.createdAt) {
        throw 'Repo process fingerprint mismatch; nothing stopped.'
    }
}
if ($Mode -eq 'Preview') {
    [pscustomobject]@{
        Mode = $Mode
        Preflight = 'PASS'
        ContainerId = $info.Id
        RepoProcesses = @($tunnels | Select-Object pid, createdAt, port)
        Warning = 'Restore interrupts the shared Repo connection; do not stop the container.'
    } | ConvertTo-Json -Depth 5
    return
}
if ($tunnels.Count -eq 1) {
    $fresh = @(Get-RepoTunnel)
    if ($fresh.Count -ne 1 -or $fresh[0].pid -ne $tunnels[0].pid -or
        $fresh[0].createdAt -ne $tunnels[0].createdAt) {
        throw 'Repo identity changed before stop; nothing stopped.'
    }
    $process = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $fresh[0].pid)
    if ($process.ExecutablePath -ine $runtime -or
        (Invoke-CimMethod -InputObject $process -MethodName GetOwnerSid).Sid -ne $identity.User.Value -or
        $process.CreationDate.ToUniversalTime().ToString('o') -ne $fresh[0].createdAt) {
        throw 'Repo process changed before stop; nothing stopped.'
    }
    $null = Stop-RepoAccess
}
$deadline = [DateTime]::UtcNow.AddSeconds(5)
while (@(Get-ProfileCandidates).Count -ne 0 -and [DateTime]::UtcNow -lt $deadline) {
    Start-Sleep -Milliseconds 200
}
if (@(Get-ProfileCandidates).Count -ne 0 -or @(Get-RepoTunnel).Count -ne 0) {
    throw 'Old Repo runtime remains. Do not launch a duplicate.'
}
$entry = 'command=docker exec -i fortis-repo-test /usr/local/bin/node /workspace/repo/.fortis/mcp-bridge.mjs'
Write-Host 'Starting previous Bridge entry with the existing repo-mode profile.'
Write-Host 'Leave this PowerShell window open; do not forward runtime logs.'
$priorPreference = $ErrorActionPreference
try {
    $ErrorActionPreference = 'Continue'
    & $runtime run --profile repo-mode --mcp.command $entry '--harpoon.additional-transport=' *> $null
    $exitCode = $LASTEXITCODE
} finally {
    $ErrorActionPreference = $priorPreference
}
Write-Host ("Bridge runtime ended; exit code " + $exitCode + ".")
