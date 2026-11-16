# Offline behavioral checks; no Windows install, network, real runtime or credentials.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$policy = Join-Path $PSScriptRoot 'current/launchers/shared/FortisContainerPolicy.ps1'
. $policy
$installer = Join-Path $PSScriptRoot 'Install-FortisRuntime.ps1'
$tokens = $null; $errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile($installer, [ref]$tokens, [ref]$errors)
if ($errors.Count -ne 0) { throw 'Installer syntax failed.' }
# Load only pure archive/PE functions. Never invoke installer entrypoint or bypass its owner gate.
foreach ($name in @('Assert-FortisAmd64Executable', 'Read-FortisRuntimeArchive', 'Assert-FortisInstallAccess', 'Assert-FortisInstallDirectory')) {
    $function = $ast.Find({ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -ceq $name }, $true)
    if ($null -eq $function) { throw "Function missing: $name" }
    . ([scriptblock]::Create($function.Extent.Text))
}
$folder = Join-Path ([IO.Path]::GetTempPath()) ('fortis-install-test-' + [Guid]::NewGuid().ToString('N'))
$null = [IO.Directory]::CreateDirectory($folder)
$checks = 0
function Pass([string]$Name) { $script:checks++; Write-Output ('PASS ' + $Name) }
function Reject([string]$Name, [scriptblock]$Action) {
    $rejected = $false
    try { & $Action | Out-Null } catch { $rejected = $true }
    if (-not $rejected) { throw "Expected rejection: $Name" }
    Pass $Name
}
function Digest([byte[]]$Bytes) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($sha.ComputeHash($Bytes)).Replace('-', '') }
    finally { $sha.Dispose() }
}
function New-TestArchive([string]$Path, [byte[]]$Bytes, [string]$Extra = '') {
    $zip = [IO.Compression.ZipFile]::Open($Path, [IO.Compression.ZipArchiveMode]::Create)
    try {
        $stem = 'tunnel-client-runtime-v' + $script:FortisPolicy.WindowsRuntimeVersion + '-windows-amd64'
        $names = @('tunnel-client-runtime.exe','LICENSE','NOTICE',($stem+'-licenses.txt'),($stem+'.spdx.json'))
        if ($Extra) { $names += $Extra }
        foreach ($name in $names) {
            $entry = $zip.CreateEntry($name); $stream = $entry.Open()
            try { if ($name -ceq 'tunnel-client-runtime.exe') { $stream.Write($Bytes,0,$Bytes.Length) } }
            finally { $stream.Dispose() }
        }
    } finally { $zip.Dispose() }
}
try {
    if ($env:OS -ceq 'Windows_NT') {
        $currentSid = [Security.Principal.WindowsIdentity]::GetCurrent().User
        if ($currentSid.Value -cne $script:FortisPolicy.OwnerSid) {
            Reject 'production-owner-sid-gate' { Assert-FortisWindowsOwner }
        }
        # Only the private fixture ACL is modified. Production installer never changes ACL.
        $script:FortisPolicy.OwnerSid = $currentSid.Value
        $aclFolder = Join-Path $folder 'acl-fixture'
        $null = [IO.Directory]::CreateDirectory($aclFolder)
        $acl = New-Object Security.AccessControl.DirectorySecurity
        $acl.SetOwner($currentSid)
        $acl.SetAccessRuleProtection($true,$false)
        $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($currentSid,'FullControl','ContainerInherit, ObjectInherit','None','Allow'))
        Set-Acl -LiteralPath $aclFolder -AclObject $acl
        Assert-FortisInstallDirectory $aclFolder; Pass 'owner-only-directory-acl'
        $everyone = [Security.Principal.SecurityIdentifier]::new('S-1-1-0')
        $badRule = [Security.AccessControl.FileSystemAccessRule]::new($everyone,'Modify','Allow')
        $acl.AddAccessRule($badRule)
        Set-Acl -LiteralPath $aclFolder -AclObject $acl
        Reject 'other-principal-write-acl' { Assert-FortisInstallDirectory $aclFolder }
        $acl.RemoveAccessRuleSpecific($badRule)
        Set-Acl -LiteralPath $aclFolder -AclObject $acl
        $junction = Join-Path $folder 'junction-fixture'
        $null = New-Item -ItemType Junction -Path $junction -Target $aclFolder
        try { Reject 'reparse-install-directory' { Assert-FortisInstallDirectory $junction } }
        finally { [IO.Directory]::Delete($junction) }
    }
    $bytes = New-Object byte[] 256
    $bytes[0]=0x4D; $bytes[1]=0x5A; $bytes[0x3c]=0x40
    $bytes[0x40]=0x50; $bytes[0x41]=0x45; $bytes[0x44]=0x64; $bytes[0x45]=0x86
    Assert-FortisAmd64Executable $bytes; Pass 'valid-amd64-pe'
    $wrong = [byte[]]$bytes.Clone(); $wrong[0x45]=0x01
    Reject 'wrong-pe-architecture' { Assert-FortisAmd64Executable $wrong }
    $wrong = [byte[]]$bytes.Clone(); $wrong[0x3c]=0xFF
    Reject 'pe-offset-out-of-bounds' { Assert-FortisAmd64Executable $wrong }
    Reject 'truncated-pe' { Assert-FortisAmd64Executable ([byte[]]@(0x4D,0x5A)) }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = Join-Path $folder 'valid.zip'
    New-TestArchive $archive $bytes
    $script:FortisPolicy.WindowsRuntimeArchiveSha256 = (Get-FileHash $archive -Algorithm SHA256).Hash
    $script:FortisPolicy.WindowsRuntimeSha256 = Digest $bytes
    $read = Read-FortisRuntimeArchive $archive
    if ($read.Length -ne 256 -or (Digest $read) -cne (Digest $bytes)) { throw 'Archive bytes changed.' }
    Pass 'valid-reviewed-archive'
    $script:FortisPolicy.WindowsRuntimeArchiveSha256 = '0' * 64
    Reject 'archive-hash-mismatch' { Read-FortisRuntimeArchive $archive }
    $script:FortisPolicy.WindowsRuntimeArchiveSha256 = (Get-FileHash $archive -Algorithm SHA256).Hash
    $script:FortisPolicy.WindowsRuntimeSha256 = '0' * 64
    Reject 'extracted-exe-hash-mismatch' { Read-FortisRuntimeArchive $archive }
    $script:FortisPolicy.WindowsRuntimeSha256 = Digest $bytes
    foreach ($extra in @('unreviewed.exe','../escape.exe','tunnel-client-runtime.exe')) {
        $archive = Join-Path $folder ([Guid]::NewGuid().ToString('N') + '.zip')
        New-TestArchive $archive $bytes $extra
        $script:FortisPolicy.WindowsRuntimeArchiveSha256 = (Get-FileHash $archive -Algorithm SHA256).Hash
        Reject ('unreviewed-archive-entry-' + $extra) { Read-FortisRuntimeArchive $archive }
    }
    $runtime = Join-Path $folder 'runtime.bin'
    [IO.File]::WriteAllBytes($runtime,$bytes)
    $script:FortisPolicy.WindowsRuntimePath = $runtime
    $script:FortisPolicy.WindowsRuntimeSha256 = Digest $bytes
    $null = Assert-FortisTunnelRuntime; Pass 'matching-runtime-accepted'
    [IO.File]::WriteAllText($runtime,'tampered')
    Reject 'modified-runtime-rejected' { Assert-FortisTunnelRuntime }
    [IO.File]::Delete($runtime)
    Reject 'missing-runtime-rejected' { Assert-FortisTunnelRuntime }
    # Use a synthetic PowerShell command to exercise console/file mirroring and exit reporting.
    $fake = Join-Path $folder 'synthetic-runtime.ps1'
    @'
param([Parameter(ValueFromRemainingArguments=$true)][object[]]$Remaining)
foreach ($arg in $Remaining) {
    if ([string]$arg -like '--pid.file=*') { [IO.File]::WriteAllText(([string]$arg).Substring(11),[string]$PID) }
}
Write-Output '{"msg":"synthetic runtime event"}'
$global:LASTEXITCODE = 0
'@ | Set-Content -LiteralPath $fake -Encoding UTF8
    function Assert-FortisTunnelRuntime { return $fake }
    foreach ($repo in @('Repo1','Repo2')) {
        $printed = @(Invoke-FortisRepoRuntime -Repo $repo -LogDirectory $folder -RuntimeArguments @('--profile','synthetic'))
        $records = @($printed | ForEach-Object { $_ | ConvertFrom-Json })
        if ($records.Count -ne 4 -or $records[0].repo -cne $repo -or $records[1].runtime_pid -ne $PID -or $records[3].exit_code -ne 0) { throw 'Console records differ.' }
        $file = Join-Path $folder ('runtime-diag-' + $records[0].run_id + '.jsonl')
        $saved = @([IO.File]::ReadAllLines($file))
        if (($saved -join "`n") -cne ($printed -join "`n")) { throw 'Diagnostic file differs from console.' }
        if ($ErrorActionPreference -cne 'Stop') { throw 'Error preference was not restored.' }
        Pass ('console-and-log-mirror-' + $repo)
    }
    $originalFake = [IO.File]::ReadAllText($fake)
    [IO.File]::WriteAllText($fake, $originalFake.Replace('$global:LASTEXITCODE = 0', '$global:LASTEXITCODE = 7'))
    Reject 'nonzero-runtime-exit-rejected' { Invoke-FortisRepoRuntime -Repo Repo1 -LogDirectory $folder -RuntimeArguments @() }
    [IO.File]::WriteAllText($fake, $originalFake.Replace('$global:LASTEXITCODE = 0', ''))
    $global:LASTEXITCODE = 0
    Reject 'missing-runtime-exit-code-rejected' { Invoke-FortisRepoRuntime -Repo Repo2 -LogDirectory $folder -RuntimeArguments @() }
    Write-Output ("FORTIS_RUNTIME_INSTALL_OFFLINE_PASS checks=$checks; Windows live acceptance not tested")
} finally { [IO.Directory]::Delete($folder,$true) }
