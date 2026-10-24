# Read-only metadata collection. Run manually in normal Windows PowerShell
# as FORTIS_M\alexa. Prints JSON; does not apply settings or run launchers.
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows PowerShell is required.' }
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($identity.Name -ine 'FORTIS_M\alexa') {
    throw 'Run manually from the existing FORTIS_M\alexa account.'
}
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Use a normal, non-elevated PowerShell window.'
}
$repoRoot = 'C:\Users\alexa\chatgpt-repo-mode'
$hashFiles = @(
    "$repoRoot\run-tunnel.ps1", "$repoRoot\control.ps1",
    "$repoRoot\probe.mjs", "$repoRoot\workspace-config.json",
    'C:\Tools\desktop-commander-runtime\node.exe',
    'C:\Tools\tunnel-client\tunnel-client.exe',
    'C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe'
)
$aclOnly = @(
    'C:\Users\alexa', $repoRoot, 'C:\Tools',
    'C:\Tools\desktop-commander-runtime', 'C:\Tools\tunnel-client',
    'C:\Tools\tunnel-client\runtime', 'C:\Tools\tunnel-client\runtime\v0.0.15',
    "$env:APPDATA\tunnel-client", "$env:APPDATA\tunnel-client\runtime.key"
)
$objects = foreach ($targetPath in @($hashFiles + $aclOnly | Select-Object -Unique)) {
    try {
        $acl = Get-Acl -LiteralPath $targetPath -ErrorAction Stop
        $rules = @($acl.Access | ForEach-Object {
            [pscustomobject]@{
                Identity = $_.IdentityReference.Value
                Rights = [string]$_.FileSystemRights
                Type = [string]$_.AccessControlType
                Inherited = $_.IsInherited
                InheritanceFlags = [string]$_.InheritanceFlags
                PropagationFlags = [string]$_.PropagationFlags
            }
        })
        $sha256 = $null
        if ($hashFiles -contains $targetPath) {
            $sha256 = (Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash
        }
        [pscustomobject]@{
            Path = $targetPath; Owner = $acl.Owner
            InheritanceProtected = $acl.AreAccessRulesProtected
            SHA256 = $sha256; Access = $rules
        }
    } catch {
        [pscustomobject]@{
            Path = $targetPath; ErrorType = $_.Exception.GetType().Name
        }
    }
}
$runtimeProcesses = @()
try {
    $candidates = @(Get-CimInstance Win32_Process -Filter "Name='tunnel-client-runtime.exe'")
    $selected = @($candidates | Where-Object {
        $_.CommandLine -match '(?i)--profile(?:=|\s+)"?repo-mode(?:\s|"|$)'
    })
    foreach ($repoProcess in $selected) {
        $ownerSid = $null
        try {
            $ownerSid = (Invoke-CimMethod -InputObject $repoProcess -MethodName GetOwnerSid).Sid
        } catch {}
        $listeners = @()
        $listenerError = $null
        try {
            $listeners = @(Get-NetTCPConnection -State Listen -OwningProcess $repoProcess.ProcessId |
                Select-Object LocalAddress, LocalPort)
        } catch { $listenerError = $_.Exception.GetType().Name }
        $runtimeProcesses += [pscustomobject]@{
            ProcessId = $repoProcess.ProcessId; ParentProcessId = $repoProcess.ParentProcessId
            ExecutablePath = $repoProcess.ExecutablePath; CreationDate = $repoProcess.CreationDate
            OwnerSid = $ownerSid; Listeners = $listeners; ListenerError = $listenerError
        }
    }
} catch {
    $runtimeProcesses = @([pscustomobject]@{ ErrorType = $_.Exception.GetType().Name })
}
$dockerMetadata = $null
$networkMetadata = @()
try {
    $rawInspect = & docker inspect --type container -- fortis-repo-test 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'Docker inspect unavailable.' }
    $containerInfo = @($rawInspect | ConvertFrom-Json)[0]
    $networkNames = @($containerInfo.NetworkSettings.Networks.PSObject.Properties.Name)
    $dockerMetadata = [pscustomobject]@{
        Id = $containerInfo.Id; User = $containerInfo.Config.User
        Privileged = $containerInfo.HostConfig.Privileged
        NetworkMode = $containerInfo.HostConfig.NetworkMode; PidMode = $containerInfo.HostConfig.PidMode
        IpcMode = $containerInfo.HostConfig.IpcMode; UsernsMode = $containerInfo.HostConfig.UsernsMode
        CgroupnsMode = $containerInfo.HostConfig.CgroupnsMode
        ReadonlyRootfs = $containerInfo.HostConfig.ReadonlyRootfs
        CapDrop = $containerInfo.HostConfig.CapDrop; SecurityOpt = $containerInfo.HostConfig.SecurityOpt
        Memory = $containerInfo.HostConfig.Memory; NanoCpus = $containerInfo.HostConfig.NanoCpus
        PidsLimit = $containerInfo.HostConfig.PidsLimit
        PortBindings = $containerInfo.HostConfig.PortBindings
        Mounts = @($containerInfo.Mounts | Select-Object Type, Name, Source, Destination, RW)
        NetworkNames = $networkNames
    }
    foreach ($networkName in $networkNames) {
        try {
            $rawNetwork = & docker network inspect -- $networkName 2>$null
            if ($LASTEXITCODE -ne 0) { throw 'Network inspect unavailable.' }
            $networkInfo = @($rawNetwork | ConvertFrom-Json)[0]
            $networkMetadata += [pscustomobject]@{
                Name = $networkInfo.Name; Driver = $networkInfo.Driver
                Internal = $networkInfo.Internal; EnableIPv6 = $networkInfo.EnableIPv6
                EnableICC = $networkInfo.Options.'com.docker.network.bridge.enable_icc'
                IPMasquerade = $networkInfo.Options.'com.docker.network.bridge.enable_ip_masquerade'
            }
        } catch {
            $networkMetadata += [pscustomobject]@{
                Name = $networkName; ErrorType = $_.Exception.GetType().Name
            }
        }
    }
} catch {
    $dockerMetadata = [pscustomobject]@{ ErrorType = $_.Exception.GetType().Name }
}
[pscustomobject]@{
    CollectedAtUtc = [DateTime]::UtcNow.ToString('o')
    Identity = $identity.Name
    FilesAndACLs = @($objects)
    RepoRuntimeProcesses = $runtimeProcesses
    Docker = $dockerMetadata; Networks = $networkMetadata
    Limitations = @(
        'No credential contents or key hashes are collected.',
        'No raw profile, environment, process command line or payload is emitted.',
        'A zero process count is not proof that Repo is stopped: profile matching may be unavailable.',
        'Firewall policy, unknown host endpoints and vulnerabilities are not audited by this script.'
    )
} | ConvertTo-Json -Depth 10
