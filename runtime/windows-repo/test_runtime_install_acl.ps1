# Dot-sourced by test_runtime_install.ps1. Synthetic ACLs; no production writes.
function New-AclFixtureRule {
    param([string]$Sid, [string]$Type, [int]$Rights, [int]$Inheritance = 0, [int]$Propagation = 0)
    [pscustomobject]@{ Sid=$Sid; Type=$Type; Rights=$Rights; Inheritance=$Inheritance; Propagation=$Propagation }
}
function Check-AclFixture {
    param([string]$Name, [object[]]$Rules, [switch]$ShouldReject, [switch]$Descendants,
          [bool]$Canonical = $true, [string]$Owner = $script:FortisPolicy.OwnerSid)
    $action = { Assert-FortisInstallAclRules -Path 'C:\fixture' -OwnerSid $Owner -Rules $Rules -Canonical $Canonical -RequireDescendantDeny:$Descendants }
    if ($ShouldReject) { Reject $Name $action } else { & $action; Pass $Name }
}
$aclGuest = 'S-1-5-21-303538662-3368424508-2654684973-1009'
$aclWrite = [int][Security.AccessControl.FileSystemRights]'Write, Delete, DeleteSubdirectoriesAndFiles, ChangePermissions, TakeOwnership'
$aclModify = [int][Security.AccessControl.FileSystemRights]::Modify
$aclFull = [int][Security.AccessControl.FileSystemRights]::FullControl
$aclRead = [int][Security.AccessControl.FileSystemRights]::ReadAndExecute
$aclOwnerGrant = New-AclFixtureRule $script:FortisPolicy.OwnerSid 'Allow' $aclFull 3
$aclAu = New-AclFixtureRule 'S-1-5-11' 'Allow' $aclModify
$aclAuChildren = New-AclFixtureRule 'S-1-5-11' 'Allow' $aclModify 3 2
$aclGuestTree = New-AclFixtureRule $aclGuest 'Deny' $aclWrite 3
$aclGuestSelf = New-AclFixtureRule $aclGuest 'Deny' $aclWrite
$aclUsersRead = New-AclFixtureRule 'S-1-5-32-545' 'Allow' $aclRead 3
$aclLegacy = @($aclGuestTree,$aclOwnerGrant,$aclUsersRead,$aclAu,$aclAuChildren)
Check-AclFixture 'acl-private-owner' @($aclOwnerGrant) -Descendants
Check-AclFixture 'acl-approved-runtime-shape' $aclLegacy -Descendants
Check-AclFixture 'acl-tools-parent-self-deny' @($aclGuestSelf,$aclOwnerGrant,$aclAu,$aclAuChildren)
Check-AclFixture 'acl-new-descendants-need-inherited-deny' @($aclGuestSelf,$aclOwnerGrant,$aclAu,$aclAuChildren) -ShouldReject -Descendants
Check-AclFixture 'acl-au-write-needs-guest-deny' @($aclOwnerGrant,$aclAu) -ShouldReject
Check-AclFixture 'acl-other-guest-deny-not-equivalent' @((New-AclFixtureRule 'S-1-5-21-303538662-3368424508-2654684973-1010' 'Deny' $aclWrite 3),$aclOwnerGrant,$aclAu) -ShouldReject
Check-AclFixture 'acl-partial-deny-not-equivalent' @((New-AclFixtureRule $aclGuest 'Deny' 2 3),$aclOwnerGrant,$aclAu) -ShouldReject
Check-AclFixture 'acl-inherit-only-deny-not-effective-here' @((New-AclFixtureRule $aclGuest 'Deny' $aclWrite 3 2),$aclOwnerGrant,$aclAu) -ShouldReject
Check-AclFixture 'acl-no-propagation-rejected-for-new-exe' @((New-AclFixtureRule $aclGuest 'Deny' $aclWrite 3 1),$aclOwnerGrant,$aclAu) -ShouldReject -Descendants
Check-AclFixture 'acl-container-only-deny-misses-leaf' @((New-AclFixtureRule $aclGuest 'Deny' $aclWrite 1),$aclOwnerGrant,$aclAu) -ShouldReject -Descendants
Check-AclFixture 'acl-object-only-deny-misses-directory' @((New-AclFixtureRule $aclGuest 'Deny' $aclWrite 2),$aclOwnerGrant,$aclAu) -ShouldReject -Descendants
Check-AclFixture 'acl-allow-before-deny-rejected' @($aclAu,$aclGuestTree,$aclOwnerGrant) -ShouldReject -Descendants
Check-AclFixture 'acl-unknown-writer-remains-rejected' @($aclGuestTree,$aclOwnerGrant,(New-AclFixtureRule 'S-1-1-0' 'Allow' $aclModify)) -ShouldReject
Check-AclFixture 'acl-au-full-control-not-legacy-modify' @($aclGuestTree,$aclOwnerGrant,(New-AclFixtureRule 'S-1-5-11' 'Allow' $aclFull)) -ShouldReject
Check-AclFixture 'acl-untrusted-owner-rejected' $aclLegacy -Owner $aclGuest -ShouldReject
Check-AclFixture 'acl-noncanonical-rejected' $aclLegacy -Canonical $false -ShouldReject
Check-AclFixture 'acl-empty-or-null-dacl-rejected' @() -ShouldReject
Check-AclFixture 'acl-public-read-needs-no-deny' @($aclOwnerGrant,$aclUsersRead)
Check-AclFixture 'acl-creator-owner-template' @($aclOwnerGrant,(New-AclFixtureRule 'S-1-3-0' 'Allow' $aclFull 3 2)) -Descendants
Check-AclFixture 'acl-effective-creator-owner-not-assumed-safe' @($aclOwnerGrant,(New-AclFixtureRule 'S-1-3-0' 'Allow' $aclFull 3)) -ShouldReject
Check-AclFixture 'acl-creator-group-template-not-assumed-safe' @($aclOwnerGrant,(New-AclFixtureRule 'S-1-3-1' 'Allow' $aclFull 3 2)) -ShouldReject
Check-AclFixture 'acl-generic-rights-fail-closed' @($aclOwnerGrant,(New-AclFixtureRule 'S-1-5-11' 'Allow' 268435456)) -ShouldReject
Check-AclFixture 'acl-invalid-inheritance-fail-closed' @($aclOwnerGrant,(New-AclFixtureRule 'S-1-5-11' 'Allow' $aclModify 4)) -ShouldReject
Check-AclFixture 'acl-invalid-propagation-fail-closed' @($aclOwnerGrant,(New-AclFixtureRule 'S-1-5-11' 'Allow' $aclModify 0 2)) -ShouldReject
$aclMessage = ''
try { Assert-FortisInstallAclRules -Path 'C:\fixture' -OwnerSid $script:FortisPolicy.OwnerSid -Rules @($aclOwnerGrant,$aclAu) -Canonical $true }
catch { $aclMessage = $_.Exception.Message }
if (-not $aclMessage.Contains('C:\fixture') -or -not $aclMessage.Contains('S-1-5-11')) { throw 'ACL error must identify path and SID.' }
Pass 'acl-diagnostic-identifies-path-and-sid'

if ($env:OS -ceq 'Windows_NT') {
    # Actual NTFS inheritance fixtures, all under this test's unique temporary root.
    $fixtureOwnerSid = [Security.Principal.WindowsIdentity]::GetCurrent().User
    $fixtureGuestSid = [Security.Principal.SecurityIdentifier]::new($aclGuest)
    $fixtureAuSid = [Security.Principal.SecurityIdentifier]::new('S-1-5-11')
    function New-LegacyAclFixture([bool]$TreeDeny) {
        $security = New-Object Security.AccessControl.DirectorySecurity
        $security.SetOwner($fixtureOwnerSid); $security.SetAccessRuleProtection($true,$false)
        $security.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($fixtureOwnerSid,'FullControl','ContainerInherit, ObjectInherit','None','Allow'))
        $flags = if ($TreeDeny) { [Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit' } else { [Security.AccessControl.InheritanceFlags]::None }
        $security.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($fixtureGuestSid,[Security.AccessControl.FileSystemRights]$aclWrite,$flags,[Security.AccessControl.PropagationFlags]::None,'Deny'))
        $security.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($fixtureAuSid,'Modify','Allow'))
        $security.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($fixtureAuSid,'Modify','ContainerInherit, ObjectInherit','InheritOnly','Allow'))
        return $security
    }
    $legacyParent = Join-Path $folder 'legacy-acl-parent'
    $null = [IO.Directory]::CreateDirectory($legacyParent)
    Set-Acl -LiteralPath $legacyParent -AclObject (New-LegacyAclFixture $true)
    $legacyChild = Join-Path $legacyParent 'version-child'
    $null = [IO.Directory]::CreateDirectory($legacyChild)
    $legacyFile = Join-Path $legacyChild 'synthetic-runtime.bin'
    [IO.File]::WriteAllBytes($legacyFile,[byte[]]@(1,2,3))
    $beforeDacl = (Get-Acl -LiteralPath $legacyChild).GetSecurityDescriptorSddlForm([Security.AccessControl.AccessControlSections]::Access)
    Assert-FortisInstallDirectory -Path $legacyChild -RequireDescendantDeny
    Pass 'acl-native-inherited-guest-deny-and-au-modify'
    Assert-FortisInstallAccess -Path $legacyFile
    Pass 'acl-native-leaf-inherits-guest-deny'
    $afterDacl = (Get-Acl -LiteralPath $legacyChild).GetSecurityDescriptorSddlForm([Security.AccessControl.AccessControlSections]::Access)
    if ($beforeDacl -cne $afterDacl) { throw 'Installer validation changed fixture ACL.' }
    Pass 'acl-native-validation-does-not-write'
    $childAcl = Get-Acl -LiteralPath $legacyChild
    $childAcl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($fixtureAuSid,'Modify','Allow'))
    Set-Acl -LiteralPath $legacyChild -AclObject $childAcl
    Reject 'acl-native-explicit-allow-before-inherited-deny' { Assert-FortisInstallDirectory -Path $legacyChild -RequireDescendantDeny }
    $missingParent = Join-Path $folder 'no-descendant-deny-parent'
    $null = [IO.Directory]::CreateDirectory($missingParent)
    Set-Acl -LiteralPath $missingParent -AclObject (New-LegacyAclFixture $false)
    Assert-FortisInstallDirectory -Path $missingParent
    Pass 'acl-native-parent-self-only-deny'
    Reject 'acl-native-new-descendants-require-propagation' { Assert-FortisInstallDirectory -Path $missingParent -RequireDescendantDeny }
}
