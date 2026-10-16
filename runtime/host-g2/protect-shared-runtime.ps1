[CmdletBinding()]
param(
    [ValidateSet('Preview', 'Apply', 'Rollback')]
    [string]$Mode = 'Preview',
    [string]$BackupPath
)
$ErrorActionPreference = 'Stop'

$restrictedSid = 'S-1-5-21-303538662-3368424508-2654684973-1009'
$ownerSid = 'S-1-5-21-303538662-3368424508-2654684973-1001'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$administrator = ([Security.Principal.WindowsPrincipal]$identity).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)
if ($Mode -ne 'Preview' -and ($identity.User.Value -ne $ownerSid -or !$administrator)) {
    throw 'Apply/Rollback requires an administrator PowerShell opened manually by owner alexa.'
}

$targets = @(
    [pscustomobject]@{ Path = 'C:\Tools'; Inherit = $false },
    [pscustomobject]@{ Path = 'C:\Tools\tunnel-client'; Inherit = $true },
    [pscustomobject]@{ Path = 'C:\Tools\desktop-commander-runtime'; Inherit = $true },
    [pscustomobject]@{ Path = 'C:\Tools\desktop-commander'; Inherit = $true }
)
# Deny only mutation rights to SID 1009; retain read/list/execute.
# WriteData/CreateFiles, AppendData/CreateDirectories, WriteEA, DeleteChild,
# WriteAttributes, Delete, WriteDac, WriteOwner.
$denyRights = [Security.AccessControl.FileSystemRights]0xD0156
$accessSection = [Security.AccessControl.AccessControlSections]::Access
$backupRoot = Join-Path $env:LOCALAPPDATA 'FortisHostG2AclBackup'

foreach ($target in $targets) {
    $item = Get-Item -LiteralPath $target.Path -Force
    if (!$item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw ('Target must be an ordinary directory: ' + $target.Path)
    }
}

if ($Mode -eq 'Rollback') {
    if (!$BackupPath) { throw 'Rollback requires the exact backup file returned by Apply.' }
    $fullBackup = [IO.Path]::GetFullPath($BackupPath)
    $prefix = [IO.Path]::GetFullPath($backupRoot) + [IO.Path]::DirectorySeparatorChar
    if (!$fullBackup.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Backup must be in the owner FortisHostG2AclBackup directory.'
    }
    $backup = [IO.File]::ReadAllText($fullBackup) | ConvertFrom-Json
    if ($backup.Version -ne 1 -or $backup.RestrictedSid -ne $restrictedSid -or
        @($backup.Entries).Count -ne $targets.Count) { throw 'Invalid backup metadata.' }

    # Validate the complete rollback before changing any DACL.
    foreach ($target in $targets) {
        $entry = @($backup.Entries | Where-Object { $_.Path -ceq $target.Path })
        if ($entry.Count -ne 1) { throw 'Backup target mismatch.' }
        $current = (Get-Acl -LiteralPath $target.Path).GetSecurityDescriptorSddlForm($accessSection)
        if ($current -cne $entry[0].Before -and $current -cne $entry[0].After) {
            throw ('DACL has unrelated changes; manual review required: ' + $target.Path)
        }
    }
    foreach ($target in $targets) {
        $entry = @($backup.Entries | Where-Object { $_.Path -ceq $target.Path })[0]
        $acl = Get-Acl -LiteralPath $target.Path
        if ($acl.GetSecurityDescriptorSddlForm($accessSection) -ceq $entry.Before) { continue }
        $acl.SetSecurityDescriptorSddlForm($entry.Before, $accessSection)
        Set-Acl -LiteralPath $target.Path -AclObject $acl
        if ((Get-Acl -LiteralPath $target.Path).GetSecurityDescriptorSddlForm($accessSection) -cne $entry.Before) {
            throw ('Rollback verification failed: ' + $target.Path)
        }
    }
    Write-Output 'Restored the four saved DACLs; backup retained. Verify inherited child ACLs separately.'
    return
}

$entries = @()
foreach ($target in $targets) {
    $acl = Get-Acl -LiteralPath $target.Path
    $before = $acl.GetSecurityDescriptorSddlForm($accessSection)
    $inheritance = [Security.AccessControl.InheritanceFlags]::None
    if ($target.Inherit) {
        $inheritance = [Security.AccessControl.InheritanceFlags](
            [Security.AccessControl.InheritanceFlags]::ContainerInherit -bor
            [Security.AccessControl.InheritanceFlags]::ObjectInherit
        )
    }
    $rule = New-Object Security.AccessControl.FileSystemAccessRule(
        (New-Object Security.Principal.SecurityIdentifier($restrictedSid)),
        $denyRights,
        $inheritance,
        [Security.AccessControl.PropagationFlags]::None,
        [Security.AccessControl.AccessControlType]::Deny
    )
    $acl.AddAccessRule($rule)
    $entries += [pscustomobject]@{
        Path = $target.Path
        Inherit = $target.Inherit
        Before = $before
        After = $acl.GetSecurityDescriptorSddlForm($accessSection)
    }
}

if ($Mode -eq 'Preview') {
    [pscustomobject]@{
        Mode = 'Preview - no filesystem or ACL writes'
        RestrictedSid = $restrictedSid
        DenyMask = '0xD0156'
        Targets = $entries
        Note = 'Child inheritance/explicit ACE exceptions require restricted-token verification after approval.'
    } | ConvertTo-Json -Depth 6
    return
}

if ($BackupPath) { throw 'Apply creates its own unique backup; do not pass BackupPath.' }
[IO.Directory]::CreateDirectory($backupRoot) | Out-Null
$BackupPath = Join-Path $backupRoot ('runtime-dacl-' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ') + '-' + [guid]::NewGuid().ToString('N') + '.json')
$backup = [pscustomobject]@{
    Version = 1
    RestrictedSid = $restrictedSid
    OwnerSid = $identity.User.Value
    CreatedUtc = [DateTime]::UtcNow.ToString('o')
    Entries = $entries
}
$bytes = (New-Object Text.UTF8Encoding($false)).GetBytes(($backup | ConvertTo-Json -Depth 8))
$stream = [IO.File]::Open($BackupPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
try { $stream.Write($bytes, 0, $bytes.Length) } finally { $stream.Dispose() }
Write-Output ('Backup: ' + $BackupPath)

foreach ($entry in $entries) {
    $acl = Get-Acl -LiteralPath $entry.Path
    if ($acl.GetSecurityDescriptorSddlForm($accessSection) -cne $entry.Before) {
        throw ('DACL changed after preview; stop and retain backup: ' + $entry.Path)
    }
    $acl.SetSecurityDescriptorSddlForm($entry.After, $accessSection)
    Set-Acl -LiteralPath $entry.Path -AclObject $acl
    if ((Get-Acl -LiteralPath $entry.Path).GetSecurityDescriptorSddlForm($accessSection) -cne $entry.After) {
        throw ('DACL verification failed; stop and retain backup: ' + $entry.Path)
    }
    Write-Output ('Applied SID 1009 mutation deny: ' + $entry.Path)
}
Write-Output 'DACL change applied. No services/tunnels restarted. Restricted-token and child ACL verification is still required.'
