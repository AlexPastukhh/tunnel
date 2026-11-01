param([ValidateSet('Preview','Run')][string]$Mode='Preview', [switch]$RestartRepo1)
# PR-A-17 CANDIDATE. Source only; NOT installed. Side-by-side Repo1 quiet-log canary.
# First verify pinned Windows/Docker/Linux identity, then optionally restore ONLY recognized tmpfs factory reset.
# Direct DC entry in the existing repo-mode tunnel, with fail-closed read-only checks.
# No old probe.mjs, Bridge exec, registration, profile write, or container start/stop.
# On recognized tmpfs reset: repair DC only if no MCP is serving; Git file creation is exclusive.
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows PowerShell is required.' }
$fortisIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($fortisIdentity.Name -ine 'FORTIS_M\alexa') { throw 'Run from the existing FORTIS_M\alexa account.' }
$fortisPrincipal = New-Object Security.Principal.WindowsPrincipal($fortisIdentity)
if ($fortisPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Use a normal, non-elevated PowerShell window.'
}
$fortisRoot = 'C:\Users\alexa\chatgpt-repo-mode'
$fortisControl = Join-Path $PSScriptRoot 'control.ps1'
$fortisRuntime = 'C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe'
$fortisDocker = (Get-Command docker.exe -CommandType Application -ErrorAction Stop).Source
$fortisContainer = 'fortis-repo-test'
$fortisExpectedContainerId = '0c0f8cb2d608679b4c3de51c527cbe2aca687cbf1360e6bf116444b2a0928cc2'
function Assert-FileHash {
    param([string]$Path, [string]$Expected)
    if ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ine $Expected) {
        throw "Prepared file fingerprint changed: $Path"
    }
}
Assert-FileHash $fortisControl '62A93BFA5F4C957C5A89267AC3416CE09BB28FAB71EBD87DB976F20E21092D58'
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
if (([long]$fortisInfo.HostConfig.Memory -lt 4294967296 -or [long]$fortisInfo.HostConfig.Memory -gt 8589934592) -or $fortisInfo.HostConfig.NanoCpus -ne 2000000000 -or ([long]$fortisInfo.HostConfig.PidsLimit -lt 256 -or [long]$fortisInfo.HostConfig.PidsLimit -gt 1024)) {
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
# Require exactly the original egress network, with at most one optional RDG bridge.
if ($fortisNetworks.Count -lt 1 -or $fortisNetworks.Count -gt 2 -or
    $fortisNetworks -cnotcontains 'fortis-repo-egress' -or
    @($fortisNetworks | Where-Object {
        $_ -cne 'fortis-repo-egress' -and $_ -cne 'rdg-personal_agents'
    }).Count -ne 0) {
    throw 'Container network membership changed; nothing stopped.'
}
if ($fortisNetworks -ccontains 'rdg-personal_agents') {
    $fortisRdgRaw = & $fortisDocker network inspect rdg-personal_agents 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'RDG network inspection failed; nothing stopped.' }
    $fortisRdgInfo = @($fortisRdgRaw | ConvertFrom-Json)[0]
    if ($null -eq $fortisRdgInfo -or
        $fortisRdgInfo.Name -cne 'rdg-personal_agents' -or
        $fortisRdgInfo.Driver -cne 'bridge' -or
        $fortisRdgInfo.Internal -ne $true) {
        throw 'RDG network isolation changed; nothing stopped.'
    }
}
# Security contract after Fortis Windows-import isolation: three mounts, all volume-backed.
# Read BOTH effective Docker mounts and requested volume subpaths, never trust names alone.
$fortisMounts = @($fortisInfo.Mounts | Where-Object { $_.Type -ne 'tmpfs' })
$fortisHostMounts = @($fortisInfo.HostConfig.Mounts)
if ($fortisMounts.Count -ne 3 -or $fortisHostMounts.Count -ne 3) {
    throw 'Expected exactly three pinned volume mounts; nothing stopped.'
}
$fortisExpectedSubpaths = @{
    '/workspace/repo' = ''
    '/workspace/repos' = 'Repos'
    '/workspace/files' = 'Workfiles'
}
foreach ($fortisDestination in $fortisExpectedSubpaths.Keys) {
    $fortisMatch = @($fortisMounts | Where-Object { $_.Destination -ceq $fortisDestination })
    if ($fortisMatch.Count -ne 1 -or $fortisMatch[0].Type -cne 'volume' -or
        $fortisMatch[0].Name -cne 'fortis-repo-workspace' -or -not $fortisMatch[0].RW) {
        throw 'Unexpected Docker mount type, name, location or mode; nothing stopped.'
    }
    $fortisHostMatch = @($fortisHostMounts | Where-Object { $_.Target -ceq $fortisDestination })
    if ($fortisHostMatch.Count -ne 1 -or $fortisHostMatch[0].Type -cne 'volume' -or
        $fortisHostMatch[0].Source -cne 'fortis-repo-workspace') {
        throw 'Unexpected Docker HostConfig.Mounts; nothing stopped.'
    }
    # Docker may omit ReadOnly=false; still reject explicitly read-only requests.
    $fortisHostReadOnlyProperty = $fortisHostMatch[0].PSObject.Properties['ReadOnly']
    if ($null -ne $fortisHostReadOnlyProperty -and [bool]$fortisHostReadOnlyProperty.Value) {
        throw 'Unexpected Docker HostConfig.Mounts; nothing stopped.'
    }
    $fortisVolumeOpts = $fortisHostMatch[0].PSObject.Properties['VolumeOptions']
    $fortisActualSubpath = ''

    if ($null -ne $fortisVolumeOpts -and $null -ne $fortisVolumeOpts.Value) {
        $fortisSubpathProperty = $fortisVolumeOpts.Value.PSObject.Properties['Subpath']
        if ($null -ne $fortisSubpathProperty) {
            $fortisActualSubpath = [string]$fortisSubpathProperty.Value
        }
    }
    elseif ($fortisDestination -cne '/workspace/repo') {
        throw 'Missing Docker volume options; nothing stopped.'
    }
    if ($fortisActualSubpath -cne $fortisExpectedSubpaths[$fortisDestination]) {
        throw 'Unexpected Docker volume subpath; nothing stopped.'
    }
}
# Only read known runtime/config metadata. No MCP probe, marker or project tool call.
$fortisProbeCode = @'
const fs=require('fs'),crypto=require('crypto');const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');const s=fs.readFileSync('/proc/self/status','utf8');let cfg=null;try{cfg=JSON.parse(fs.readFileSync('/home/node/.claude-server-commander/config.json','utf8'))}catch(e){if(e.code!=='ENOENT')throw e;}const mi=fs.readFileSync('/proc/self/mountinfo','utf8').split('\n');console.log(JSON.stringify({uid:process.getuid(),capEff:s.match(/^CapEff:\s*(.+)$/m)?.[1],capBnd:s.match(/^CapBnd:\s*(.+)$/m)?.[1],noNewPrivs:s.match(/^NoNewPrivs:\s*(.+)$/m)?.[1],seccomp:s.match(/^Seccomp:\s*(.+)$/m)?.[1],rootReadOnly:mi.some(l=>{const a=l.split(' ');return a[4]==='/'&&a[5].split(',').includes('ro');}),directHash:hash('/opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js'),configMissing:cfg===null,allowedDirectories:cfg?.allowedDirectories??null,defaultShell:cfg?.defaultShell??null,telemetryEnabled:cfg?.telemetryEnabled??null}));
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
# Allow only exact recognized settings: already pinned, untouched stock defaults, or absent tmpfs file.
$fortisPinnedConfig = (-not $fortisProbe.configMissing) -and
    (@(Compare-Object -ReferenceObject $fortisExpectedRoots -DifferenceObject @($fortisProbe.allowedDirectories)).Count -eq 0) -and
    ($fortisProbe.defaultShell -eq '/bin/bash') -and ($fortisProbe.telemetryEnabled -eq $false)
$fortisFactoryDefaults = (-not $fortisProbe.configMissing) -and
    ($null -ne $fortisProbe.allowedDirectories) -and (@($fortisProbe.allowedDirectories).Count -eq 0) -and
    ($fortisProbe.defaultShell -eq '/bin/sh') -and ($fortisProbe.telemetryEnabled -eq $true)
$fortisConfigState = if ($fortisPinnedConfig) {'Pinned'} elseif ($fortisFactoryDefaults) {'FactoryDefaults'} elseif ($fortisProbe.configMissing) {'Missing'} else {'UnexpectedDrift'}
if ($fortisConfigState -eq 'UnexpectedDrift') {
    throw 'Unexpected Desktop Commander config drift; fail closed, do not repair.'
}
# PR-A-17: log-only preload is embedded in this reviewed Windows copy.
# Refuse to overwrite an existing NODE_OPTIONS policy. No mutable Docker helper file.
$fortisInheritedNodeOptions = @($fortisInfo.Config.Env | Where-Object {
    ([string]$_).StartsWith('NODE_OPTIONS=', [StringComparison]::Ordinal)
})
if ($fortisInheritedNodeOptions.Count -gt 1 -or
    ($fortisInheritedNodeOptions.Count -eq 1 -and $fortisInheritedNodeOptions[0] -cne 'NODE_OPTIONS=')) {
    throw 'Existing container NODE_OPTIONS requires separate review; nothing stopped.'
}
$fortisQuietPreloadSha256 = 'a18a0d409cd1e40bcb6bbb82935a041297aec43de34c65ac26015fa1f7422eb3'
$fortisQuietNodeOption = '--import=data:text/javascript;base64,Ly8gREMgMC4yLjUyIGVtaXRzIGVhY2ggbG9nZ2luZyBub3RpZmljYXRpb24gaW4gb25lIGNvbXBsZXRlIHN0ZG91dC53cml0ZS4KLy8gVGhpcyBhdmFpbGFiaWxpdHkgcG9saWN5IGlzIG5vdCBhIHNlY3VyaXR5IGJvdW5kYXJ5IG9yIGEgZ2VuZXJpYyBNQ1AgcHJveHkuCi8vIFVucmVjb2duaXNlZCwgbWFsZm9ybWVkLCBmcmFnbWVudGVkIGFuZCBiYXRjaGVkIHdyaXRlcyBwYXNzIHRocm91Z2ggdW5jaGFuZ2VkLgoKY29uc3Qgb3duT3B0aW9uID0gYC0taW1wb3J0PSR7aW1wb3J0Lm1ldGEudXJsfWA7CmlmIChwcm9jZXNzLmVudi5OT0RFX09QVElPTlMgPT09IG93bk9wdGlvbikgewogIC8vIFRoZSBwcmVsb2FkIGJlbG9uZ3MgdG8gdGhlIE1DUCBzZXJ2ZXIsIG5vdCBkZXZlbG9wbWVudCBjb21tYW5kcyBpdCBzcGF3bnMuCiAgZGVsZXRlIHByb2Nlc3MuZW52Lk5PREVfT1BUSU9OUzsKfQoKY29uc3Qgb3JpZ2luYWxXcml0ZSA9IHByb2Nlc3Muc3Rkb3V0LndyaXRlOwpjb25zdCBoYXNPd24gPSBPYmplY3QucHJvdG90eXBlLmhhc093blByb3BlcnR5OwoKZnVuY3Rpb24gaXNMb2dnaW5nTm90aWZpY2F0aW9uKGNodW5rLCBlbmNvZGluZykgewogIGlmIChlbmNvZGluZyAhPSBudWxsICYmIHR5cGVvZiBlbmNvZGluZyAhPT0gJ3N0cmluZycgJiYgdHlwZW9mIGVuY29kaW5nICE9PSAnZnVuY3Rpb24nKSByZXR1cm4gZmFsc2U7CiAgaWYgKHR5cGVvZiBlbmNvZGluZyA9PT0gJ3N0cmluZycgJiYgIUJ1ZmZlci5pc0VuY29kaW5nKGVuY29kaW5nKSkgcmV0dXJuIGZhbHNlOwogIGlmICh0eXBlb2YgY2h1bmsgIT09ICdzdHJpbmcnICYmICFCdWZmZXIuaXNCdWZmZXIoY2h1bmspKSByZXR1cm4gZmFsc2U7CiAgaWYgKHR5cGVvZiBjaHVuayA9PT0gJ3N0cmluZycgJiYgdHlwZW9mIGVuY29kaW5nID09PSAnc3RyaW5nJyAmJgogICAgICAhWyd1dGY4JywgJ3V0Zi04J10uaW5jbHVkZXMoZW5jb2RpbmcudG9Mb3dlckNhc2UoKSkpIHJldHVybiBmYWxzZTsKCiAgY29uc3QgdGV4dCA9IHR5cGVvZiBjaHVuayA9PT0gJ3N0cmluZycgPyBjaHVuayA6IGNodW5rLnRvU3RyaW5nKCd1dGY4Jyk7CiAgLy8gSW5zcGVjdCBvbmx5IGNvbXBsZXRlIHNpbmdsZS1saW5lIG1lc3NhZ2VzLCBhcyB3cml0dGVuIGJ5IHRoZSBwaW5uZWQgREMuCiAgaWYgKCF0ZXh0LmVuZHNXaXRoKCdcbicpIHx8IHRleHQuaW5kZXhPZignXG4nKSAhPT0gdGV4dC5sZW5ndGggLSAxIHx8CiAgICAgICF0ZXh0LmluY2x1ZGVzKCcibm90aWZpY2F0aW9ucy9tZXNzYWdlIicpKSByZXR1cm4gZmFsc2U7CiAgdHJ5IHsKICAgIGNvbnN0IHBhY2tldCA9IEpTT04ucGFyc2UodGV4dCk7CiAgICByZXR1cm4gcGFja2V0ICE9PSBudWxsICYmIHR5cGVvZiBwYWNrZXQgPT09ICdvYmplY3QnICYmICFBcnJheS5pc0FycmF5KHBhY2tldCkgJiYKICAgICAgcGFja2V0Lmpzb25ycGMgPT09ICcyLjAnICYmIHBhY2tldC5tZXRob2QgPT09ICdub3RpZmljYXRpb25zL21lc3NhZ2UnICYmCiAgICAgICFoYXNPd24uY2FsbChwYWNrZXQsICdpZCcpOwogIH0gY2F0Y2ggewogICAgcmV0dXJuIGZhbHNlOwogIH0KfQoKcHJvY2Vzcy5zdGRvdXQud3JpdGUgPSBmdW5jdGlvbiBxdWlldE1jcExvZ3MoY2h1bmssIGVuY29kaW5nLCBjYWxsYmFjaykgewogIGlmICgoY2FsbGJhY2sgPT0gbnVsbCB8fCB0eXBlb2YgY2FsbGJhY2sgPT09ICdmdW5jdGlvbicpICYmCiAgICAgIGlzTG9nZ2luZ05vdGlmaWNhdGlvbihjaHVuaywgZW5jb2RpbmcpKSB7CiAgICBjb25zdCBkb25lID0gdHlwZW9mIGVuY29kaW5nID09PSAnZnVuY3Rpb24nID8gZW5jb2RpbmcgOiBjYWxsYmFjazsKICAgIGlmICh0eXBlb2YgZG9uZSA9PT0gJ2Z1bmN0aW9uJykgcHJvY2Vzcy5uZXh0VGljayhkb25lKTsKICAgIHJldHVybiB0cnVlOwogIH0KICAvLyBQcmVzZXJ2ZSB0aGUgb3JpZ2luYWwgYnl0ZXMsIG92ZXJsb2FkcywgcmV0dXJuIHZhbHVlIGFuZCBiYWNrcHJlc3N1cmUuCiAgcmV0dXJuIFJlZmxlY3QuYXBwbHkob3JpZ2luYWxXcml0ZSwgdGhpcywgYXJndW1lbnRzKTsKfTsK'
# Fixed synthetic output only: no real MCP is started by this compatibility probe.
$fortisQuietProbeCode = @'
const fs=require('fs');const cg='/sys/fs/cgroup/';const n=p=>Number(fs.readFileSync(cg+p,'utf8'));const cap=[n('memory.max'),n('memory.current'),n('pids.max'),n('pids.current')];if(!cap.every(Number.isFinite)||cap[0]-cap[1]<268435456||cap[2]-cap[3]<48)process.exit(2);process.stdout.write(JSON.stringify({jsonrpc:'2.0',method:'notifications/message',params:{level:'info',data:'FORTIS_SYNTHETIC_LOG'}})+'\n');process.stdout.write(JSON.stringify({jsonrpc:'2.0',method:'notifications/progress',params:{progressToken:'fortis-quiet-preview',progress:1}})+'\n');process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:1,result:{quietPreloadOk:process.env.NODE_OPTIONS===undefined}})+'\n');
'@
$fortisQuietRaw = & $fortisDocker exec --user 1000:1000 --env ('NODE_OPTIONS=' + $fortisQuietNodeOption) $fortisContainer /usr/local/bin/node -e $fortisQuietProbeCode 2>$null
$fortisQuietExpected = @(
    '{"jsonrpc":"2.0","method":"notifications/progress","params":{"progressToken":"fortis-quiet-preview","progress":1}}'
    '{"jsonrpc":"2.0","id":1,"result":{"quietPreloadOk":true}}'
)
if ($LASTEXITCODE -ne 0 -or @($fortisQuietRaw).Count -ne 2 -or
    @($fortisQuietRaw)[0] -cne $fortisQuietExpected[0] -or @($fortisQuietRaw)[1] -cne $fortisQuietExpected[1]) {
    throw 'Quiet preload compatibility/headroom probe failed; nothing stopped or repaired.'
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
        DirectHashVerified = $true; ExistingTunnelCount = $existingTunnels.Count
        ExistingProfileCount = $existingProfiles.Count; SavedProfileEdits = $false
        QuietPreloadProbe = 'PASS'; QuietPreloadSha256 = $fortisQuietPreloadSha256
    } | ConvertTo-Json -Depth 4
    return
}
# Canary is a warm-run logging change, not a new cold-recovery procedure.
if (-not $fortisPinnedConfig) { throw 'Quiet canary requires already pinned DC config; nothing stopped.' }
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
# Boot repair is restricted to exact stock/missing tmpfs config and a known absent Git config.
# Do not disable the subsequent original config check. Never execute legacy Bridge/probe.
$fortisBootCode = @'
const fs=require('fs'),cp=require('child_process'),crypto=require('crypto');
const dc='/opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js';
const bridge='/workspace/repo/.fortis/mcp-bridge.mjs';
const file='/home/node/.claude-server-commander/config.json';
const folder='/home/node/.claude-server-commander';
const gitFile='/home/node/.gitconfig';
const expected=['/workspace/repos','/workspace/files','/workspace/repo'];
const fail=m=>{throw Error(m)};
if(process.getuid()!==1000)fail('Linux UID drift');
const home=fs.lstatSync('/home/node');
if(!home.isDirectory()||home.isSymbolicLink()||home.uid!==1000||(home.mode&0o777)!==0o700)fail('Home metadata drift');
const argsOf=p=>fs.readFileSync('/proc/'+p+'/cmdline','utf8').split('\0').filter(Boolean);
let dirExists=fs.existsSync(folder);
if(dirExists){const d=fs.lstatSync(folder);if(!d.isDirectory()||d.isSymbolicLink()||d.uid!==1000||(d.mode&0o777)!==0o755)fail('DC config directory drift')}
let existing=null,bytes=null,mode=0o644;
try{const s=fs.lstatSync(file);if(!s.isFile()||s.isSymbolicLink()||s.uid!==1000||(s.mode&0o777)!==0o644)fail('DC config file identity drift');bytes=fs.readFileSync(file);existing=JSON.parse(bytes.toString('utf8'));}
catch(e){if(e.code!=='ENOENT')throw e}
const pinned=x=>x&&Array.isArray(x.allowedDirectories)&&x.allowedDirectories.length===3&&expected.every(q=>x.allowedDirectories.includes(q))&&x.defaultShell==='/bin/bash'&&x.telemetryEnabled===false;
const stock=x=>x&&Array.isArray(x.allowedDirectories)&&x.allowedDirectories.length===0&&x.defaultShell==='/bin/sh'&&x.telemetryEnabled===true;
if(existing&&!pinned(existing)&&!stock(existing))fail('DC settings changed outside recognized defaults; refusing repair');
// An already pinned shared DC config needs no mutation: other profiles may serve MCP simultaneously.
// Only a reset/missing config requires a moment without ANY DC/Bridge process.
if(!pinned(existing)){
 for(const pid of fs.readdirSync('/proc').filter(x=>/^\d+$/.test(x))){
  try{const a=argsOf(pid);if(a.includes(dc)||a.includes(bridge))fail('Another MCP process exists during DC reset: '+pid)}
  catch(e){if(e.message.startsWith('Another MCP'))throw e}
 }
}
const g=cp.spawnSync('git',['config','--global','--get-all','safe.directory'],{encoding:'utf8'});
const a=cp.spawnSync('git',['config','--global','--get','core.autocrlf'],{encoding:'utf8'});
if(g.error||a.error)fail('Git unavailable');
let existingGit=false;try{fs.lstatSync(gitFile);existingGit=true}catch(e){if(e.code!=='ENOENT')throw e}
if(existingGit){
 const stat=fs.lstatSync(gitFile);
 if(!stat.isFile()||stat.isSymbolicLink()||stat.uid!==1000||![0o600,0o644].includes(stat.mode&0o777))fail('Git config metadata drift');
 if(g.status!==0||!g.stdout.trim().split('\n').includes('/workspace/repos/tunnel')||a.status!==0||a.stdout.trim()!=='true')fail('Unexpected existing Git config; do not rewrite');
} else if(g.status!==1||a.status!==1){fail('Git config source unexpectedly changed')}
function atomicWrite(target,data,mode,createOnly=false){
 const tmp=target+'.boot-'+process.pid+'-'+crypto.randomBytes(8).toString('hex');
 try{
  fs.writeFileSync(tmp,data,{flag:'wx',mode});
  if(createOnly)fs.linkSync(tmp,target); // EEXIST on races: never overwrite shared Git config.
  else fs.renameSync(tmp,target);
 }finally{try{fs.unlinkSync(tmp)}catch{}}
}
if(!dirExists){fs.mkdirSync(folder,{mode:0o755});const d=fs.lstatSync(folder);if(d.uid!==1000||(d.mode&0o777)!==0o755)fail('New config directory drift')}
if(!pinned(existing)){
 const next=existing||{};
 next.allowedDirectories=expected;
 next.defaultShell='/bin/bash';
 next.telemetryEnabled=false;
 if(bytes){
   const check=fs.readFileSync(file);
   if(!check.equals(bytes))fail('DC config changed during repair');
 } else if(fs.existsSync(file))fail('DC config appeared during repair');
 atomicWrite(file,JSON.stringify(next,null,2)+'\n',mode);
}
if(!existingGit){
 atomicWrite(gitFile,'[safe]\n\tdirectory = /workspace/repos/tunnel\n[core]\n\tautocrlf = true\n',0o600,true);
}
const chk=JSON.parse(fs.readFileSync(file,'utf8'));
if(!pinned(chk))fail('DC config post-verify failed');
const gitSafe=cp.spawnSync('git',['config','--global','--get-all','safe.directory'],{encoding:'utf8'});
const gitCrlf=cp.spawnSync('git',['config','--global','--get','core.autocrlf'],{encoding:'utf8'});
if(gitSafe.status!==0||!gitSafe.stdout.trim().split('\n').includes('/workspace/repos/tunnel')||gitCrlf.status!==0||gitCrlf.stdout.trim()!=='true')fail('Git config post-verify failed');
console.log('REBOOT_BOOTSTRAP_PASS');
'@
$fortisBootOutput = & $fortisDocker exec $fortisContainer /usr/local/bin/node -e $fortisBootCode 2>$null
if ($LASTEXITCODE -ne 0 -or @($fortisBootOutput).Count -ne 1 -or @($fortisBootOutput)[0] -ne 'REBOOT_BOOTSTRAP_PASS') {
    throw 'Guarded Docker tmpfs reboot bootstrap failed. Do not start tunnel.'
}
$fortisProbeRaw = & $fortisDocker exec $fortisContainer /usr/local/bin/node -e $fortisProbeCode 2>$null
if ($LASTEXITCODE -ne 0) { throw 'Post-bootstrap read-only preflight failed.' }
$fortisProbe = $fortisProbeRaw | ConvertFrom-Json
if ($fortisProbe.configMissing -or
    @(Compare-Object -ReferenceObject $fortisExpectedRoots -DifferenceObject @($fortisProbe.allowedDirectories)).Count -ne 0 -or
    $fortisProbe.defaultShell -ne '/bin/bash' -or $fortisProbe.telemetryEnabled -ne $false) {
    throw 'Post-bootstrap DC config verification failed.'
}
$mcpCommand = 'command=docker exec -i --env NODE_OPTIONS=' + $fortisQuietNodeOption + ' fortis-repo-test /usr/local/bin/node /opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js'
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
