param(
    [ValidateSet('Preview','TestDirect','Restore')][string]$Mode = 'Preview'
)
# Manual, temporary Repo-only connection test. No saved profile/file edits.
# Windows AST parsing and Preview are mandatory before TestDirect; no Windows run has been performed.
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows PowerShell is required.' }
$fortisIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($fortisIdentity.Name -ine 'FORTIS_M\alexa') { throw 'Run from the existing FORTIS_M\alexa account.' }
$fortisPrincipal = New-Object Security.Principal.WindowsPrincipal($fortisIdentity)
if ($fortisPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Use a normal, non-elevated PowerShell window.'
}
$fortisRoot = 'C:\Users\alexa\chatgpt-repo-mode'
$fortisControl = Join-Path $fortisRoot 'control.ps1'
$fortisRuntime = 'C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe'
$fortisDocker = (Get-Command docker.exe -CommandType Application -ErrorAction Stop).Source
$fortisContainer = 'fortis-repo-test'
$fortisExpectedContainerId = 'c6d7be9fe6eb4138a9dc47db3f82c32c377007c2d461c1f03ad37fe9bb3d074a'
function Assert-FileHash {
    param([string]$Path, [string]$Expected)
    if ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ine $Expected) {
        throw "Prepared file fingerprint changed: $Path"
    }
}
Assert-FileHash $fortisControl '605F9D54A0A35FF3011DC44356A733F975A8993F1225FF53378A6B7880A193C5'
Assert-FileHash $fortisRuntime 'A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A'
$fortisRaw = & $fortisDocker inspect --type container -- $fortisContainer 2>$null
if ($LASTEXITCODE -ne 0) { throw 'Docker inspect failed; nothing stopped.' }
$fortisInfo = @($fortisRaw | ConvertFrom-Json)[0]
if ($fortisInfo.Id -ne $fortisExpectedContainerId -or -not $fortisInfo.State.Running) {
    throw 'Expected existing running container not found; nothing stopped.'
}
if ($fortisInfo.Config.User -ne '1000:1000' -or $fortisInfo.HostConfig.Privileged -or -not $fortisInfo.HostConfig.ReadonlyRootfs) {
    throw 'Container identity/security constraints changed; nothing stopped.'
}
if (@($fortisInfo.HostConfig.CapDrop) -notcontains 'ALL' -or @($fortisInfo.HostConfig.SecurityOpt) -notcontains 'no-new-privileges') {
    throw 'Container capability constraints changed; nothing stopped.'
}
if ($fortisInfo.HostConfig.Memory -ne 1073741824 -or $fortisInfo.HostConfig.NanoCpus -ne 2000000000 -or $fortisInfo.HostConfig.PidsLimit -ne 256) {
    throw 'Container resource constraints changed; nothing stopped.'
}
if ($null -ne $fortisInfo.HostConfig.PortBindings -and @($fortisInfo.HostConfig.PortBindings.PSObject.Properties).Count -ne 0) {
    throw 'Published ports changed; nothing stopped.'
}
$fortisNetworks = @($fortisInfo.NetworkSettings.Networks.PSObject.Properties.Name)
if ($fortisNetworks.Count -ne 1 -or $fortisNetworks[0] -ne 'fortis-repo-egress') {
    throw 'Container network membership changed; nothing stopped.'
}
function Convert-MountPath {
    param([string]$Value)
    ($Value -replace '\\','/' -replace '^/run/desktop/mnt/host/([a-zA-Z])/','$1:/').TrimEnd('/').ToLowerInvariant()
}
$fortisMounts = @($fortisInfo.Mounts | Where-Object { $_.Type -ne 'tmpfs' })
if ($fortisMounts.Count -ne 3) { throw 'Container mounts changed; nothing stopped.' }
$fortisExpectedFolders = @{
    '/workspace/repos' = 'C:\Users\alexa\Repos'
    '/workspace/files' = 'C:\Users\alexa\Workfiles'
}
foreach ($fortisDestination in $fortisExpectedFolders.Keys) {
    $fortisMount = @($fortisMounts | Where-Object { $_.Destination -eq $fortisDestination })
    if ($fortisMount.Count -ne 1 -or $fortisMount[0].Type -ne 'bind' -or -not $fortisMount[0].RW) {
        throw 'Workspace mount mode changed; nothing stopped.'
    }
    if ((Convert-MountPath $fortisMount[0].Source) -ne (Convert-MountPath $fortisExpectedFolders[$fortisDestination])) {
        throw 'Workspace mount source changed; nothing stopped.'
    }
}
$fortisVolume = @($fortisMounts | Where-Object { $_.Destination -eq '/workspace/repo' })
if ($fortisVolume.Count -ne 1 -or $fortisVolume[0].Type -ne 'volume' -or $fortisVolume[0].Name -ne 'fortis-repo-workspace' -or -not $fortisVolume[0].RW) {
    throw 'Internal volume changed; nothing stopped.'
}
# Only read known runtime/config metadata. No MCP probe, marker or project tool call.
$fortisProbeCode = @'
const fs=require('fs'),crypto=require('crypto');const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');const s=fs.readFileSync('/proc/self/status','utf8');const cfg=JSON.parse(fs.readFileSync('/home/node/.claude-server-commander/config.json','utf8'));const mi=fs.readFileSync('/proc/self/mountinfo','utf8').split('\n');console.log(JSON.stringify({uid:process.getuid(),capEff:s.match(/^CapEff:\s*(.+)$/m)?.[1],capBnd:s.match(/^CapBnd:\s*(.+)$/m)?.[1],noNewPrivs:s.match(/^NoNewPrivs:\s*(.+)$/m)?.[1],seccomp:s.match(/^Seccomp:\s*(.+)$/m)?.[1],rootReadOnly:mi.some(l=>{const a=l.split(' ');return a[4]==='/'&&a[5].split(',').includes('ro');}),directHash:hash('/opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js'),bridgeHash:hash('/workspace/repo/.fortis/mcp-bridge.mjs'),allowedDirectories:cfg.allowedDirectories,defaultShell:cfg.defaultShell,telemetryEnabled:cfg.telemetryEnabled}));
'@
$fortisProbeRaw = & $fortisDocker exec $fortisContainer /usr/local/bin/node -e $fortisProbeCode 2>$null
if ($LASTEXITCODE -ne 0) { throw 'Read-only runtime preflight failed; nothing stopped.' }
$fortisProbe = $fortisProbeRaw | ConvertFrom-Json
if ($fortisProbe.uid -ne 1000 -or $fortisProbe.capEff -notmatch '^0+$' -or $fortisProbe.capBnd -notmatch '^0+$' -or $fortisProbe.noNewPrivs -ne '1' -or $fortisProbe.seccomp -ne '2' -or -not $fortisProbe.rootReadOnly) {
    throw 'Actual Linux restrictions differ; nothing stopped.'
}
if ($fortisProbe.directHash -ne 'a4145198dc75cd34e7c7452c2054b4cc0d29e199ae1459961a17e4da25a13500') {
    throw 'Installed direct DC fingerprint changed; nothing stopped.'
}
if ($fortisProbe.bridgeHash -ne '8389436658e22f213d9865a78872159e027ca33094999db64ca96b5a7c79fc21') {
    throw 'Original Bridge fingerprint changed; nothing stopped.'
}
$fortisExpectedRoots = @('/workspace/repos','/workspace/files','/workspace/repo')
if (@(Compare-Object -ReferenceObject $fortisExpectedRoots -DifferenceObject @($fortisProbe.allowedDirectories)).Count -ne 0 -or $fortisProbe.defaultShell -ne '/bin/bash' -or $fortisProbe.telemetryEnabled -ne $false) {
    throw 'Current DC settings differ from prepared baseline; nothing stopped.'
}
# Pinned control is imported only for its selected Repo discovery/stop functions.
# Its Menu/Start/StopContainer actions are not invoked.
. $fortisControl
function Get-ProfileCandidates {
    @(Get-CimInstance Win32_Process -Filter "Name='tunnel-client-runtime.exe' OR Name='tunnel-client.exe'" |
        Where-Object { $_.CommandLine -match '(?i)--profile(?:=|\s+)"?repo-mode(?:\s|"|$)' })
}
$fortisTunnels = @(Get-RepoTunnel)
$fortisCandidates = @(Get-ProfileCandidates)
if ($fortisTunnels.Count -gt 1 -or $fortisCandidates.Count -gt 1) {
    throw 'Multiple Repo processes found; nothing stopped.'
}
if ($fortisCandidates.Count -gt 0 -and $fortisTunnels.Count -eq 0) {
    throw 'A Repo-profile process lacks verified Repo identity; nothing stopped.'
}
if ($fortisTunnels.Count -eq 1 -and $fortisCandidates.Count -ne 1) {
    throw 'A verified Repo tunnel lacks a visible matching profile process; nothing stopped.'
}
if ($fortisCandidates.Count -eq 1 -and $fortisTunnels.Count -eq 1 -and
    $fortisCandidates[0].ProcessId -ne $fortisTunnels[0].pid) {
    throw 'Repo profile PID differs from the tunnel-ID process; nothing stopped.'
}
if ($Mode -eq 'TestDirect' -and $fortisTunnels.Count -ne 1) {
    throw 'TestDirect requires one verified running Repo tunnel; nothing stopped.'
}
foreach ($fortisTunnel in $fortisTunnels) {
    $fortisProcess = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $fortisTunnel.pid)
    if ($fortisProcess.ExecutablePath -ine $fortisRuntime) { throw 'Unexpected Repo executable; nothing stopped.' }
    $fortisOwner = (Invoke-CimMethod -InputObject $fortisProcess -MethodName GetOwnerSid).Sid
    if ($fortisOwner -ne $fortisIdentity.User.Value) { throw 'Repo is owned by another account; nothing stopped.' }
    if ($fortisProcess.CreationDate.ToUniversalTime().ToString('o') -ne $fortisTunnel.createdAt) {
        throw 'Repo process identity changed; nothing stopped.'
    }
}
if ($Mode -eq 'Preview') {
    [pscustomobject]@{
        Mode = $Mode; ContainerId = $fortisInfo.Id
        Identity = $fortisIdentity.Name; LinuxUid = $fortisProbe.uid
        ExistingRepoProcesses = @($fortisTunnels | Select-Object pid, createdAt, port)
        Preflight = 'PASS'; SavedProfileEdits = $false
        Warning = 'TestDirect/Restore briefly interrupt this shared Repo connection and may end active tool terminal sessions.'
    } | ConvertTo-Json -Depth 5
    return
}
Write-Host 'This switches only the shared Repo connection. The container is not stopped.'
Write-Host 'Active Repo tool terminal sessions in other chats may be interrupted.'
if ($fortisTunnels.Count -eq 1) {
    $fresh = @(Get-RepoTunnel)
    if ($fresh.Count -ne 1 -or $fresh[0].pid -ne $fortisTunnels[0].pid -or
        $fresh[0].createdAt -ne $fortisTunnels[0].createdAt) {
        throw 'Repo identity changed before stop; nothing stopped.'
    }
    $freshProcess = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $fresh[0].pid)
    if ($freshProcess.ExecutablePath -ine $fortisRuntime -or
        (Invoke-CimMethod -InputObject $freshProcess -MethodName GetOwnerSid).Sid -ne $fortisIdentity.User.Value -or
        $freshProcess.CreationDate.ToUniversalTime().ToString('o') -ne $fresh[0].createdAt) {
        throw 'Repo process fingerprint changed before stop; nothing stopped.'
    }
    $null = Stop-RepoAccess
}
$fortisDeadline = [DateTime]::UtcNow.AddSeconds(5)
while (@(Get-ProfileCandidates).Count -ne 0 -and [DateTime]::UtcNow -lt $fortisDeadline) {
    Start-Sleep -Milliseconds 200
}
if (@(Get-ProfileCandidates).Count -ne 0 -or @(Get-RepoTunnel).Count -ne 0) {
    throw 'Repo did not stop cleanly. Do not start a duplicate; use the documented restore path.'
}
$fortisEntry = $(if ($Mode -eq 'TestDirect') {
    '/opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js'
} else {
    '/workspace/repo/.fortis/mcp-bridge.mjs'
})
$fortisCommand = 'command=docker exec -i fortis-repo-test /usr/local/bin/node ' + $fortisEntry
Write-Host ("Starting " + $Mode + " using the existing repo-mode profile.")
Write-Host 'Leave this PowerShell window open. Return to ChatGPT and report that it is started.'
Write-Host 'Runtime console logs are suppressed; do not send raw profile or doctor output.'
$fortisPriorPreference = $ErrorActionPreference
try {
    $ErrorActionPreference = 'Continue'
    & $fortisRuntime run --profile repo-mode --mcp.command $fortisCommand '--harpoon.additional-transport=' *> $null
    $fortisExit = $LASTEXITCODE
} finally { $ErrorActionPreference = $fortisPriorPreference }
Write-Host ("Repo runtime ended; exit code " + $fortisExit + ".")
Write-Host 'To restore Bridge mode, run this script with -Mode Restore in a normal PowerShell window.'
