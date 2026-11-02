# Shared Repo1/Repo2 policy. Keep common trust decisions here, not in either launcher.
# PowerShell 5.1 compatible; one shared policy for both Windows Repo launchers.

$script:FortisPolicy = @{
    OwnerSid = 'S-1-5-21-303538662-3368424508-2654684973-1001'
    PolicySourceSha256 = 'C7EA99D7030635C62A1BF856C6F751B043E62C5248EDC5E03440400CCAF8422E'
    ContainerName = 'fortis-repo-test'
    LinuxUser = '1000:1000'
    RequiredNetwork = 'fortis-repo-egress'
    OptionalInternalNetwork = 'rdg-personal_agents'
    RequiredTmpfs = @('/tmp', '/home/node')
    AllowedExtraTmpfsRoots = @('/tmp/')
    RequiredMounts = @(
        [pscustomobject]@{ Type='volume'; Source='fortis-repo-workspace'; Target='/workspace/repo'; Subpath=''; ReadOnly=$false }
        [pscustomobject]@{ Type='volume'; Source='fortis-repo-workspace'; Target='/workspace/repos'; Subpath='Repos'; ReadOnly=$false }
        [pscustomobject]@{ Type='volume'; Source='fortis-repo-workspace'; Target='/workspace/files'; Subpath='Workfiles'; ReadOnly=$false }
    )
    OptionalMounts = @(
        [pscustomobject]@{ Type='volume'; Source='fortis-r7-client'; Target='/run/fortis-client'; Subpath=''; ReadOnly=$true }
    )
    MaxMemoryBytes = 8589934592
    MaxNanoCpus = 2000000000
    MaxPids = 1024
    WindowsRuntimePath = 'C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe'
    WindowsRuntimeSha256 = 'A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A'
    QuietNodeOption = '--import=data:text/javascript;base64,Ly8gREMgMC4yLjUyIGVtaXRzIGVhY2ggbG9nZ2luZyBub3RpZmljYXRpb24gaW4gb25lIGNvbXBsZXRlIHN0ZG91dC53cml0ZS4KLy8gVGhpcyBhdmFpbGFiaWxpdHkgcG9saWN5IGlzIG5vdCBhIHNlY3VyaXR5IGJvdW5kYXJ5IG9yIGEgZ2VuZXJpYyBNQ1AgcHJveHkuCi8vIFVucmVjb2duaXNlZCwgbWFsZm9ybWVkLCBmcmFnbWVudGVkIGFuZCBiYXRjaGVkIHdyaXRlcyBwYXNzIHRocm91Z2ggdW5jaGFuZ2VkLgoKY29uc3Qgb3duT3B0aW9uID0gYC0taW1wb3J0PSR7aW1wb3J0Lm1ldGEudXJsfWA7CmlmIChwcm9jZXNzLmVudi5OT0RFX09QVElPTlMgPT09IG93bk9wdGlvbikgewogIC8vIFRoZSBwcmVsb2FkIGJlbG9uZ3MgdG8gdGhlIE1DUCBzZXJ2ZXIsIG5vdCBkZXZlbG9wbWVudCBjb21tYW5kcyBpdCBzcGF3bnMuCiAgZGVsZXRlIHByb2Nlc3MuZW52Lk5PREVfT1BUSU9OUzsKfQoKY29uc3Qgb3JpZ2luYWxXcml0ZSA9IHByb2Nlc3Muc3Rkb3V0LndyaXRlOwpjb25zdCBoYXNPd24gPSBPYmplY3QucHJvdG90eXBlLmhhc093blByb3BlcnR5OwoKZnVuY3Rpb24gaXNMb2dnaW5nTm90aWZpY2F0aW9uKGNodW5rLCBlbmNvZGluZykgewogIGlmIChlbmNvZGluZyAhPSBudWxsICYmIHR5cGVvZiBlbmNvZGluZyAhPT0gJ3N0cmluZycgJiYgdHlwZW9mIGVuY29kaW5nICE9PSAnZnVuY3Rpb24nKSByZXR1cm4gZmFsc2U7CiAgaWYgKHR5cGVvZiBlbmNvZGluZyA9PT0gJ3N0cmluZycgJiYgIUJ1ZmZlci5pc0VuY29kaW5nKGVuY29kaW5nKSkgcmV0dXJuIGZhbHNlOwogIGlmICh0eXBlb2YgY2h1bmsgIT09ICdzdHJpbmcnICYmICFCdWZmZXIuaXNCdWZmZXIoY2h1bmspKSByZXR1cm4gZmFsc2U7CiAgaWYgKHR5cGVvZiBjaHVuayA9PT0gJ3N0cmluZycgJiYgdHlwZW9mIGVuY29kaW5nID09PSAnc3RyaW5nJyAmJgogICAgICAhWyd1dGY4JywgJ3V0Zi04J10uaW5jbHVkZXMoZW5jb2RpbmcudG9Mb3dlckNhc2UoKSkpIHJldHVybiBmYWxzZTsKCiAgY29uc3QgdGV4dCA9IHR5cGVvZiBjaHVuayA9PT0gJ3N0cmluZycgPyBjaHVuayA6IGNodW5rLnRvU3RyaW5nKCd1dGY4Jyk7CiAgLy8gSW5zcGVjdCBvbmx5IGNvbXBsZXRlIHNpbmdsZS1saW5lIG1lc3NhZ2VzLCBhcyB3cml0dGVuIGJ5IHRoZSBwaW5uZWQgREMuCiAgaWYgKCF0ZXh0LmVuZHNXaXRoKCdcbicpIHx8IHRleHQuaW5kZXhPZignXG4nKSAhPT0gdGV4dC5sZW5ndGggLSAxIHx8CiAgICAgICF0ZXh0LmluY2x1ZGVzKCcibm90aWZpY2F0aW9ucy9tZXNzYWdlIicpKSByZXR1cm4gZmFsc2U7CiAgdHJ5IHsKICAgIGNvbnN0IHBhY2tldCA9IEpTT04ucGFyc2UodGV4dCk7CiAgICByZXR1cm4gcGFja2V0ICE9PSBudWxsICYmIHR5cGVvZiBwYWNrZXQgPT09ICdvYmplY3QnICYmICFBcnJheS5pc0FycmF5KHBhY2tldCkgJiYKICAgICAgcGFja2V0Lmpzb25ycGMgPT09ICcyLjAnICYmIHBhY2tldC5tZXRob2QgPT09ICdub3RpZmljYXRpb25zL21lc3NhZ2UnICYmCiAgICAgICFoYXNPd24uY2FsbChwYWNrZXQsICdpZCcpOwogIH0gY2F0Y2ggewogICAgcmV0dXJuIGZhbHNlOwogIH0KfQoKcHJvY2Vzcy5zdGRvdXQud3JpdGUgPSBmdW5jdGlvbiBxdWlldE1jcExvZ3MoY2h1bmssIGVuY29kaW5nLCBjYWxsYmFjaykgewogIGlmICgoY2FsbGJhY2sgPT0gbnVsbCB8fCB0eXBlb2YgY2FsbGJhY2sgPT09ICdmdW5jdGlvbicpICYmCiAgICAgIGlzTG9nZ2luZ05vdGlmaWNhdGlvbihjaHVuaywgZW5jb2RpbmcpKSB7CiAgICBjb25zdCBkb25lID0gdHlwZW9mIGVuY29kaW5nID09PSAnZnVuY3Rpb24nID8gZW5jb2RpbmcgOiBjYWxsYmFjazsKICAgIGlmICh0eXBlb2YgZG9uZSA9PT0gJ2Z1bmN0aW9uJykgcHJvY2Vzcy5uZXh0VGljayhkb25lKTsKICAgIHJldHVybiB0cnVlOwogIH0KICAvLyBQcmVzZXJ2ZSB0aGUgb3JpZ2luYWwgYnl0ZXMsIG92ZXJsb2FkcywgcmV0dXJuIHZhbHVlIGFuZCBiYWNrcHJlc3N1cmUuCiAgcmV0dXJuIFJlZmxlY3QuYXBwbHkob3JpZ2luYWxXcml0ZSwgdGhpcywgYXJndW1lbnRzKTsKfTsK'
    QuietPreloadSha256 = 'a18a0d409cd1e40bcb6bbb82935a041297aec43de34c65ac26015fa1f7422eb3'
    LinuxNodePath = '/usr/local/bin/node'
    DirectEntryPath = '/opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js'
    LegacyBridgePath = '/workspace/repo/.fortis/mcp-bridge.mjs'
    ConfigDirectory = '/home/node/.claude-server-commander'
    ConfigPath = '/home/node/.claude-server-commander/config.json'
    GitConfigPath = '/home/node/.gitconfig'
    HomePath = '/home/node'
    AllowedDirectories = @('/workspace/repos', '/workspace/files', '/workspace/repo')
}

$script:FortisPolicySourcePath = $PSCommandPath

function Get-FortisObjectValue {
    param($Object, [string]$Name, $Default = $null)
    if ($null -eq $Object) { return $Default }
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) { return $Default }
    return $property.Value
}

function Assert-FortisWindowsOwner {
    if ($env:OS -ne 'Windows_NT') { throw 'Windows PowerShell is required.' }
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    if ($null -eq $identity.User -or $identity.User.Value -cne $script:FortisPolicy.OwnerSid) {
        throw 'Run from the original Fortis owner Windows account.'
    }
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Use a normal, non-elevated PowerShell window.'
    }
    return $identity
}

function Get-FortisDockerPath {
    return (Get-Command docker.exe -CommandType Application -ErrorAction Stop).Source
}

function Assert-FortisContainerPolicy {
    param($Info, [string]$DockerPath)

    if ($Info.Name -cne ('/' + $script:FortisPolicy.ContainerName) -or
        [string]$Info.Id -cnotmatch '^[0-9a-f]{64}$') {
        throw 'Unexpected Fortis container name or ID.'
    }

    $hostConfig = $Info.HostConfig
    if ($Info.Config.User -cne $script:FortisPolicy.LinuxUser -or
        $hostConfig.Privileged -eq $true -or
        $hostConfig.ReadonlyRootfs -ne $true) {
        throw 'Fortis user, privilege or read-only rootfs policy changed.'
    }
    foreach ($namespace in @('PidMode','IpcMode','UTSMode','UsernsMode','CgroupnsMode')) {
        $mode = [string](Get-FortisObjectValue $hostConfig $namespace '')
        if ($mode -notin @('', 'private')) { throw "Host namespace sharing is not allowed: $namespace" }
    }
    foreach ($listName in @('Devices','DeviceRequests','VolumesFrom','GroupAdd')) {
        $value = Get-FortisObjectValue $hostConfig $listName
        if ($null -ne $value -and @($value).Count -ne 0) {
            throw "Unexpected host device, supplementary group or inherited volume: $listName"
        }
    }

    $capDrop = @($hostConfig.CapDrop | ForEach-Object { [string]$_ })
    $capAddValue = Get-FortisObjectValue $hostConfig 'CapAdd'
    $capAddCount = 0
    if ($null -ne $capAddValue) { $capAddCount = @($capAddValue).Count }
    if ($capDrop -notcontains 'ALL' -or $capAddCount -ne 0) {
        throw 'Fortis capabilities must remain fully dropped with no additions.'
    }
    $securityOptions = @($hostConfig.SecurityOpt | ForEach-Object { [string]$_ })
    if (@($securityOptions | Where-Object { $_ -match '^no-new-privileges(?::true)?$' }).Count -eq 0) {
        throw 'Fortis no-new-privileges policy is missing.'
    }
    if (@($securityOptions | Where-Object { $_ -match '^(seccomp|apparmor)=unconfined$' }).Count -ne 0) {
        throw 'Unconfined seccomp/AppArmor is not allowed.'
    }

    # These are ceilings, not exact tuning values. Stricter/lower allocations remain valid.
    $memory = [long](Get-FortisObjectValue $hostConfig 'Memory' 0)
    $nanoCpus = [long](Get-FortisObjectValue $hostConfig 'NanoCpus' 0)
    $pidsLimit = [long](Get-FortisObjectValue $hostConfig 'PidsLimit' 0)
    if ($memory -le 0 -or $memory -gt $script:FortisPolicy.MaxMemoryBytes -or
        $nanoCpus -le 0 -or $nanoCpus -gt $script:FortisPolicy.MaxNanoCpus -or
        $pidsLimit -le 0 -or $pidsLimit -gt $script:FortisPolicy.MaxPids) {
        throw 'Fortis resource ceilings are missing or exceeded.'
    }

    $tmpfs = Get-FortisObjectValue $hostConfig 'Tmpfs'
    $tmpfsNames = @()
    if ($null -ne $tmpfs) { $tmpfsNames = @($tmpfs.PSObject.Properties | ForEach-Object { $_.Name }) }
    foreach ($path in $script:FortisPolicy.RequiredTmpfs) {
        if ($tmpfsNames -cnotcontains $path) { throw "Required tmpfs is missing: $path" }
    }
    foreach ($path in $tmpfsNames) {
        if ($script:FortisPolicy.RequiredTmpfs -ccontains $path) { continue }
        $segments = @($path.Split('/') | Where-Object { $_ -ne '' })
        $hasTraversal = @($segments | Where-Object { $_ -in @('.', '..') }).Count -ne 0
        $safeScratchPath = -not $hasTraversal -and @($script:FortisPolicy.AllowedExtraTmpfsRoots | Where-Object { $path.StartsWith($_, [StringComparison]::Ordinal) }).Count -gt 0
        if (-not $safeScratchPath) { throw "Unexpected tmpfs outside approved scratch roots: $path" }
    }

    $portBindings = Get-FortisObjectValue $hostConfig 'PortBindings'
    $publishedPorts = 0
    if ($null -ne $portBindings) { $publishedPorts = @($portBindings.PSObject.Properties).Count }
    if ($publishedPorts -ne 0 -or (Get-FortisObjectValue $hostConfig 'PublishAllPorts' $false) -eq $true) {
        throw 'Fortis must not publish container ports.'
    }

    $binds = Get-FortisObjectValue $hostConfig 'Binds'
    if ($null -ne $binds -and @($binds).Count -ne 0) {
        throw 'Unexpected Docker bind mount; only the reviewed named volumes are allowed.'
    }
    $requestedMounts = @(Get-FortisObjectValue $hostConfig 'Mounts')
    # Docker inspect objects can omit optional properties. Read Type defensively:
    # only an explicit tmpfs is filtered; missing/unknown metadata stays in the
    # list and is rejected below (fail closed, without a StrictMode property error).
    $effectiveMounts = @((Get-FortisObjectValue $Info 'Mounts') | Where-Object {
        [string](Get-FortisObjectValue $_ 'Type' '') -cne 'tmpfs'
    })
    $allowedMounts = @($script:FortisPolicy.RequiredMounts) + @($script:FortisPolicy.OptionalMounts)
    $allowedTargets = @($allowedMounts | ForEach-Object { $_.Target })
    if ($requestedMounts.Count -notin @(3,4) -or $effectiveMounts.Count -ne $requestedMounts.Count) {
        throw 'Unexpected Docker mount count or disagreement between requested and effective mounts.'
    }
    foreach ($mount in $effectiveMounts) {
        foreach ($field in @('Type','Name','Destination','RW')) {
            $value = Get-FortisObjectValue $mount $field
            if ($null -eq $value -or [string]::IsNullOrWhiteSpace([string]$value)) {
                throw "Effective Docker mount metadata is incomplete: $field"
            }
        }
    }
    foreach ($target in $allowedTargets) {
        $requested = @($requestedMounts | Where-Object { (Get-FortisObjectValue $_ 'Target' '') -ceq $target })
        $effective = @($effectiveMounts | Where-Object { (Get-FortisObjectValue $_ 'Destination' '') -ceq $target })
        $required = @($script:FortisPolicy.RequiredMounts | Where-Object { $_.Target -ceq $target }).Count -eq 1
        if ($required -and ($requested.Count -ne 1 -or $effective.Count -ne 1)) {
            throw "Required Fortis mount is missing or duplicated: $target"
        }
        if (-not $required -and ($requested.Count -gt 1 -or $effective.Count -gt 1)) {
            throw "Optional Fortis mount is duplicated: $target"
        }
        if ($requested.Count -eq 0 -and $effective.Count -eq 0) { continue }
        if ($requested.Count -ne 1 -or $effective.Count -ne 1) {
            throw "Requested/effective Docker mount views differ: $target"
        }
        $rule = @($allowedMounts | Where-Object { $_.Target -ceq $target })[0]
        $volumeOptions = Get-FortisObjectValue $requested[0] 'VolumeOptions'
        $subpath = [string](Get-FortisObjectValue $volumeOptions 'Subpath' '')
        $readOnlyProperty = $requested[0].PSObject.Properties['ReadOnly']
        $requestedReadOnly = $false
        if ($null -ne $readOnlyProperty) { $requestedReadOnly = [bool]$readOnlyProperty.Value }
        $effectiveReadWrite = [bool](Get-FortisObjectValue $effective[0] 'RW' $false)
        if ($requested[0].Type -cne $rule.Type -or
            $requested[0].Source -cne $rule.Source -or
            $requested[0].Target -cne $rule.Target -or
            $subpath -cne $rule.Subpath -or
            $requestedReadOnly -ne $rule.ReadOnly -or
            (Get-FortisObjectValue $effective[0] 'Type' '') -cne $rule.Type -or
            (Get-FortisObjectValue $effective[0] 'Name' '') -cne $rule.Source -or
            (Get-FortisObjectValue $effective[0] 'Destination' '') -cne $rule.Target -or
            $effectiveReadWrite -ne [bool](-not $rule.ReadOnly)) {
            throw "Fortis mount identity or access mode changed: $target"
        }
    }
    $unknownRequested = @($requestedMounts | Where-Object { $allowedTargets -cnotcontains $_.Target })
    $unknownEffective = @($effectiveMounts | Where-Object { $allowedTargets -cnotcontains (Get-FortisObjectValue $_ 'Destination' '') })
    if ($unknownRequested.Count -ne 0 -or $unknownEffective.Count -ne 0) {
        throw 'Unexpected extra Docker mount (including Docker socket or unreviewed host path).'
    }

    $networkMode = [string](Get-FortisObjectValue $hostConfig 'NetworkMode' '')
    if ($networkMode -match '^(host|none|container:|service:)' ) {
        throw 'Host/shared network namespaces are not allowed.'
    }
    $networkMap = Get-FortisObjectValue (Get-FortisObjectValue $Info 'NetworkSettings') 'Networks'
    $networkNames = @()
    if ($null -ne $networkMap) { $networkNames = @($networkMap.PSObject.Properties | ForEach-Object { $_.Name }) }
    if ($networkNames.Count -lt 1 -or $networkNames.Count -gt 2 -or
        $networkNames -cnotcontains $script:FortisPolicy.RequiredNetwork -or
        @($networkNames | Where-Object {
            $_ -cne $script:FortisPolicy.RequiredNetwork -and $_ -cne $script:FortisPolicy.OptionalInternalNetwork
        }).Count -ne 0) {
        throw 'Fortis network membership changed.'
    }
    if ($networkNames -ccontains $script:FortisPolicy.OptionalInternalNetwork) {
        if ([string]::IsNullOrWhiteSpace($DockerPath)) { throw 'Docker path is required to verify the optional RDG network.' }
        $networkRaw = @(& $DockerPath network inspect $script:FortisPolicy.OptionalInternalNetwork 2>$null)
        if ($LASTEXITCODE -ne 0 -or $networkRaw.Count -eq 0) { throw 'Could not inspect the optional RDG network.' }
        $networkInfo = @(($networkRaw -join "`n") | ConvertFrom-Json)[0]
        if ($networkInfo.Name -cne $script:FortisPolicy.OptionalInternalNetwork -or
            $networkInfo.Driver -cne 'bridge' -or $networkInfo.Internal -ne $true) {
            throw 'Optional RDG network must remain an internal bridge.'
        }
    }

    $containerEnv = @((Get-FortisObjectValue $Info.Config 'Env') | ForEach-Object { [string]$_ })
    $nodeOptions = @($containerEnv | Where-Object { $_.StartsWith('NODE_OPTIONS=', [StringComparison]::Ordinal) })
    if ($nodeOptions.Count -gt 1 -or ($nodeOptions.Count -eq 1 -and $nodeOptions[0] -cne 'NODE_OPTIONS=')) {
        throw 'Container NODE_OPTIONS can inject code into Node processes; review it separately.'
    }
}

function Get-FortisContainerContext {
    param([string]$ContainerId, [switch]$AllowStopped)
    $null = Assert-FortisWindowsOwner
    $docker = Get-FortisDockerPath
    $target = $script:FortisPolicy.ContainerName
    if (-not [string]::IsNullOrWhiteSpace($ContainerId)) { $target = $ContainerId }
    $raw = @(& $docker inspect --type container -- $target 2>$null)
    if ($LASTEXITCODE -ne 0 -or $raw.Count -eq 0) { throw 'Fortis container is missing or Docker is unavailable.' }
    $items = @(($raw -join "`n") | ConvertFrom-Json)
    if ($items.Count -ne 1) { throw 'Docker inspect did not return exactly one Fortis container.' }
    $info = $items[0]
    if (-not [string]::IsNullOrWhiteSpace($ContainerId) -and $info.Id -cne $ContainerId) {
        throw 'The inspected container ID changed.'
    }
    Assert-FortisContainerPolicy -Info $info -DockerPath $docker
    if (-not $AllowStopped -and -not $info.State.Running) { throw 'Fortis container is not running.' }
    return [pscustomobject]@{ DockerPath=$docker; ContainerId=[string]$info.Id; Info=$info }
}

function Start-FortisContainer {
    param($Context)
    & $Context.DockerPath start $Context.ContainerId | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Could not start the already-existing Fortis container.' }
    return (Get-FortisContainerContext -ContainerId $Context.ContainerId)
}

function Invoke-FortisDockerExec {
    param($Context, [string[]]$Command, [string[]]$Options = @())
    $output = @(& $Context.DockerPath exec @Options $Context.ContainerId @Command 2>$null)
    if ($LASTEXITCODE -ne 0) { throw 'Guarded Docker exec failed.' }
    return $output
}

function ConvertTo-FortisJsonLiteral {
    param($Value)
    return (ConvertTo-Json -InputObject $Value -Compress -Depth 8)
}

function Get-FortisLinuxProbeCode {
    $code = @'
const fs=require('fs');
const p='/proc/self/status';
const status=fs.readFileSync(p,'utf8');
const match=name=>{const m=status.match(new RegExp('^'+name+':\\s*(.+)$','m'));return m?m[1].trim():null;};
const mounts=fs.readFileSync('/proc/self/mountinfo','utf8').split('\n');
const root=mounts.map(line=>line.split(' ')).find(parts=>parts[4]==='/');
const entry=__DIRECT_ENTRY_PATH__;
let directEntryAvailable=false;
try{const st=fs.lstatSync(entry);directEntryAvailable=st.isFile()&&!st.isSymbolicLink();if(directEntryAvailable)fs.accessSync(entry,fs.constants.R_OK);}catch(e){if(e.code!=='ENOENT'&&e.code!=='EACCES')throw e;directEntryAvailable=false;}
const home=__HOME_PATH__,folder=__CONFIG_DIRECTORY__,file=__CONFIG_PATH__;
const homeStat=fs.lstatSync(home);
const homeSafe=homeStat.isDirectory()&&!homeStat.isSymbolicLink()&&homeStat.uid===__LINUX_UID__&&(homeStat.mode&0o077)===0;
let configDirectorySafe=true,configDirectoryMissing=false;
try{const d=fs.lstatSync(folder);configDirectorySafe=d.isDirectory()&&!d.isSymbolicLink()&&d.uid===__LINUX_UID__&&(d.mode&0o022)===0;}
catch(e){if(e.code==='ENOENT')configDirectoryMissing=true;else throw e;}
let cfg=null,configFileSafe=true,configFileMissing=false;
try{const st=fs.lstatSync(file);configFileSafe=st.isFile()&&!st.isSymbolicLink()&&st.uid===__LINUX_UID__&&(st.mode&0o022)===0;if(!configFileSafe)throw Error('DC config file metadata drift');cfg=JSON.parse(fs.readFileSync(file,'utf8'));}
catch(e){if(e.code==='ENOENT')configFileMissing=true;else throw e;}
console.log(JSON.stringify({uid:process.getuid(),euid:process.geteuid(),gid:process.getgid(),egid:process.getegid(),capEff:match('CapEff'),capBnd:match('CapBnd'),noNewPrivs:match('NoNewPrivs'),seccomp:match('Seccomp'),rootReadOnly:!!root&&root[5].split(',').includes('ro'),directEntryAvailable,homeSafe,configDirectorySafe,configDirectoryMissing,configFileSafe,configFileMissing,configMissing:configFileMissing,allowedDirectories:cfg?cfg.allowedDirectories:null}));
'@
    $uid = [int]($script:FortisPolicy.LinuxUser.Split(':')[0])
    $gid = [int]($script:FortisPolicy.LinuxUser.Split(':')[1])
    return $code.Replace('__DIRECT_ENTRY_PATH__', (ConvertTo-FortisJsonLiteral $script:FortisPolicy.DirectEntryPath)).Replace('__HOME_PATH__', (ConvertTo-FortisJsonLiteral $script:FortisPolicy.HomePath)).Replace('__CONFIG_DIRECTORY__', (ConvertTo-FortisJsonLiteral $script:FortisPolicy.ConfigDirectory)).Replace('__CONFIG_PATH__', (ConvertTo-FortisJsonLiteral $script:FortisPolicy.ConfigPath)).Replace('__LINUX_UID__', [string]$uid)
}

function Get-FortisLinuxRuntimeSnapshot {
    param($Context)
    $code = Get-FortisLinuxProbeCode
    $raw = Invoke-FortisDockerExec -Context $Context -Command @($script:FortisPolicy.LinuxNodePath, '-e', $code)
    $probe = ($raw -join "`n") | ConvertFrom-Json
    $linuxUid = [int]($script:FortisPolicy.LinuxUser.Split(':')[0])
    $linuxGid = [int]($script:FortisPolicy.LinuxUser.Split(':')[1])
    if ($probe.uid -ne $linuxUid -or $probe.euid -ne $linuxUid -or
        $probe.gid -ne $linuxGid -or $probe.egid -ne $linuxGid -or
        $probe.capEff -notmatch '^0+$' -or $probe.capBnd -notmatch '^0+$' -or
        $probe.noNewPrivs -ne '1' -or $probe.seccomp -ne '2' -or
        -not $probe.rootReadOnly -or -not $probe.directEntryAvailable -or
        -not $probe.homeSafe -or -not $probe.configDirectorySafe -or -not $probe.configFileSafe) {
        throw 'Effective Linux identity, capabilities, seccomp, rootfs, config permissions or Direct entry policy changed.'
    }

    $roots = @($probe.allowedDirectories | ForEach-Object { [string]$_ })
    $configState = 'UnexpectedDrift'
    if ($probe.configMissing) { $configState = 'Missing' }
    elseif ($null -ne $probe.allowedDirectories -and $roots.Count -eq 0) { $configState = 'FactoryDefaults' }
    elseif ($roots.Count -eq $script:FortisPolicy.AllowedDirectories.Count -and
        @($roots | Sort-Object -Unique).Count -eq $script:FortisPolicy.AllowedDirectories.Count -and
        @($script:FortisPolicy.AllowedDirectories | Where-Object { $roots -cnotcontains $_ }).Count -eq 0) {
        $configState = 'Pinned'
    }
    if ($configState -eq 'UnexpectedDrift') {
        throw 'Desktop Commander allowedDirectories drifted; refusing automatic repair.'
    }
    return [pscustomobject]@{ Probe=$probe; ConfigState=$configState; LinuxSecurityVerified=$true; DirectEntryAvailable=$true }
}

function Get-FortisRuntimeBootstrapCode {
    $code = @'
const fs=require('fs'),crypto=require('crypto');
const dc=__DIRECT_ENTRY_PATH__;
const bridge=__LEGACY_BRIDGE_PATH__;
const home=__HOME_PATH__;
const folder=__CONFIG_DIRECTORY__;
const file=__CONFIG_PATH__;
const gitFile=__GIT_CONFIG_PATH__;
const expected=__ALLOWED_DIRECTORIES__;
const fail=m=>{throw Error(m)};
if(process.getuid()!==__LINUX_UID__||process.geteuid()!==__LINUX_UID__||process.getgid()!==__LINUX_GID__||process.getegid()!==__LINUX_GID__)fail('Linux identity drift');
const homeStat=fs.lstatSync(home);
if(!homeStat.isDirectory()||homeStat.isSymbolicLink()||homeStat.uid!==__LINUX_UID__||(homeStat.mode&0o077)!==0)fail('Home directory metadata drift');
let folderExists=true;
try{const d=fs.lstatSync(folder);if(!d.isDirectory()||d.isSymbolicLink()||d.uid!==__LINUX_UID__||(d.mode&0o022)!==0)fail('DC config directory metadata drift');}
catch(e){if(e.code==='ENOENT')folderExists=false;else throw e;}
let existing=null,bytes=null,fileMode=0o644;
try{const st=fs.lstatSync(file);if(!st.isFile()||st.isSymbolicLink()||st.uid!==__LINUX_UID__||(st.mode&0o022)!==0)fail('DC config file metadata drift');fileMode=st.mode&0o777;bytes=fs.readFileSync(file);existing=JSON.parse(bytes.toString('utf8'));}
catch(e){if(e.code!=='ENOENT')throw e;}
const roots=existing?existing.allowedDirectories:null;
const pinned=Array.isArray(roots)&&roots.length===expected.length&&new Set(roots).size===expected.length&&expected.every(x=>roots.includes(x));
const stock=Array.isArray(roots)&&roots.length===0;
if(existing&&!pinned&&!stock)fail('Unknown DC allowedDirectories state; refusing repair');
if(!pinned){
 for(const pid of fs.readdirSync('/proc').filter(x=>/^\d+$/.test(x))){
  try{const args=fs.readFileSync('/proc/'+pid+'/cmdline','utf8').split('\0');if(args.includes(dc)||args.includes(bridge))fail('Another MCP process is active during config repair');}
  catch(e){if(e.message.startsWith('Another MCP'))throw e;if(e.code!=='ENOENT'&&e.code!=='EACCES')throw e;}
 }
}
function atomicWrite(target,data,mode,createOnly){
 const temp=target+'.boot-'+process.pid+'-'+crypto.randomBytes(8).toString('hex');
 try{fs.writeFileSync(temp,data,{flag:'wx',mode});if(createOnly)fs.linkSync(temp,target);else fs.renameSync(temp,target);}
 finally{try{fs.unlinkSync(temp);}catch(e){if(e.code!=='ENOENT')throw e;}}
}
if(!folderExists){fs.mkdirSync(folder,{mode:0o755});const d=fs.lstatSync(folder);if(d.uid!==__LINUX_UID__||(d.mode&0o022)!==0)fail('New config directory metadata drift');}
if(!pinned){
 const next=existing||{};next.allowedDirectories=expected;
 if(bytes){if(!fs.readFileSync(file).equals(bytes))fail('DC config changed during repair');}
 else if(fs.existsSync(file))fail('DC config appeared during repair');
 atomicWrite(file,JSON.stringify(next,null,2)+'\n',fileMode,!bytes);
}
// Git settings are convenience defaults, not security gates. Create only when absent; never rewrite user config.
try{fs.lstatSync(gitFile);}catch(e){if(e.code!=='ENOENT')throw e;atomicWrite(gitFile,'[safe]\n\tdirectory = /workspace/repos/tunnel\n[core]\n\tautocrlf = true\n',0o600,true);}
const check=JSON.parse(fs.readFileSync(file,'utf8'));
if(!Array.isArray(check.allowedDirectories)||check.allowedDirectories.length!==expected.length||!expected.every(x=>check.allowedDirectories.includes(x)))fail('DC allowedDirectories post-check failed');
console.log('FORTIS_RUNTIME_CONFIG_PASS');
'@
    $uid = [int]($script:FortisPolicy.LinuxUser.Split(':')[0])
    $gid = [int]($script:FortisPolicy.LinuxUser.Split(':')[1])
    $roots = ConvertTo-FortisJsonLiteral -Value @($script:FortisPolicy.AllowedDirectories)
    return $code.Replace('__DIRECT_ENTRY_PATH__', (ConvertTo-FortisJsonLiteral $script:FortisPolicy.DirectEntryPath)).Replace('__LEGACY_BRIDGE_PATH__', (ConvertTo-FortisJsonLiteral $script:FortisPolicy.LegacyBridgePath)).Replace('__HOME_PATH__', (ConvertTo-FortisJsonLiteral $script:FortisPolicy.HomePath)).Replace('__CONFIG_DIRECTORY__', (ConvertTo-FortisJsonLiteral $script:FortisPolicy.ConfigDirectory)).Replace('__CONFIG_PATH__', (ConvertTo-FortisJsonLiteral $script:FortisPolicy.ConfigPath)).Replace('__GIT_CONFIG_PATH__', (ConvertTo-FortisJsonLiteral $script:FortisPolicy.GitConfigPath)).Replace('__ALLOWED_DIRECTORIES__', $roots).Replace('__LINUX_UID__', [string]$uid).Replace('__LINUX_GID__', [string]$gid)
}

function Repair-FortisLinuxRuntimeConfig {
    param($Context, $Snapshot)
    if ($Snapshot.ConfigState -eq 'Pinned') { return $Snapshot }
    if ($Snapshot.ConfigState -notin @('Missing','FactoryDefaults')) {
        throw 'Only a missing or untouched factory-default config may be repaired.'
    }
    $code = Get-FortisRuntimeBootstrapCode
    $raw = Invoke-FortisDockerExec -Context $Context -Command @($script:FortisPolicy.LinuxNodePath, '-e', $code)
    $rawLines = @($raw)
    if ($rawLines.Count -ne 1 -or [string]$rawLines[0] -cne 'FORTIS_RUNTIME_CONFIG_PASS') {
        throw 'Guarded runtime config repair did not return its success marker.'
    }
    $after = Get-FortisLinuxRuntimeSnapshot -Context $Context
    if ($after.ConfigState -ne 'Pinned') { throw 'Runtime config repair did not verify.' }
    return $after
}

function Assert-FortisTunnelRuntime {
    $path = $script:FortisPolicy.WindowsRuntimePath
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw 'Pinned Windows Tunnel Runtime is missing.' }
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -cne $script:FortisPolicy.WindowsRuntimeSha256) {
        throw 'Windows Tunnel Runtime SHA-256 changed; review the shared dependency policy.'
    }
    return $path
}


function Assert-FortisPolicyIntegrity {
    $path = $script:FortisPolicySourcePath
    if ([string]::IsNullOrWhiteSpace($path) -or -not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw 'Shared Fortis policy source path is unavailable.'
    }
    $rawBytes = [IO.File]::ReadAllBytes($path)
    $source = [Text.Encoding]::UTF8.GetString($rawBytes)
    $pattern = "(?m)^([ `t]*PolicySourceSha256[ `t]*=[ `t]*)'[0-9A-F]{64}'([ `t]*)$"
    if ([regex]::Matches($source, $pattern).Count -ne 1) {
        throw 'Shared Fortis policy integrity anchor is missing or duplicated.'
    }
    $normalized = [regex]::Replace($source, $pattern, ('$1' + "'<SELF>'" + '$2'))
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $actual = [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($normalized))).Replace('-', '')
    } finally {
        $sha.Dispose()
    }
    if ($actual -cne $script:FortisPolicy.PolicySourceSha256) {
        throw 'Shared Fortis policy integrity check failed.'
    }
}

Assert-FortisPolicyIntegrity
