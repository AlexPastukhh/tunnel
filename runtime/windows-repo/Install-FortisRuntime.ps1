# Owner-run side-by-side install only. Does not start workers or change profiles.
[CmdletBinding()]
param([switch]$Apply, [string]$ArchivePath)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$policyPath = Join-Path $PSScriptRoot 'current\launchers\shared\FortisContainerPolicy.ps1'
. $policyPath
$identity = Assert-FortisWindowsOwner

function Assert-FortisInstallAclRules {
    param([string]$Path, [string]$OwnerSid, [object[]]$Rules, [bool]$Canonical,
          [switch]$RequireDescendantDeny)
    $trusted = @($script:FortisPolicy.OwnerSid, 'S-1-5-18', 'S-1-5-32-544')
    if ($trusted -cnotcontains $OwnerSid) { throw "Install path owner is not trusted: $Path" }
    if (-not $Canonical -or $null -eq $Rules -or $Rules.Count -eq 0) {
        throw "Install path requires a nonempty canonical DACL: $Path"
    }
    # Existing approved boundary: G3_RUNTIME_ACL_PROPOSAL_2026-10-13.md.
    # AU Modify remains allowed only behind the named guest's complete DENY.
    # This is not a general AccessCheck or isolation from every Windows account.
    $guestSid = 'S-1-5-21-303538662-3368424508-2654684973-1009'
    $writeMask = [int][Security.AccessControl.FileSystemRights]'Write, Delete, DeleteSubdirectoriesAndFiles, ChangePermissions, TakeOwnership'
    $knownRights = [int][Security.AccessControl.FileSystemRights]::FullControl
    $modify = [int][Security.AccessControl.FileSystemRights]::Modify
    $both = [int][Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit'
    $inheritOnly = [int][Security.AccessControl.PropagationFlags]::InheritOnly
    $noPropagate = [int][Security.AccessControl.PropagationFlags]::NoPropagateInherit
    $selfDenied = 0; $descendantsDenied = 0
    foreach ($rule in $Rules) {
        $sid = [string]$rule.Sid; $rights = [int]$rule.Rights
        $inherit = [int]$rule.Inheritance; $propagate = [int]$rule.Propagation
        if ($rights -lt 0 -or ($rights -band (-bnot $knownRights)) -ne 0 -or
            $inherit -lt 0 -or $inherit -gt 3 -or $propagate -lt 0 -or $propagate -gt 3 -or
            ($inherit -eq 0 -and $propagate -ne 0) -or @('Allow','Deny') -cnotcontains $rule.Type) {
            throw "Unsupported install ACL entry: path=$Path; sid=$sid"
        }
        $onlyChildren = ($propagate -band $inheritOnly) -ne 0
        if ($rule.Type -ceq 'Deny' -and $sid -ceq $guestSid) {
            if (-not $onlyChildren) { $selfDenied = $selfDenied -bor ($rights -band $writeMask) }
            if (($inherit -band $both) -eq $both -and ($propagate -band $noPropagate) -eq 0) {
                $descendantsDenied = $descendantsDenied -bor ($rights -band $writeMask)
            }
        }
        if ($rule.Type -cne 'Allow' -or ($rights -band $writeMask) -eq 0 -or $trusted -ccontains $sid) { continue }
        # CREATOR OWNER is a child-owner template, never an effective current grant.
        # Each created directory/file is independently checked for trusted ownership.
        if ($sid -ceq 'S-1-3-0' -and $onlyChildren) { continue }
        $legacy = $sid -ceq 'S-1-5-11' -and (($rights -band $writeMask) -band (-bnot $modify)) -eq 0
        # Only DENYs already encountered in actual DACL order can protect this grant.
        if ($legacy -and ($selfDenied -band $writeMask) -eq $writeMask -and
            (-not $RequireDescendantDeny -or ($descendantsDenied -band $writeMask) -eq $writeMask)) { continue }
        throw ('Install ACL write grant is outside the accepted boundary: path={0}; sid={1}; rights=0x{2:X}; inheritance={3}; propagation={4}; descendantDenyRequired={5}' -f $Path,$sid,$rights,$inherit,$propagate,[bool]$RequireDescendantDeny)
    }
}

function Assert-FortisInstallAccess {
    param([string]$Path, [switch]$RequireDescendantDeny)
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Install path must not contain reparse points: $Path"
    }
    $acl = Get-Acl -LiteralPath $Path
    $owner = $acl.GetOwner([Security.Principal.SecurityIdentifier]).Value
    $rules = @($acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier]) | ForEach-Object {
        [pscustomobject]@{ Sid=$_.IdentityReference.Value; Type=$_.AccessControlType.ToString();
            Rights=[int]$_.FileSystemRights; Inheritance=[int]$_.InheritanceFlags; Propagation=[int]$_.PropagationFlags }
    })
    Assert-FortisInstallAclRules -Path $Path -OwnerSid $owner -Rules $rules -Canonical $acl.AreAccessRulesCanonical -RequireDescendantDeny:$RequireDescendantDeny
}

function Assert-FortisInstallDirectory {
    param([string]$Path, [switch]$RequireDescendantDeny)
    if (-not (Get-Item -LiteralPath $Path -Force -ErrorAction Stop).PSIsContainer) {
        throw "Install parent must be a directory: $Path"
    }
    Assert-FortisInstallAccess -Path $Path -RequireDescendantDeny:$RequireDescendantDeny
}

function Assert-FortisAmd64Executable {
    param([byte[]]$Bytes)
    if ($Bytes.Length -lt 256 -or $Bytes[0] -ne 0x4D -or $Bytes[1] -ne 0x5A) {
        throw 'Runtime is not a Windows PE executable.'
    }
    $offset = [BitConverter]::ToInt32($Bytes, 0x3c)
    if ($offset -lt 64 -or $offset -gt ($Bytes.Length - 6) -or
        [BitConverter]::ToUInt32($Bytes, $offset) -ne 0x00004550 -or
        [BitConverter]::ToUInt16($Bytes, $offset + 4) -ne 0x8664) {
        throw 'Runtime PE architecture must be Windows amd64.'
    }
}

function Read-FortisRuntimeArchive {
    param([string]$Path)
    $file = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
    if ($file.PSIsContainer -or ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $file.Length -gt 100MB -or $file.Length -lt 1) { throw 'Invalid runtime archive file.' }
    if ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -cne $script:FortisPolicy.WindowsRuntimeArchiveSha256) {
        throw 'Runtime archive SHA-256 mismatch; nothing installed.'
    }
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [IO.Compression.ZipFile]::OpenRead($file.FullName)
    try {
        $stem = 'tunnel-client-runtime-v' + $script:FortisPolicy.WindowsRuntimeVersion + '-windows-amd64'
        $expected = @('tunnel-client-runtime.exe', 'LICENSE', 'NOTICE', ($stem + '-licenses.txt'), ($stem + '.spdx.json'))
        $names = @($zip.Entries | ForEach-Object { $_.FullName })
        if ($names.Count -ne $expected.Count -or @($names | Sort-Object -Unique).Count -ne $names.Count -or
            @($names | Where-Object { $expected -cnotcontains $_ }).Count -ne 0) {
            throw 'Runtime archive entries differ from the reviewed release.'
        }
        $entry = $zip.GetEntry('tunnel-client-runtime.exe')
        if ($entry.Length -gt 100MB -or $entry.Length -lt 256) { throw 'Invalid runtime executable size.' }
        $inputStream = $entry.Open()
        $buffer = New-Object IO.MemoryStream
        try {
            $inputStream.CopyTo($buffer)
            $bytes = $buffer.ToArray()
        } finally { $inputStream.Dispose(); $buffer.Dispose() }
        $sha = [Security.Cryptography.SHA256]::Create()
        try { $digest = [BitConverter]::ToString($sha.ComputeHash($bytes)).Replace('-', '') }
        finally { $sha.Dispose() }
        if ($digest -cne $script:FortisPolicy.WindowsRuntimeSha256) { throw 'Extracted runtime SHA-256 mismatch.' }
        Assert-FortisAmd64Executable -Bytes $bytes
        return ,$bytes
    } finally { $zip.Dispose() }
}

if (-not [Environment]::Is64BitOperatingSystem) { throw 'This release requires Windows x64.' }
$target = $script:FortisPolicy.WindowsRuntimePath
$versionDirectory = Split-Path -Parent $target
$runtimeDirectory = Split-Path -Parent $versionDirectory
# Existing dependency tree must already be present; do not bootstrap or change its ACL.
for ($part = $runtimeDirectory; -not [string]::IsNullOrEmpty((Split-Path -Parent $part)); $part = Split-Path -Parent $part) {
    Assert-FortisInstallDirectory -Path $part -RequireDescendantDeny:($part -ceq $runtimeDirectory)
}
if (Test-Path -LiteralPath $versionDirectory) { Assert-FortisInstallDirectory -Path $versionDirectory -RequireDescendantDeny }
if (Test-Path -LiteralPath $target) {
    $file = Get-Item -LiteralPath $target -Force
    if (($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or $file.PSIsContainer) {
        throw 'Runtime target is not a regular file.'
    }
    Assert-FortisInstallAccess -Path $target
    $null = Assert-FortisTunnelRuntime
    Write-Output 'FORTIS_RUNTIME_ALREADY_INSTALLED_HASH_PASS'
    return
}
$bytes = $null
if (-not [string]::IsNullOrWhiteSpace($ArchivePath)) { $bytes = Read-FortisRuntimeArchive -Path $ArchivePath }
[pscustomobject]@{
    Mode = $(if ($Apply) { 'Apply' } else { 'Preview' })
    Version = $script:FortisPolicy.WindowsRuntimeVersion
    UpstreamCommit = $script:FortisPolicy.WindowsRuntimeCommit
    ArchiveUrl = $script:FortisPolicy.WindowsRuntimeArchiveUrl
    ArchiveSha256 = $script:FortisPolicy.WindowsRuntimeArchiveSha256
    ExecutableSha256 = $script:FortisPolicy.WindowsRuntimeSha256
    Target = $target; ExistingRuntimePreserved = $true
    AclBoundary = 'Owner/private or approved FortisHostG1 deny; existing AU Modify preserved'
    ArchiveChecked = ($null -ne $bytes); WorkersRestarted = $false
} | ConvertTo-Json
if (-not $Apply) { Write-Output 'FORTIS_RUNTIME_INSTALL_PREVIEW_PASS'; return }

$temporary = Join-Path ([IO.Path]::GetTempPath()) ('fortis-runtime-install-' + [Guid]::NewGuid().ToString('N'))
if (Test-Path -LiteralPath $temporary) { throw 'Temporary install directory already exists.' }
$null = [IO.Directory]::CreateDirectory($temporary)
try {
    Assert-FortisInstallDirectory -Path $temporary
    if ($null -eq $bytes) {
        $archive = Join-Path $temporary 'runtime.zip'
        $priorProtocol = [Net.ServicePointManager]::SecurityProtocol
        try {
            [Net.ServicePointManager]::SecurityProtocol = $priorProtocol -bor [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -UseBasicParsing -Uri $script:FortisPolicy.WindowsRuntimeArchiveUrl -OutFile $archive -MaximumRedirection 5
        } finally { [Net.ServicePointManager]::SecurityProtocol = $priorProtocol }
        $bytes = Read-FortisRuntimeArchive -Path $archive
    }
    # Recheck trusted ancestors immediately before the write. Never overwrite a target.
    for ($part = $runtimeDirectory; -not [string]::IsNullOrEmpty((Split-Path -Parent $part)); $part = Split-Path -Parent $part) {
        Assert-FortisInstallDirectory -Path $part -RequireDescendantDeny:($part -ceq $runtimeDirectory)
    }
    $null = [IO.Directory]::CreateDirectory($versionDirectory)
    Assert-FortisInstallDirectory -Path $versionDirectory -RequireDescendantDeny
    $file = [IO.File]::Open($target, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try { $file.Write($bytes, 0, $bytes.Length); $file.Flush() }
    finally { $file.Dispose() }
    Assert-FortisInstallAccess -Path $target
    $null = Assert-FortisTunnelRuntime
    $actualVersion = (& $target --version | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $actualVersion -cnotmatch ('^' + [regex]::Escape($script:FortisPolicy.WindowsRuntimeVersion) + ' git sha: ' + $script:FortisPolicy.WindowsRuntimeCommit + ' .*flavor=runtime$')) {
        throw 'Installed executable version/flavor check failed; previous runtime is preserved.'
    }
    Write-Output $actualVersion
    Write-Output 'FORTIS_RUNTIME_INSTALL_APPLY_PASS'
} finally {
    # Only the unique staging directory created by this invocation is removed.
    if (Test-Path -LiteralPath $temporary) { [IO.Directory]::Delete($temporary, $true) }
}
