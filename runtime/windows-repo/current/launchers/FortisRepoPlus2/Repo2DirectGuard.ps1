param(
    [ValidateSet('Preview','Run')][string]$Mode = 'Preview',
    [string]$ContainerId
)
# Repo2-specific entrypoint. Shared Windows/Docker/Linux policy lives in launchers/shared.
# Preview is read-only; Run repairs only a recognized missing/factory-default tmpfs config.
$ErrorActionPreference = 'Stop'
$policyPath = Join-Path $PSScriptRoot '..\\shared\\FortisContainerPolicy.ps1'
if (-not (Test-Path -LiteralPath $policyPath -PathType Leaf)) { throw 'Shared Fortis policy is missing.' }
. $policyPath
$identity = Assert-FortisWindowsOwner
$context = Get-FortisContainerContext -ContainerId $ContainerId
$runtime = Get-FortisLinuxRuntimeSnapshot -Context $context

if ($Mode -eq 'Preview') {
    [pscustomobject]@{
        Mode = 'Preview'
        Preflight = $(if ($runtime.ConfigState -eq 'Pinned') { 'PASS' } else { 'REBOOT_REPAIR_REQUIRED' })
        ConfigState = $runtime.ConfigState
        ContainerId = $context.ContainerId
        ContainerIdMatched = $true
        LinuxUid = $runtime.Probe.uid
        LinuxSecurityVerified = $runtime.LinuxSecurityVerified
        DirectEntryAvailable = $runtime.DirectEntryAvailable
        ImageId = $context.Info.Image
        NoWindowsProfileEdits = $true
    } | ConvertTo-Json -Depth 3
    return
}

$runtime = Repair-FortisLinuxRuntimeConfig -Context $context -Snapshot $runtime
if ($runtime.ConfigState -ne 'Pinned') { throw 'Repo2 shared runtime policy did not reach the pinned state.' }
Write-Output ('REPO2_DIRECT_GUARD_PASS:' + $context.ContainerId)
