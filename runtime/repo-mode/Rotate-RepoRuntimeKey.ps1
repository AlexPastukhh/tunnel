#requires -Version 5.1
<#
.SYNOPSIS
  Local owner-only rotation of the *saved* Repo tunnel control-plane API key.
.DESCRIPTION
  Preview performs metadata/ACL checks only. Install prompts locally for a NEW
  provider-issued API key, DPAPI-backs up the existing bytes under LocalAppData,
  atomically replaces the pinned runtime.key with identical ACL, then exits.
  Rollback restores a specific DPAPI backup *only while the old key is valid*.
  Does not issue/revoke API keys, start/stop/restart tunnels, change profile IDs,
  Docker, permissions, mounts, or launch legacy HOST.
.EXAMPLE
  .\Rotate-RepoRuntimeKey.ps1 -Action Preview
  .\Rotate-RepoRuntimeKey.ps1 -Action Install
  .\Rotate-RepoRuntimeKey.ps1 -Action Rollback -BackupFile 'C:\...\repo-key-...dpapi'
#>
[CmdletBinding()]
param(
    [ValidateSet('Preview','Install','Rollback')][string]$Action='Preview',
    [string]$BackupFile
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

# Pin this machine's owner account; never run under G2 or from Repo Docker.
$ExpectedOwnerSid='S-1-5-21-303538662-3368424508-2654684973-1001'
$who=[Security.Principal.WindowsIdentity]::GetCurrent()
if ($who.User.Value -cne $ExpectedOwnerSid) {throw 'Exact existing owner Windows SID is required'}
if ($env:OS -ne 'Windows_NT' -or ![Environment]::Is64BitProcess) {
    throw 'Windows x64 PowerShell 5.1+ required'
}
$keyPath=Join-Path $env:USERPROFILE 'AppData\Roaming\tunnel-client\runtime.key'
$keyParent=Split-Path -Parent $keyPath
$vault=Join-Path $env:LOCALAPPDATA 'FortisRepoKeyRotation'
if (!(Test-Path -LiteralPath $keyPath -PathType Leaf)) {
    throw 'Existing saved Repo key absent. Do not create profile or key here.'
}
foreach ($path in @($keyParent,$keyPath)) {
    $item=Get-Item -LiteralPath $path -Force
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw 'Refusing reparse point on key path'
    }
}
$acl=Get-Acl -LiteralPath $keyPath
if (!$acl.AreAccessRulesProtected) {
    throw 'Existing key ACL inherits permissions; investigate before rotation'
}
$ownerSid=$acl.Owner
try {
    $ownerSid=([Security.Principal.NTAccount]$acl.Owner).Translate(
        [Security.Principal.SecurityIdentifier]).Value
} catch {
    if ($ownerSid -cne $ExpectedOwnerSid) {
        throw 'Cannot resolve saved key owner'
    }
}
if ($ownerSid -cne $ExpectedOwnerSid) {throw 'Saved key has an unexpected owner'}
# Do not silently copy broad ACLs onto a newly provisioned secret.
foreach ($rule in $acl.Access) {
    $sid=$rule.IdentityReference.Translate(
        [Security.Principal.SecurityIdentifier]).Value
    if ($sid -notin @($ExpectedOwnerSid,'S-1-5-18')) {
        throw 'Saved key has unexpected ACL entry; refusing'
    }
}
Write-Output 'Repo runtime key: existing file/owner/ACL checks passed; contents not displayed.'
Write-Output 'Note: retired owner HOST historically references the same saved key file.'
# Windows PowerShell 5.1 does not automatically load ProtectedData.
# Preview must test the DPAPI dependency before accepting a real secret.
$dpapiProbe=$null
$dpapiEncrypted=$null
$dpapiPlain=$null
try {
    Add-Type -AssemblyName System.Security -ErrorAction Stop
    $dpapiProbe=[Text.Encoding]::ASCII.GetBytes('FORTIS_SYNTHETIC_DPAPI_CHECK_ONLY')
    $dpapiEncrypted=[Security.Cryptography.ProtectedData]::Protect(
        $dpapiProbe,$null,[Security.Cryptography.DataProtectionScope]::CurrentUser)
    $dpapiPlain=[Security.Cryptography.ProtectedData]::Unprotect(
        $dpapiEncrypted,$null,[Security.Cryptography.DataProtectionScope]::CurrentUser)
    if ([Convert]::ToBase64String($dpapiPlain) -cne
        [Convert]::ToBase64String($dpapiProbe)) {
        throw 'Synthetic DPAPI roundtrip mismatch'
    }
} catch {
    throw 'DPAPI self-test failed before any saved Repo key change. Check Windows PowerShell/System.Security.'
} finally {
    if ($null -ne $dpapiProbe) {[Array]::Clear($dpapiProbe,0,$dpapiProbe.Length)}
    if ($null -ne $dpapiEncrypted) {[Array]::Clear($dpapiEncrypted,0,$dpapiEncrypted.Length)}
    if ($null -ne $dpapiPlain) {[Array]::Clear($dpapiPlain,0,$dpapiPlain.Length)}
}
Write-Output 'SYNTHETIC_DPAPI_CHECK_PASS: current owner DPAPI Protect/Unprotect works in memory.'
if ($Action -eq 'Preview') {
    Write-Output 'PREVIEW ONLY: no key bytes read, file written, or tunnel restarted.'
    return
}

function Assert-Vault {
    if (!(Test-Path -LiteralPath $vault -PathType Container)) {
        $null=[IO.Directory]::CreateDirectory($vault)
        $security=New-Object Security.AccessControl.DirectorySecurity
        $security.SetAccessRuleProtection($true,$false)
        $userRule=[Security.AccessControl.FileSystemAccessRule]::new(
            $who.User,[Security.AccessControl.FileSystemRights]::FullControl,
            [Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit',
            [Security.AccessControl.PropagationFlags]::None,
            [Security.AccessControl.AccessControlType]::Allow)
        $security.AddAccessRule($userRule)
        Set-Acl -LiteralPath $vault -AclObject $security
    }
    $info=Get-Item -LiteralPath $vault -Force
    if (($info.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw 'Refusing reparse point in backup location'
    }
    $security=Get-Acl -LiteralPath $vault
    if (!$security.AreAccessRulesProtected) {
        throw 'Backup directory ACL not protected'
    }
    foreach ($rule in $security.Access) {
        $sid=$rule.IdentityReference.Translate(
            [Security.Principal.SecurityIdentifier]).Value
        if ($sid -notin @($ExpectedOwnerSid,'S-1-5-18')) {
            throw 'Backup location accessible by unexpected principal'
        }
    }
}
function Write-ExactKey([byte[]]$newKey) {
    $temp=Join-Path $keyParent ('runtime.key.new-'+[guid]::NewGuid().ToString('N')+'.tmp')
    try {
        [IO.File]::WriteAllBytes($temp,$newKey)
        Set-Acl -LiteralPath $temp -AclObject $acl
        $tempAcl=Get-Acl -LiteralPath $temp
        if ($tempAcl.Sddl -cne $acl.Sddl) {
            throw 'Staged file security descriptor differs from old key'
        }
        # Same-volume replacement. Existing profile keeps its file: reference.
        [IO.File]::Replace($temp,$keyPath,$null,$false)
        $replacedAcl=Get-Acl -LiteralPath $keyPath
        if ($replacedAcl.Sddl -cne $acl.Sddl) {
            throw 'Replacement ACL differs. Restore using the DPAPI backup.'
        }
    } finally {
        if (Test-Path -LiteralPath $temp -PathType Leaf) {
            Remove-Item -LiteralPath $temp -Force
        }
    }
}

Assert-Vault
if ($Action -eq 'Install') {
    if ($BackupFile) {throw 'BackupFile is only for Rollback'}
    Write-Warning 'Get the new runtime API key from your provider FIRST. Do not revoke the old key yet.'
    $newSecure=Read-Host 'Enter NEW Repo API key locally (input hidden)' -AsSecureString
    $pointer=[IntPtr]::Zero
    $candidate=$null
    try {
        $pointer=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($newSecure)
        $value=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
        if ($value.Length -lt 20 -or $value.Length -gt 4096 -or
            $value -notmatch '^[\x21-\x7e]+$') {
            throw 'New key must be one nonempty printable ASCII token (20..4096 chars)'
        }
        $candidate=[Text.UTF8Encoding]::new($false).GetBytes($value)
        $old=[IO.File]::ReadAllBytes($keyPath)
        try {
            $identical=$candidate.Length -eq $old.Length
            if ($identical) {
                for ($i=0;$i -lt $old.Length;$i++) {
                    if ($candidate[$i] -ne $old[$i]) {$identical=$false;break}
                }
            }
            if ($identical) {throw 'New key is identical to the saved key; nothing rotated'}
            $backupName='repo-key-'+[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')+'-'+
                        [guid]::NewGuid().ToString('N')+'.dpapi'
            $backup=Join-Path $vault $backupName
            $encrypted=[Security.Cryptography.ProtectedData]::Protect(
                $old,$null,[Security.Cryptography.DataProtectionScope]::CurrentUser)
            try {
                [IO.File]::WriteAllBytes($backup,$encrypted)
            } finally {
                [Array]::Clear($encrypted,0,$encrypted.Length)
            }
            Write-Output ('DPAPI rollback snapshot prepared at: '+$backup)
            Write-ExactKey $candidate
            Write-Output 'INSTALL COMPLETE: Repo saved file replaced; running daemon NOT restarted.'
            Write-Output 'Next: restart ONLY Repo through the existing control; verify MCP.'
            Write-Output 'Only THEN revoke the old provider key. DPAPI backup can no longer authenticate once revoked.'
        } finally {
            [Array]::Clear($old,0,$old.Length)
        }
    } finally {
        if ($null -ne $candidate) {[Array]::Clear($candidate,0,$candidate.Length)}
        if ($pointer -ne [IntPtr]::Zero) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
        }
        if ($null -ne $newSecure) {$newSecure.Dispose()}
    }
    return
}
if ($Action -eq 'Rollback') {
    if (!$BackupFile) {throw 'Rollback requires exact DPAPI BackupFile'}
    $full=[IO.Path]::GetFullPath($BackupFile)
    if ([IO.Path]::GetFullPath((Split-Path -Parent $full)) -ine
        [IO.Path]::GetFullPath($vault)) {
        throw 'Rollback backup must be within owner-private local vault'
    }
    if ([IO.Path]::GetFileName($full) -notmatch
        '^repo-key-[0-9]{8}T[0-9]{6}Z-[0-9a-f]{32}\.dpapi$') {
        throw 'Unexpected backup filename'
    }
    $backupItem=Get-Item -LiteralPath $full -Force
    if (($backupItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw 'Refusing reparse point for backup'
    }
    $confirm=Read-Host 'Type ROLLBACK to restore old key (provider key must still be valid)'
    if ($confirm -cne 'ROLLBACK') {throw 'Cancelled'}
    $encrypted=[IO.File]::ReadAllBytes($full)
    try {
        $old=[Security.Cryptography.ProtectedData]::Unprotect(
            $encrypted,$null,[Security.Cryptography.DataProtectionScope]::CurrentUser)
        try {
            Write-ExactKey $old
        } finally {
            [Array]::Clear($old,0,$old.Length)
        }
    } finally {
        [Array]::Clear($encrypted,0,$encrypted.Length)
    }
    Write-Output 'ROLLBACK COMPLETE: saved old key restored; restart ONLY Repo and verify.'
}
