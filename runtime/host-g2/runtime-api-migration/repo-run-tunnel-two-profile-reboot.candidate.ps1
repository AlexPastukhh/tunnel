param([ValidateSet('Preview','Run')][string]$Mode='Run')
# PR-A-15 CANDIDATE. Source only; NOT installed. Owner-gated two-profile boot repair.
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
    } | ConvertTo-Json -Depth 4
    return
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
