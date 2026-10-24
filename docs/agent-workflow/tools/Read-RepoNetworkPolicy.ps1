# Read-only network policy metadata. Run manually as FORTIS_M\alexa.
# Prints selected JSON only. Does not change firewall, Docker or WSL settings.
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows PowerShell is required.' }
$fortisIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($fortisIdentity.Name -ine 'FORTIS_M\alexa') {
    throw 'Run manually from the existing FORTIS_M\alexa account.'
}
$fortisPrincipal = New-Object Security.Principal.WindowsPrincipal($fortisIdentity)
function Read-Metadata {
    param([scriptblock]$Query)
    try { & $Query } catch {
        [pscustomobject]@{ ErrorType = $_.Exception.GetType().Name; HResult = $_.Exception.HResult }
    }
}
function Read-ScalarValue {
    param($Value)
    if ($null -eq $Value) { return $null }
    if ($Value.PSObject.Properties['value']) { $Value = $Value.value }
    if ($null -eq $Value) { return $null }
    if ($Value -is [string] -or $Value -is [bool] -or $Value -is [ValueType]) { return $Value }
    return '[non-scalar]'
}
$profiles = @(Read-Metadata {
    Get-NetFirewallProfile -PolicyStore ActiveStore | ForEach-Object {
        [pscustomobject]@{
            Name = [string]$_.Name; Enabled = [string]$_.Enabled
            DefaultInboundAction = [string]$_.DefaultInboundAction
            DefaultOutboundAction = [string]$_.DefaultOutboundAction
            AllowInboundRules = [string]$_.AllowInboundRules
            AllowLocalFirewallRules = [string]$_.AllowLocalFirewallRules
            AllowLocalIPsecRules = [string]$_.AllowLocalIPsecRules
        }
    }
})
$connections = @(Read-Metadata {
    Get-NetConnectionProfile | ForEach-Object {
        [pscustomobject]@{
            InterfaceIndex = $_.InterfaceIndex; NetworkCategory = [string]$_.NetworkCategory
            IPv4Connectivity = [string]$_.IPv4Connectivity; IPv6Connectivity = [string]$_.IPv6Connectivity
        }
    }
})
$addresses = @(Read-Metadata {
    Get-NetIPAddress -AddressState Preferred |
        Select-Object InterfaceIndex, AddressFamily, IPAddress, PrefixLength
})
$backendProcesses = @(Read-Metadata {
    Get-CimInstance Win32_Process -Filter "Name='com.docker.backend.exe' OR Name='com.docker.service' OR Name='com.docker.service.exe' OR Name='Docker Desktop.exe'" |
        Select-Object ProcessId, ExecutablePath
})
$desktopSettings = @()
foreach ($settingsPath in @("$env:APPDATA\Docker\settings-store.json", "$env:APPDATA\Docker\settings.json")) {
    if (-not (Test-Path -LiteralPath $settingsPath -PathType Leaf)) { continue }
    $desktopSettings += Read-Metadata {
        $settingsObject = Get-Content -LiteralPath $settingsPath -Raw | ConvertFrom-Json
        $selectedSettings = [ordered]@{ Source = $settingsPath }
        foreach ($settingName in @('wslEngineEnabled','networkType','defaultNetworkingMode','dnsInhibition','enableHostNetworking','exposeDockerAPIOnTCP2375')) {
            $selectedSettings[$settingName] = Read-ScalarValue $settingsObject.$settingName
        }
        [pscustomobject]$selectedSettings
    }
}
$managedNetwork = Read-Metadata {
    $adminPath = 'C:\ProgramData\DockerDesktop\admin-settings.json'
    if (-not (Test-Path -LiteralPath $adminPath -PathType Leaf)) {
        [pscustomobject]@{ Present = $false }
    } else {
        $managedObject = Get-Content -LiteralPath $adminPath -Raw | ConvertFrom-Json
        $proxyObject = $managedObject.containersProxy
        [pscustomobject]@{
            Present = $true
            ContainersProxyPresent = ($null -ne $proxyObject)
            Mode = Read-ScalarValue $proxyObject.mode
            Locked = Read-ScalarValue $proxyObject.locked
            TransparentPorts = Read-ScalarValue $proxyObject.transparentPorts
            PACConfigured = -not [string]::IsNullOrWhiteSpace([string](Read-ScalarValue $proxyObject.pac))
            HTTPProxyConfigured = -not [string]::IsNullOrWhiteSpace([string](Read-ScalarValue $proxyObject.http))
            HTTPSProxyConfigured = -not [string]::IsNullOrWhiteSpace([string](Read-ScalarValue $proxyObject.https))
            ExclusionCount = @($proxyObject.exclude).Count
        }
    }
}
$docker = Read-Metadata {
    $infoRaw = & docker info --format '{{json .}}' 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'Docker info unavailable.' }
    $info = $infoRaw | ConvertFrom-Json
    $inspectRaw = & docker inspect --type container -- fortis-repo-test 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'Container inspect unavailable.' }
    $containerInfo = @($inspectRaw | ConvertFrom-Json)[0]
    $networkRaw = & docker network inspect -- fortis-repo-egress 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'Network inspect unavailable.' }
    $networkInfo = @($networkRaw | ConvertFrom-Json)[0]
    $networkOptions = [ordered]@{}
    foreach ($optionName in @('com.docker.network.bridge.enable_icc','com.docker.network.bridge.enable_ip_masquerade','com.docker.network.bridge.gateway_mode_ipv4','com.docker.network.bridge.gateway_mode_ipv6','com.docker.network.bridge.host_binding_ipv4')) {
        $networkOptions[$optionName] = Read-ScalarValue $networkInfo.Options.$optionName
    }
    [pscustomobject]@{
        ServerVersion = $info.ServerVersion; KernelVersion = $info.KernelVersion
        OperatingSystem = $info.OperatingSystem; OSType = $info.OSType
        FirewallBackend = Read-ScalarValue $info.FirewallBackend
        SecurityOptions = $info.SecurityOptions
        HTTPProxyConfigured = -not [string]::IsNullOrWhiteSpace([string]$info.HTTPProxy)
        HTTPSProxyConfigured = -not [string]::IsNullOrWhiteSpace([string]$info.HTTPSProxy)
        ContainerId = $containerInfo.Id; ImageId = $containerInfo.Image
        NetworkMode = $containerInfo.HostConfig.NetworkMode
        ContainerNetwork = @($containerInfo.NetworkSettings.Networks.PSObject.Properties | ForEach-Object {
            [pscustomobject]@{
                Name = $_.Name; IPAddress = $_.Value.IPAddress
                IPPrefixLen = $_.Value.IPPrefixLen; Gateway = $_.Value.Gateway
                GlobalIPv6Address = $_.Value.GlobalIPv6Address
                IPv6Gateway = $_.Value.IPv6Gateway
            }
        })
        Driver = $networkInfo.Driver; Internal = $networkInfo.Internal
        EnableIPv6 = $networkInfo.EnableIPv6; NetworkOptions = $networkOptions
        IPAM = @($networkInfo.IPAM.Config | Select-Object Subnet, Gateway)
        AttachedContainerCount = @($networkInfo.Containers.PSObject.Properties).Count
    }
}
$firewallRules = @(Read-Metadata {
    $includeGenericAllows = @($profiles | Where-Object { [string]$_.DefaultOutboundAction -eq 'Block' }).Count -gt 0
    $profileQueryFailed = @($profiles | Where-Object { $_.PSObject.Properties['ErrorType'] }).Count -gt 0
    if ($profileQueryFailed -or $profiles.Count -eq 0) { $includeGenericAllows = $true }
    $applicationFilters = @(Get-NetFirewallApplicationFilter -PolicyStore ActiveStore)
    foreach ($applicationFilter in $applicationFilters) {
        $program = [string]$applicationFilter.Program
        $generic = ($program -in @('Any','*','System'))
        $related = $program -match '(?i)(^|\\)(com\.docker\.backend\.exe|com\.docker\.service(?:\.exe)?|Docker Desktop\.exe|docker\.exe|wslhost\.exe|wslservice\.exe|vmcompute\.exe|tunnel-client-runtime\.exe|tunnel-client\.exe)$'
        if (-not ($generic -or $related)) { continue }
        $associatedRules = @(Get-NetFirewallRule -AssociatedNetFirewallApplicationFilter $applicationFilter -PolicyStore ActiveStore |
            Where-Object { [string]$_.Enabled -eq 'True' })
        foreach ($rule in $associatedRules) {
            if ($generic -and -not $related -and [string]$rule.Action -ne 'Block' -and -not $includeGenericAllows) { continue }
            $portFilter = @($rule | Get-NetFirewallPortFilter)
            $addressFilter = @($rule | Get-NetFirewallAddressFilter)
            $serviceFilter = @($rule | Get-NetFirewallServiceFilter)
            $interfaceFilter = @($rule | Get-NetFirewallInterfaceTypeFilter)
            $securityFilter = @($rule | Get-NetFirewallSecurityFilter)
            [pscustomobject]@{
                Name = $rule.Name; Direction = [string]$rule.Direction
                Action = [string]$rule.Action; Profile = [string]$rule.Profile
                PolicyStoreSourceType = [string]$rule.PolicyStoreSourceType
                OverrideBlockRules = $rule.OverrideBlockRules
                Program = $program; Scope = $(if ($related) { 'Docker-WSL-Tunnel application' } else { 'Any-System rule' })
                Ports = @($portFilter | Select-Object Protocol, LocalPort, RemotePort)
                Addresses = @($addressFilter | Select-Object LocalAddress, RemoteAddress)
                Services = @($serviceFilter | Select-Object Service)
                InterfaceTypes = @($interfaceFilter | Select-Object InterfaceType)
                Interfaces = @($rule | Get-NetFirewallInterfaceFilter | Select-Object InterfaceAlias)
                Security = @($securityFilter | ForEach-Object {
                    [pscustomobject]@{
                        Authentication = [string]$_.Authentication; Encryption = [string]$_.Encryption
                        OverrideBlockRules = $_.OverrideBlockRules
                        HasLocalUserConstraint = ([string]$_.LocalUser -notin @('','Any'))
                        HasRemoteUserConstraint = ([string]$_.RemoteUser -notin @('','Any'))
                        HasRemoteMachineConstraint = ([string]$_.RemoteMachine -notin @('','Any'))
                    }
                })
            }
        }
    }
})
$hyperV = Read-Metadata {
    $wslCreator = '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}'
    $settings = @(Read-Metadata {
        Get-NetFirewallHyperVVMSetting -PolicyStore ActiveStore -Name $wslCreator | ForEach-Object {
            [pscustomobject]@{
                Name = $_.Name; Enabled = [string]$_.Enabled
                DefaultInboundAction = [string]$_.DefaultInboundAction
                DefaultOutboundAction = [string]$_.DefaultOutboundAction
                LoopbackEnabled = [string]$_.LoopbackEnabled; AllowHostPolicyMerge = [string]$_.AllowHostPolicyMerge
            }
        }
    })
    $hyperVProfiles = @(Read-Metadata {
        Get-NetFirewallHyperVProfile -PolicyStore ActiveStore | ForEach-Object {
            [pscustomobject]@{
                Name = $_.Name; Enabled = [string]$_.Enabled
                DefaultInboundAction = [string]$_.DefaultInboundAction
                DefaultOutboundAction = [string]$_.DefaultOutboundAction
                AllowLocalFirewallRules = [string]$_.AllowLocalFirewallRules
            }
        }
    })
    $rules = @(Read-Metadata {
        $ruleCommand = Get-Command Get-NetFirewallHyperVRule -ErrorAction Stop
        $ruleParameters = @{ VMCreatorId = $wslCreator }
        if ($ruleCommand.Parameters.ContainsKey('PolicyStore')) { $ruleParameters['PolicyStore'] = 'ActiveStore' }
        Get-NetFirewallHyperVRule @ruleParameters | ForEach-Object {
            [pscustomobject]@{
                Name = $_.Name; Enabled = [string]$_.Enabled; Direction = [string]$_.Direction
                Action = [string]$_.Action; Protocol = [string]$_.Protocol
                LocalAddresses = $_.LocalAddresses; RemoteAddresses = $_.RemoteAddresses
                LocalPorts = $_.LocalPorts; RemotePorts = $_.RemotePorts; Profiles = [string]$_.Profiles
                QueriedPolicyStore = $(if ($ruleParameters.ContainsKey('PolicyStore')) { 'ActiveStore' } else { 'Cmdlet default; not assumed ActiveStore' })
            }
        }
    })
    [pscustomobject]@{ VMCreatorId = $wslCreator; Settings = $settings; Profiles = $hyperVProfiles; Rules = $rules }
}
[pscustomobject]@{
    Schema = 'fortis-repo-network-policy-v1'
    CollectedAtUtc = [DateTime]::UtcNow.ToString('o')
    Identity = $fortisIdentity.Name
    IsElevated = $fortisPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    WindowsVersion = [Environment]::OSVersion.Version.ToString()
    FirewallProfiles = $profiles; Connections = $connections; LocalAddresses = $addresses
    DockerBackendProcesses = $backendProcesses; DockerDesktopSettings = $desktopSettings
    ManagedNetworkSettings = $managedNetwork; Docker = $docker
    FirewallRules = $firewallRules; HyperV = $hyperV
    CollectionScope = @(
        'Active Windows profiles; enabled rules for Docker, WSL and Tunnel executables.',
        'Any/System block rules; generic allows only when outbound defaults block or the profile query failed.',
        'WSL Hyper-V firewall metadata; this does not prove which backend carries each Docker flow.',
        'No rule changes, service actions, packet capture, network scan, key/connection-profile/env/log contents.',
        'No proxy URLs, PAC contents, rule descriptions, process command lines or other-container names.',
        'No raw Linux VM nftables/iptables table is collected. Missing fields/errors remain unknown.'
    )
} | ConvertTo-Json -Depth 14
