# Optional owner action: launch the existing protected Viewer at Windows sign-in.
[CmdletBinding()]
param([switch]$Disable)
$ErrorActionPreference = 'Stop'
$owner = [Security.Principal.WindowsIdentity]::GetCurrent()
if (($owner.Name -split '\\')[-1] -ine 'alexa') { throw 'Only the approved owner can enable autostart.' }
$install = Join-Path $env:LOCALAPPDATA 'FortisObservatoryV1\Viewer'
$target = Join-Path $install 'Start-FortisObservatoryAuto.cmd'
$runKey = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run'
$name = 'FortisObservatoryOwnerViewer'
if ($Disable) {
    Remove-ItemProperty -Path $runKey -Name $name -ErrorAction SilentlyContinue
    Write-Output 'AUTOSTART_DISABLED=True'
    exit 0
}
if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
    throw 'Install updated owner Viewer first.'
}
$dir = Get-Item -LiteralPath $install -Force
$file = Get-Item -LiteralPath $target -Force
if (($dir.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or
    ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'Reparse point refused.'
}
$acl = Get-Acl -LiteralPath $install
if (-not $acl.AreAccessRulesProtected) { throw 'Owner ACL is not protected.' }
$sid = $owner.User.Value
foreach ($entry in @($acl.Access)) {
    if ($entry.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow) {
        $got = $entry.IdentityReference.Translate(
            [Security.Principal.SecurityIdentifier]).Value
        if ($got -ne $sid -and $got -ne 'S-1-5-18') {
            throw 'Unexpected ACL identity; no autorun enabled.'
        }
    }
}
$command = '"' + $target + '"'
New-Item -Path $runKey -Force | Out-Null
New-ItemProperty -Path $runKey -Name $name -PropertyType String -Value $command -Force | Out-Null
$check = (Get-ItemProperty -Path $runKey -Name $name).$name
if ($check -cne $command) { throw 'Registry Run entry verification failed.' }
Write-Output 'AUTOSTART_ENABLED_ON_OWNER_LOGIN=True'
Write-Output 'Docker readiness: wait up to 15 minutes. Viewer bearer remains owner-private.'
