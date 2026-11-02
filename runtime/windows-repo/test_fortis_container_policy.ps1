# Pure offline policy tests. No Windows identity, Docker daemon, MCP or Tunnel is invoked.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'current/launchers/shared/FortisContainerPolicy.ps1')

function New-Map($Pairs) {
    $map = New-Object PSObject
    foreach ($pair in $Pairs.GetEnumerator()) {
        $map | Add-Member -MemberType NoteProperty -Name $pair.Key -Value $pair.Value
    }
    return $map
}

function New-Info {
    $requested = @(
        [pscustomobject]@{ Type='volume'; Source='fortis-repo-workspace'; Target='/workspace/repo'; ReadOnly=$false; VolumeOptions=[pscustomobject]@{Subpath=''} }
        [pscustomobject]@{ Type='volume'; Source='fortis-repo-workspace'; Target='/workspace/repos'; ReadOnly=$false; VolumeOptions=[pscustomobject]@{Subpath='Repos'} }
        [pscustomobject]@{ Type='volume'; Source='fortis-repo-workspace'; Target='/workspace/files'; ReadOnly=$false; VolumeOptions=[pscustomobject]@{Subpath='Workfiles'} }
    )
    $effective = @(
        [pscustomobject]@{ Type='volume'; Name='fortis-repo-workspace'; Destination='/workspace/repo'; RW=$true }
        [pscustomobject]@{ Type='volume'; Name='fortis-repo-workspace'; Destination='/workspace/repos'; RW=$true }
        [pscustomobject]@{ Type='volume'; Name='fortis-repo-workspace'; Destination='/workspace/files'; RW=$true }
    )
    $tmpfs = New-Map ([ordered]@{ '/tmp'='rw,nosuid,nodev'; '/home/node'='rw,nosuid,nodev' })
    $networks = New-Map ([ordered]@{ 'fortis-repo-egress'=[pscustomobject]@{IPAddress='172.20.0.2'} })
    return [pscustomobject]@{
        Name='/fortis-repo-test'; Id=('a' * 64); Image=('sha256:' + ('b' * 64))
        Config=[pscustomobject]@{ User='1000:1000'; Env=@() }
        HostConfig=[pscustomobject]@{
            Privileged=$false; ReadonlyRootfs=$true; CapDrop=@('ALL'); CapAdd=@()
            SecurityOpt=@('no-new-privileges'); Memory=4294967296L; NanoCpus=2000000000L; PidsLimit=256
            Tmpfs=$tmpfs; PortBindings=$null; PublishAllPorts=$false; Binds=$null
            NetworkMode='fortis-repo-egress'; Mounts=$requested
            PidMode=''; IpcMode=''; UTSMode=''; UsernsMode=''; CgroupnsMode='private'
            Devices=$null; DeviceRequests=$null; VolumesFrom=$null; GroupAdd=$null
        }
        Mounts=$effective
        NetworkSettings=[pscustomobject]@{ Networks=$networks }
        State=[pscustomobject]@{ Running=$true }
    }
}

function Check-Case([string]$Name, $Info, [bool]$ExpectedPass) {
    $passed = $false
    try { Assert-FortisContainerPolicy -Info $Info -DockerPath '/bin/true'; $passed = $true }
    catch { if ($ExpectedPass) { throw "FALSE_REJECT $Name : $($_.Exception.Message)" } }
    if ($passed -ne $ExpectedPass) { throw "WRONG_POLICY_RESULT $Name : $passed" }
    Write-Output "POLICY_PASS=$Name"
}

$count = 0
$i = New-Info; Check-Case 'baseline' $i $true; $count++
$i = New-Info; $i.Image='sha256:' + ('c' * 64); Check-Case 'image-rebuild-does-not-break-policy' $i $true; $count++
$i = New-Info; $i.HostConfig.Memory=1073741824L; $i.HostConfig.NanoCpus=1000000000L; $i.HostConfig.PidsLimit=128; Check-Case 'stricter-resource-limits' $i $true; $count++
$i = New-Info; $i.HostConfig.NetworkMode=''; Check-Case 'network-membership-independent-of-default-mode' $i $true; $count++
$i = New-Info; $i.HostConfig.Tmpfs | Add-Member -MemberType NoteProperty -Name '/tmp/cache' -Value 'rw,nosuid,nodev'; Check-Case 'additional-safe-tmpfs' $i $true; $count++

$i = New-Info
$i.HostConfig.Mounts += [pscustomobject]@{ Type='volume'; Source='fortis-r7-client'; Target='/run/fortis-client'; ReadOnly=$true; VolumeOptions=[pscustomobject]@{Subpath=''} }
$i.Mounts += [pscustomobject]@{ Type='volume'; Name='fortis-r7-client'; Destination='/run/fortis-client'; RW=$false }
Check-Case 'optional-client-ro' $i $true; $count++

$mutations = @(
    @{Name='wrong-user'; Change={param($x)$x.Config.User='0:0'}},
    @{Name='privileged'; Change={param($x)$x.HostConfig.Privileged=$true}},
    @{Name='writable-rootfs'; Change={param($x)$x.HostConfig.ReadonlyRootfs=$false}},
    @{Name='missing-cap-drop'; Change={param($x)$x.HostConfig.CapDrop=@()}},
    @{Name='added-capability'; Change={param($x)$x.HostConfig.CapAdd=@('NET_ADMIN')}},
    @{Name='missing-nnp'; Change={param($x)$x.HostConfig.SecurityOpt=@()}},
    @{Name='unconfined-seccomp'; Change={param($x)$x.HostConfig.SecurityOpt=@('no-new-privileges','seccomp=unconfined')}},
    @{Name='host-network-mode'; Change={param($x)$x.HostConfig.NetworkMode='host'}},
    @{Name='container-network-sharing'; Change={param($x)$x.HostConfig.NetworkMode='container:deadbeef'}},
    @{Name='unsafe-extra-tmpfs'; Change={param($x)$x.HostConfig.Tmpfs | Add-Member -MemberType NoteProperty -Name '/opt/dc' -Value 'rw'}},
    @{Name='tmpfs-path-traversal'; Change={param($x)$x.HostConfig.Tmpfs | Add-Member -MemberType NoteProperty -Name '/tmp/../opt/dc' -Value 'rw'}},
    @{Name='host-pid-namespace'; Change={param($x)$x.HostConfig.PidMode='host'}},
    @{Name='host-ipc-namespace'; Change={param($x)$x.HostConfig.IpcMode='host'}},
    @{Name='host-uts-namespace'; Change={param($x)$x.HostConfig.UTSMode='host'}},
    @{Name='host-user-namespace'; Change={param($x)$x.HostConfig.UsernsMode='host'}},
    @{Name='device-access'; Change={param($x)$x.HostConfig.Devices=@([pscustomobject]@{PathOnHost='/dev/kvm'})}},
    @{Name='device-request'; Change={param($x)$x.HostConfig.DeviceRequests=@([pscustomobject]@{Capabilities=@(@('gpu'))})}},
    @{Name='supplementary-group'; Change={param($x)$x.HostConfig.GroupAdd=@('0')}},
    @{Name='unlimited-memory'; Change={param($x)$x.HostConfig.Memory=0}},
    @{Name='memory-ceiling'; Change={param($x)$x.HostConfig.Memory=8589934593L}},
    @{Name='cpu-ceiling'; Change={param($x)$x.HostConfig.NanoCpus=2000000001L}},
    @{Name='pid-ceiling'; Change={param($x)$x.HostConfig.PidsLimit=1025}},
    @{Name='missing-tmpfs'; Change={param($x)$x.HostConfig.Tmpfs=New-Map ([ordered]@{ '/tmp'='rw' })}},
    @{Name='published-port'; Change={param($x)$x.HostConfig.PortBindings=[pscustomobject]@{ '3000/tcp'=@([pscustomobject]@{HostPort='3000'}) }}},
    @{Name='publish-all'; Change={param($x)$x.HostConfig.PublishAllPorts=$true}},
    @{Name='host-bind'; Change={param($x)$x.HostConfig.Binds=@('/var/run/docker.sock:/var/run/docker.sock')}},
    @{Name='unknown-network'; Change={param($x)$x.NetworkSettings.Networks | Add-Member -MemberType NoteProperty -Name 'host' -Value ([pscustomobject]@{})}},
    @{Name='nonempty-node-options'; Change={param($x)$x.Config.Env=@('NODE_OPTIONS=--require=/tmp/hook.js')}},
    @{Name='wrong-workspace-volume'; Change={param($x)$x.Mounts[0].Name='other-volume'}},
    @{Name='wrong-subpath'; Change={param($x)$x.HostConfig.Mounts[1].VolumeOptions.Subpath='Other'}},
    @{Name='workspace-readonly'; Change={param($x)$x.HostConfig.Mounts[0].ReadOnly=$true}},
    @{Name='workspace-not-rw'; Change={param($x)$x.Mounts[0].RW=$false}},
    @{Name='extra-docker-socket'; Change={param($x)$x.HostConfig.Mounts += [pscustomobject]@{Type='bind';Source='/var/run/docker.sock';Target='/var/run/docker.sock';ReadOnly=$false};$x.Mounts += [pscustomobject]@{Type='bind';Name='';Destination='/var/run/docker.sock';RW=$true}}},
    @{Name='client-requested-rw'; Change={param($x)$x.HostConfig.Mounts += [pscustomobject]@{Type='volume';Source='fortis-r7-client';Target='/run/fortis-client';ReadOnly=$false;VolumeOptions=[pscustomobject]@{Subpath=''}};$x.Mounts += [pscustomobject]@{Type='volume';Name='fortis-r7-client';Destination='/run/fortis-client';RW=$true}}},
    @{Name='client-effective-rw'; Change={param($x)$x.HostConfig.Mounts += [pscustomobject]@{Type='volume';Source='fortis-r7-client';Target='/run/fortis-client';ReadOnly=$true;VolumeOptions=[pscustomobject]@{Subpath=''}};$x.Mounts += [pscustomobject]@{Type='volume';Name='fortis-r7-client';Destination='/run/fortis-client';RW=$true}}},
    @{Name='client-wrong-source'; Change={param($x)$x.HostConfig.Mounts += [pscustomobject]@{Type='volume';Source='evil';Target='/run/fortis-client';ReadOnly=$true;VolumeOptions=[pscustomobject]@{Subpath=''}};$x.Mounts += [pscustomobject]@{Type='volume';Name='evil';Destination='/run/fortis-client';RW=$false}}}
)
foreach ($mutation in $mutations) {
    $i=New-Info
    & $mutation.Change $i
    Check-Case $mutation.Name $i $false
    $count++
}
Write-Output "GO3C_SHARED_POLICY_CASES_PASS=$count"

# Verify Docker exec always places the inspected immutable ID after options.
$execContext = [pscustomobject]@{ DockerPath='/bin/echo'; ContainerId=('d' * 64) }
$execOutput = Invoke-FortisDockerExec -Context $execContext -Options @('--user','1000:1000') -Command @('node','-e','42')
$execExpected = 'exec --user 1000:1000 ' + $execContext.ContainerId + ' node -e 42'
if (@($execOutput).Count -ne 1 -or [string](@($execOutput)[0]) -cne $execExpected) {
    throw 'DOCKER_EXEC_ID_BINDING_FAIL'
}
Write-Output 'DOCKER_EXEC_ID_BINDING_PASS'

# Stub only the Docker exec boundary to test runtime-state classification and repair gating.
$script:MockProbeJson = $null
function Invoke-FortisDockerExec {
    param($Context, [string[]]$Command, [string[]]$Options = @())
    if ($Command[-1] -like '*FORTIS_RUNTIME_CONFIG_PASS*') {
        $script:MockProbeJson = '{"uid":1000,"euid":1000,"gid":1000,"egid":1000,"homeSafe":true,"configDirectorySafe":true,"configFileSafe":true,"capEff":"00000000","capBnd":"00000000","noNewPrivs":"1","seccomp":"2","rootReadOnly":true,"directEntryAvailable":true,"configMissing":false,"allowedDirectories":["/workspace/repos","/workspace/files","/workspace/repo"]}'
        return @('FORTIS_RUNTIME_CONFIG_PASS')
    }
    return @($script:MockProbeJson)
}
$runtimeContext = [pscustomobject]@{ DockerPath='/bin/echo'; ContainerId=('e' * 64) }
$script:MockProbeJson = '{"uid":1000,"euid":1000,"gid":1000,"egid":1000,"homeSafe":true,"configDirectorySafe":true,"configFileSafe":true,"capEff":"00000000","capBnd":"00000000","noNewPrivs":"1","seccomp":"2","rootReadOnly":true,"directEntryAvailable":true,"configMissing":false,"allowedDirectories":["/workspace/repos","/workspace/files","/workspace/repo"]}'
$runtimeSnapshot = Get-FortisLinuxRuntimeSnapshot -Context $runtimeContext
if ($runtimeSnapshot.ConfigState -ne 'Pinned') { throw 'RUNTIME_CONFIG_PINNED_CLASSIFICATION_FAIL' }
$goodProbe = $script:MockProbeJson
$runtimeFailures = @(
    @{Name='euid'; Replace='"euid":1000'; With='"euid":0'},
    @{Name='egid'; Replace='"egid":1000'; With='"egid":0'},
    @{Name='home-mode'; Replace='"homeSafe":true'; With='"homeSafe":false'},
    @{Name='config-dir-mode'; Replace='"configDirectorySafe":true'; With='"configDirectorySafe":false'},
    @{Name='config-file-mode'; Replace='"configFileSafe":true'; With='"configFileSafe":false'}
)
foreach ($failure in $runtimeFailures) {
    $script:MockProbeJson = $goodProbe.Replace($failure.Replace,$failure.With)
    $rejected = $false
    try { $null = Get-FortisLinuxRuntimeSnapshot -Context $runtimeContext } catch { $rejected = $true }
    if (-not $rejected) { throw "RUNTIME_SECURITY_REJECT_FAIL=$($failure.Name)" }
}
$script:MockProbeJson = $goodProbe
Write-Output 'RUNTIME_IDENTITY_AND_METADATA_NEGATIVES_PASS'
$script:MockProbeJson = '{"uid":1000,"euid":1000,"gid":1000,"egid":1000,"homeSafe":true,"configDirectorySafe":true,"configFileSafe":true,"capEff":"00000000","capBnd":"00000000","noNewPrivs":"1","seccomp":"2","rootReadOnly":true,"directEntryAvailable":true,"configMissing":false,"allowedDirectories":[]}'
$runtimeSnapshot = Get-FortisLinuxRuntimeSnapshot -Context $runtimeContext
if ($runtimeSnapshot.ConfigState -ne 'FactoryDefaults') { throw 'RUNTIME_CONFIG_FACTORY_CLASSIFICATION_FAIL' }
$runtimeSnapshot = Repair-FortisLinuxRuntimeConfig -Context $runtimeContext -Snapshot $runtimeSnapshot
if ($runtimeSnapshot.ConfigState -ne 'Pinned') { throw 'RUNTIME_CONFIG_FACTORY_REPAIR_FAIL' }
$script:MockProbeJson = '{"uid":1000,"euid":1000,"gid":1000,"egid":1000,"homeSafe":true,"configDirectorySafe":true,"configFileSafe":true,"capEff":"00000000","capBnd":"00000000","noNewPrivs":"1","seccomp":"2","rootReadOnly":true,"directEntryAvailable":true,"configMissing":true,"allowedDirectories":null}'
$runtimeSnapshot = Get-FortisLinuxRuntimeSnapshot -Context $runtimeContext
if ($runtimeSnapshot.ConfigState -ne 'Missing') { throw 'RUNTIME_CONFIG_MISSING_CLASSIFICATION_FAIL' }
$runtimeSnapshot = Repair-FortisLinuxRuntimeConfig -Context $runtimeContext -Snapshot $runtimeSnapshot
if ($runtimeSnapshot.ConfigState -ne 'Pinned') { throw 'RUNTIME_CONFIG_REPAIR_PASS_FAIL' }
$script:MockProbeJson = '{"uid":1000,"euid":1000,"gid":1000,"egid":1000,"homeSafe":true,"configDirectorySafe":true,"configFileSafe":true,"capEff":"00000000","capBnd":"00000000","noNewPrivs":"1","seccomp":"2","rootReadOnly":true,"directEntryAvailable":true,"configMissing":false,"allowedDirectories":["/workspace/evil"]}'
$unknownRejected = $false
try { $null = Get-FortisLinuxRuntimeSnapshot -Context $runtimeContext } catch { $unknownRejected = $true }
if (-not $unknownRejected) { throw 'RUNTIME_CONFIG_UNKNOWN_DRIFT_REJECT_FAIL' }
Write-Output 'RUNTIME_CONFIG_STATE_REPAIR_AND_DRIFT_PASS'
