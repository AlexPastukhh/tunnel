# Owner-run side-by-side install only. Does not start workers or change profiles.
[CmdletBinding()]
param([switch]$Apply, [string]$ArchivePath)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$policyPath = Join-Path $PSScriptRoot 'current\launchers\shared\FortisContainerPolicy.ps1'
. $policyPath
$identity = Assert-FortisWindowsOwner

function Assert-FortisInstallAccess {
    param([string]$Path)
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw 'Install path must not contain reparse points.'
    }
    $trusted = @($script:FortisPolicy.OwnerSid, 'S-1-5-18', 'S-1-5-32-544')
    $acl = Get-Acl -LiteralPath $Path
    $owner = $acl.GetOwner([Security.Principal.SecurityIdentifier]).Value
    if ($trusted -cnotcontains $owner) { throw 'Install path owner is not trusted.' }
    $writeMask = [Security.AccessControl.FileSystemRights]'Write, Delete, DeleteSubdirectoriesAndFiles, ChangePermissions, TakeOwnership'
    foreach ($rule in $acl.Access) {
        $sid = $rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
        if ($rule.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow -and
            ($rule.FileSystemRights -band $writeMask) -ne 0 -and $trusted -cnotcontains $sid) {
            throw 'Install path permits another principal to write; ACL was not changed.'
        }
    }
}

function Assert-FortisInstallDirectory {
    param([string]$Path)
    if (-not (Get-Item -LiteralPath $Path -Force -ErrorAction Stop).PSIsContainer) {
        throw 'Install parent must be a directory.'
    }
    Assert-FortisInstallAccess -Path $Path
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
    Assert-FortisInstallDirectory -Path $part
}
if (Test-Path -LiteralPath $versionDirectory) { Assert-FortisInstallDirectory -Path $versionDirectory }
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
        Assert-FortisInstallDirectory -Path $part
    }
    $null = [IO.Directory]::CreateDirectory($versionDirectory)
    Assert-FortisInstallDirectory -Path $versionDirectory
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
