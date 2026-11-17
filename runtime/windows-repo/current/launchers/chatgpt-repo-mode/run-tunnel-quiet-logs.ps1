param([ValidateSet('Preview','Run')][string]$Mode='Preview', [switch]$RestartRepo1)
# Repo1 quiet-log launcher; shared Fortis security policy is loaded below.
# Shared policy verifies Windows identity, Docker/Linux isolation and guarded tmpfs repair.
# Direct DC entry in the existing repo-mode tunnel, with fail-closed read-only checks.
# No old probe.mjs, Bridge exec, registration, profile write, or container start/stop.
# Both Repo launchers use the same narrowly scoped shared tmpfs repair path.
$ErrorActionPreference = 'Stop'
$fortisPolicyPath = Join-Path $PSScriptRoot '..\\shared\\FortisContainerPolicy.ps1'
if (-not (Test-Path -LiteralPath $fortisPolicyPath -PathType Leaf)) { throw 'Shared Fortis policy is missing.' }
. $fortisPolicyPath
$fortisIdentity = Assert-FortisWindowsOwner
$fortisRoot = 'C:\Users\alexa\chatgpt-repo-mode'
$fortisControl = Join-Path $PSScriptRoot 'control.ps1'
$fortisRuntime = Assert-FortisTunnelRuntime

function Assert-FileHash {
    param([string]$Path, [string]$Expected)
    if ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ine $Expected) {
        throw "Prepared file fingerprint changed: $Path"
    }
}
Assert-FileHash $fortisControl '62A93BFA5F4C957C5A89267AC3416CE09BB28FAB71EBD87DB976F20E21092D58'

$fortisContext = Get-FortisContainerContext
$fortisInfo = $fortisContext.Info
$fortisContainer = $fortisContext.ContainerId
$fortisRuntimeState = Get-FortisLinuxRuntimeSnapshot -Context $fortisContext
$fortisProbe = $fortisRuntimeState.Probe
$fortisConfigState = $fortisRuntimeState.ConfigState
$fortisPinnedConfig = $fortisConfigState -eq 'Pinned'
# Startup availability is separate from the shared security policy.
$fortisHeadroomProbeCode = @'
// Conservative cgroup-v2 working-set estimate: credit inactive file cache only.
const fs = require('fs');
const root = '/sys/fs/cgroup/';
function counter(raw) {
  const value = raw.trim();
  if (!/^(0|[1-9][0-9]*)$/.test(value) || !Number.isSafeInteger(Number(value))) throw Error('Invalid counter');
  return Number(value);
}
let result;
try {
  const read = name => counter(fs.readFileSync(root + name, 'utf8'));
  const memoryLimitBytes = read('memory.max'), memoryCurrentBytes = read('memory.current');
  const pidLimit = read('pids.max'), pidCurrent = read('pids.current');
  const entries = fs.readFileSync(root + 'memory.stat', 'utf8').trim().split('\n').filter(line => /^inactive_file(?:\s|$)/.test(line));
  if (entries.length !== 1) throw Error('Missing or duplicate inactive_file');
  const inactiveFileBytes = counter(entries[0].replace(/^inactive_file\s+/, ''));
  if (memoryLimitBytes < 1 || pidLimit < 1 || inactiveFileBytes > memoryCurrentBytes) throw Error('Inconsistent counters');
  const memoryWorkingSetBytes = memoryCurrentBytes - inactiveFileBytes;
  const memoryHeadroomBytes = Math.max(0, memoryLimitBytes - memoryWorkingSetBytes);
  const pidHeadroom = Math.max(0, pidLimit - pidCurrent);
  const status = memoryHeadroomBytes < 268435456 ? 'MEMORY_HEADROOM_LOW' : pidHeadroom < 48 ? 'PID_HEADROOM_LOW' : 'PASS';
  result = {status, memoryLimitBytes, memoryCurrentBytes, inactiveFileBytes, memoryWorkingSetBytes, memoryHeadroomBytes, pidLimit, pidCurrent, pidHeadroom};
} catch {
  result = {status: 'RESOURCE_COUNTERS_INVALID'};
}
process.stdout.write(JSON.stringify(result) + '\n');
'@
function Assert-FortisRepo1Headroom {
    param($Probe)
    switch ([string]$Probe.status) {
        'PASS' { return }
        'MEMORY_HEADROOM_LOW' {
            throw ('Repo1 startup blocked: estimated memory headroom {0:N0} MiB < 256 MiB (working set {1:N0} MiB; inactive file cache {2:N0} MiB). Nothing started or repaired.' -f ($Probe.memoryHeadroomBytes / 1MB), ($Probe.memoryWorkingSetBytes / 1MB), ($Probe.inactiveFileBytes / 1MB))
        }
        'PID_HEADROOM_LOW' {
            throw ('Repo1 startup blocked: PID headroom {0} < 48 (current {1}; limit {2}). Nothing started or repaired.' -f $Probe.pidHeadroom, $Probe.pidCurrent, $Probe.pidLimit)
        }
        default { throw 'Repo1 resource counters are missing, invalid or inconsistent. Nothing started or repaired.' }
    }
}
try {
    $fortisHeadroomRaw = @(Invoke-FortisDockerExec -Context $fortisContext -Command @($script:FortisPolicy.LinuxNodePath, '-e', $fortisHeadroomProbeCode))
} catch {
    throw ('Repo1 resource probe failed: ' + $_.Exception.Message)
}
if ($fortisHeadroomRaw.Count -ne 1) { throw 'Repo1 resource probe returned unexpected output. Nothing started or repaired.' }
try { $fortisHeadroom = $fortisHeadroomRaw[0] | ConvertFrom-Json -ErrorAction Stop }
catch { throw 'Repo1 resource probe returned invalid JSON. Nothing started or repaired.' }
Assert-FortisRepo1Headroom -Probe $fortisHeadroom

# PR-A-17: log-only preload is embedded in this reviewed Windows copy.
# Refuse to overwrite an existing NODE_OPTIONS policy. No mutable Docker helper file.
# Shared policy already rejects a non-empty inherited NODE_OPTIONS.
$fortisQuietPreloadSha256 = $script:FortisPolicy.QuietPreloadSha256
$fortisQuietNodeOption = $script:FortisPolicy.QuietNodeOption
# Fixed synthetic output only: no real MCP is started by this compatibility probe.
$fortisQuietProbeCode = @'
process.stdout.write(JSON.stringify({jsonrpc:'2.0',method:'notifications/message',params:{level:'info',data:'FORTIS_SYNTHETIC_LOG'}})+'\n');process.stdout.write(JSON.stringify({jsonrpc:'2.0',method:'notifications/progress',params:{progressToken:'fortis-quiet-preview',progress:1}})+'\n');process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:1,result:{quietPreloadOk:process.env.NODE_OPTIONS===undefined}})+'\n');
'@
$fortisQuietRaw = Invoke-FortisDockerExec -Context $fortisContext -Options @('--user', '1000:1000', '--env', ('NODE_OPTIONS=' + $fortisQuietNodeOption)) -Command @($script:FortisPolicy.LinuxNodePath, '-e', $fortisQuietProbeCode)
$fortisQuietExpected = @(
    '{"jsonrpc":"2.0","method":"notifications/progress","params":{"progressToken":"fortis-quiet-preview","progress":1}}'
    '{"jsonrpc":"2.0","id":1,"result":{"quietPreloadOk":true}}'
)
if (@($fortisQuietRaw).Count -ne 2 -or
    @($fortisQuietRaw)[0] -cne $fortisQuietExpected[0] -or @($fortisQuietRaw)[1] -cne $fortisQuietExpected[1]) {
    throw 'Quiet preload compatibility probe failed; nothing stopped or repaired.'
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
        Mode = $Mode; Preflight = $(if ($fortisPinnedConfig) {'PASS'} else {'REBOOT_REPAIR_REQUIRED'})
        ConfigState = $fortisConfigState; ContainerId = $fortisInfo.Id
        Identity = $fortisIdentity.Name; LinuxUid = $fortisProbe.uid
        LinuxSecurityVerified = $fortisRuntimeState.LinuxSecurityVerified
        DirectEntryAvailable = $fortisRuntimeState.DirectEntryAvailable; ImageId = $fortisInfo.Image
        ExistingTunnelCount = $existingTunnels.Count
        ExistingProfileCount = $existingProfiles.Count; SavedProfileEdits = $false
        QuietPreloadProbe = 'PASS'; QuietPreloadSha256 = $fortisQuietPreloadSha256
        ResourceProbe = $fortisHeadroom.status; MemoryWorkingSetBytes = $fortisHeadroom.memoryWorkingSetBytes
        MemoryHeadroomBytes = $fortisHeadroom.memoryHeadroomBytes; InactiveFileCacheBytes = $fortisHeadroom.inactiveFileBytes
        PidHeadroom = $fortisHeadroom.pidHeadroom
    } | ConvertTo-Json -Depth 4
    return
}
# Canary changes logging only; common recovery remains in the shared policy module.
# Explicit owner switch, after all preflight checks and after the Preview return.
if ($RestartRepo1) {
    if ($existingTunnels.Count -ne 1 -or $existingProfiles.Count -ne 1) {
        throw 'Expected exactly one existing Repo1 identity; nothing stopped.'
    }
    # Reuse the pinned controller's fresh ID/PID/creation-time guard.
    Stop-RepoAccess
    $existingTunnels = @(Get-RepoTunnel)
    $existingProfiles = @(Get-ProfileCandidates)
}
# Never repair or launch a second runtime over a detected Repo connection/profile.
if ($existingTunnels.Count -ne 0 -or $existingProfiles.Count -ne 0) {
    throw 'A Repo tunnel/profile process already exists. Do not start or repair a duplicate.'
}
$fortisRuntimeState = Repair-FortisLinuxRuntimeConfig -Context $fortisContext -Snapshot $fortisRuntimeState
$fortisProbe = $fortisRuntimeState.Probe
$fortisConfigState = $fortisRuntimeState.ConfigState
$fortisPinnedConfig = $fortisConfigState -eq 'Pinned'
if (-not $fortisPinnedConfig) { throw 'Shared DC config repair did not reach the pinned state.' }
# Repo1 and Repo2 share the same bootstrap; no Repo-specific copy exists.
$mcpCommand = 'command=docker exec -i --env NODE_OPTIONS=' + $fortisQuietNodeOption + ' ' + $fortisContainer + ' ' + $script:FortisPolicy.LinuxNodePath + ' ' + $script:FortisPolicy.DirectEntryPath
$fortisQuietRunId = [Guid]::NewGuid().ToString('N')
$fortisQuietLogFile = Join-Path $fortisRoot ('runtime-diag-' + $fortisQuietRunId + '.jsonl')
if (Test-Path -LiteralPath $fortisQuietLogFile) { throw 'Quiet canary log already exists; runtime not started.' }
Write-Host ('RunId=' + $fortisQuietRunId)
Write-Host 'Starting pinned direct Desktop Commander with the quiet-log canary.'
Write-Host 'Keep this window open. Do not forward raw profile/runtime logs.'
$priorPreference = $ErrorActionPreference
try {
    $ErrorActionPreference = 'Continue'
    & $fortisRuntime run --profile repo-mode --mcp.command $mcpCommand '--harpoon.additional-transport=' --log.level debug --log.format json --log.file $fortisQuietLogFile '--log.http-raw-unsafe=false' *> $null
    $exitCode = $LASTEXITCODE
} finally {
    $ErrorActionPreference = $priorPreference
}
throw "Repo direct runtime ended (exit code $exitCode). Use the documented independent local recovery; do not restart blindly."
