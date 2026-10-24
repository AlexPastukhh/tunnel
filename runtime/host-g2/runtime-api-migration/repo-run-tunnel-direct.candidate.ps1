param([ValidateSet('Preview','Run')][string]$Mode='Run')
# PR-A-13 CANDIDATE. Source only; NOT installed. Windows PowerShell / normal FORTIS_M\alexa.
# Direct DC entry in the existing repo-mode tunnel, with fail-closed read-only checks.
# No old probe.mjs, Bridge exec, registration, profile write, container start/stop, or Git configuration writes.
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
$fortisTmpfs = @($fortisInfo.HostConfig.Tmpfs.PSObject.Properties.Name)
if ($fortisTmpfs.Count -ne 2 -or $fortisTmpfs -notcontains '/tmp' -or $fortisTmpfs -notcontains '/home/node') {
    throw 'Container tmpfs constraints changed; nothing stopped.'
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
const fs=require('fs'),crypto=require('crypto');const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');const s=fs.readFileSync('/proc/self/status','utf8');const cfg=JSON.parse(fs.readFileSync('/home/node/.claude-server-commander/config.json','utf8'));const mi=fs.readFileSync('/proc/self/mountinfo','utf8').split('\n');console.log(JSON.stringify({uid:process.getuid(),capEff:s.match(/^CapEff:\s*(.+)$/m)?.[1],capBnd:s.match(/^CapBnd:\s*(.+)$/m)?.[1],noNewPrivs:s.match(/^NoNewPrivs:\s*(.+)$/m)?.[1],seccomp:s.match(/^Seccomp:\s*(.+)$/m)?.[1],rootReadOnly:mi.some(l=>{const a=l.split(' ');return a[4]==='/'&&a[5].split(',').includes('ro');}),directHash:hash('/opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js'),allowedDirectories:cfg.allowedDirectories,defaultShell:cfg.defaultShell,telemetryEnabled:cfg.telemetryEnabled}));
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
$fortisExpectedRoots = @('/workspace/repos','/workspace/files','/workspace/repo')
if (@(Compare-Object -ReferenceObject $fortisExpectedRoots -DifferenceObject @($fortisProbe.allowedDirectories)).Count -ne 0 -or $fortisProbe.defaultShell -ne '/bin/bash' -or $fortisProbe.telemetryEnabled -ne $false) {
    throw 'Current DC settings differ from prepared baseline; nothing stopped.'
}
# The pinned controller is dot-sourced; its Menu / Start / StopAccess / StopContainer are NOT invoked.
. $fortisControl
function Get-ProfileCandidates {
    @(Get-CimInstance Win32_Process -Filter "Name='tunnel-client-runtime.exe' OR Name='tunnel-client.exe'" |
        Where-Object { $_.CommandLine -match '(?i)--profile(?:=|\s+)"?repo-mode(?:\s|"|$)' })
}
$existingTunnels = @(Get-RepoTunnel)
$existingProfiles = @(Get-ProfileCandidates)
if ($Mode -eq 'Preview') {
    [pscustomobject]@{
        Mode = $Mode; Preflight = 'PASS'; ContainerId = $fortisInfo.Id
        Identity = $fortisIdentity.Name; LinuxUid = $fortisProbe.uid
        DirectHashVerified = $true; ExistingTunnelCount = $existingTunnels.Count
        ExistingProfileCount = $existingProfiles.Count; SavedProfileEdits = $false
    } | ConvertTo-Json -Depth 4
    return
}
# Never launch a second runtime over a detected Repo connection, including unknown identity.
if ($existingTunnels.Count -ne 0 -or $existingProfiles.Count -ne 0) {
    throw 'A Repo tunnel/profile process already exists. Do not start a duplicate.'
}
$mcpCommand = 'command=docker exec -i fortis-repo-test /usr/local/bin/node /opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js'
Write-Host 'Starting pinned direct Desktop Commander using existing repo-mode runtime.'
Write-Host 'Keep this window open. Do not forward raw profile/runtime logs.'
$priorPreference = $ErrorActionPreference
try {
    $ErrorActionPreference = 'Continue'
    & $fortisRuntime run --profile repo-mode --mcp.command $mcpCommand '--harpoon.additional-transport=' *> $null
    $exitCode = $LASTEXITCODE
} finally {
    $ErrorActionPreference = $priorPreference
}
throw "Repo direct runtime ended (exit code $exitCode). Use the documented independent local recovery; do not restart blindly."
