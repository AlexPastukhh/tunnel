param([ValidateSet('Preview','Run')][string]$Mode='Preview')
# PR-A-16 / Repo2 standalone guard. SOURCE only, NOT Windows installed.
# All checks read-only in Preview; guarded tmpfs bootstrap in Run.
# No interaction with first Repo tunnel/control, no profile mutations, no key reads.
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows PowerShell is required.' }
$fortisIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($fortisIdentity.Name -ine 'FORTIS_M\alexa') { throw 'Unexpected Windows identity.' }
$fortisPrincipal = New-Object Security.Principal.WindowsPrincipal($fortisIdentity)
if ($fortisPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Use a normal, non-elevated PowerShell.'
}
$fortisDocker = (Get-Command docker.exe -CommandType Application -ErrorAction Stop).Source
$fortisContainer = 'fortis-repo-test'
$fortisExpectedContainerId = '0c0f8cb2d608679b4c3de51c527cbe2aca687cbf1360e6bf116444b2a0928cc2'

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
if ($fortisNetworks.Count -lt 1 -or $fortisNetworks.Count -gt 2 -or
    $fortisNetworks -cnotcontains 'fortis-repo-egress' -or
    @($fortisNetworks | Where-Object {
        $_ -cne 'fortis-repo-egress' -and $_ -cne 'rdg-personal_agents'
    }).Count -ne 0) {
    throw 'Container network membership changed; nothing stopped.'
}
# Optional RDG peer is allowed only on its named internal bridge network.
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

if ($Mode -eq 'Preview') {
    [pscustomobject]@{
        Mode = 'Preview'
        Preflight = $(if ($fortisPinnedConfig) {'PASS'} else {'REBOOT_REPAIR_REQUIRED'})
        ConfigState = $fortisConfigState
        ContainerIdMatched = $true
        LinuxUid = $fortisProbe.uid
        DirectModuleHashVerified = $true
        NoWindowsProfileEdits = $true
    } | ConvertTo-Json -Depth 3
    return
}

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

Write-Output 'REPO2_DIRECT_GUARD_PASS'
