# Fortis Repo native tunnel #2, owner-only Windows setup and launcher.
# No Sites. Does not read or change the original repo-mode key/profile/runtime.
[CmdletBinding()]
param([ValidateSet('Setup','Start','Status')][string]$Action = 'Setup', [string]$ContainerId)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$policyPath = Join-Path $PSScriptRoot '..\\shared\\FortisContainerPolicy.ps1'
if (-not (Test-Path -LiteralPath $policyPath -PathType Leaf)) { throw 'Shared Fortis policy is missing.' }
. $policyPath
$who = Assert-FortisWindowsOwner
$ExpectedOwnerSid = $script:FortisPolicy.OwnerSid

$TunnelId = 'tunnel_6adb9a27e544819199cb194e420028d1'
$ProfileName = 'repo-mode-plus2'
$Root = Join-Path $env:LOCALAPPDATA 'FortisRepoPlus2'
$ProfileDir = Join-Path $Root 'profiles'
$SecretDir = Join-Path $Root 'secrets'
$KeyFile = Join-Path $SecretDir 'runtime.key'
$InstalledScript = Join-Path $Root 'FortisRepo2.ps1'
$Client = 'C:\Tools\tunnel-client\tunnel-client.exe'
$Runtime = $script:FortisPolicy.WindowsRuntimePath
$BridgeTemplate = 'docker exec -i --env NODE_OPTIONS=__FORTIS_NODE_OPTIONS__ __FORTIS_CONTAINER_ID__ __FORTIS_NODE_PATH__ __FORTIS_DIRECT_ENTRY__'
if ($Action -eq 'Setup') { throw 'Side-by-side quiet candidate refuses Setup/profile or shortcut changes.' }
$OldRef = 'env:FORTIS_REPO2_TUNNEL_KEY'
$NewRef = 'file:' + $KeyFile.Replace('\','/')

function Assert-RegularDirectory([string]$path) {
    if (-not (Test-Path -LiteralPath $path -PathType Container)) {
        throw "Directory not found: $path"
    }
    $info = Get-Item -LiteralPath $path -Force
    if (($info.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Refusing reparse-point directory: $path"
    }
}

function Get-ProfilePath {
    Assert-RegularDirectory $ProfileDir
    $found = @(
        Get-ChildItem -LiteralPath $ProfileDir -File | Where-Object {
            $_.Name -eq ($ProfileName + '.yaml') -or $_.Name -eq ($ProfileName + '.yml')
        }
    )
    if ($found.Count -ne 1) {
        throw "Expected exactly one $ProfileName.yaml/.yml in $ProfileDir; create the independent profile first."
    }
    if (($found[0].Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw 'Refusing reparse-point profile'
    }
    return $found[0].FullName
}

function Assert-Profile([string]$profilePath) {
    $body = [IO.File]::ReadAllText($profilePath)
    if (-not $body.Contains($TunnelId) -or
        $body.Contains('tunnel_6ac9e4dc9e688191ae1838e858424e8d')) {
        throw 'Profile Tunnel ID mismatch: leave both tunnels unchanged.'
    }
    return $body
}

function Get-Repo2Runtime {
    # Inspect only the narrow-runtime process and its loopback /metrics.
    $processes = @(Get-CimInstance Win32_Process -Filter "Name = 'tunnel-client-runtime.exe'" -ErrorAction SilentlyContinue)
    foreach ($p in $processes) {
        $sockets = @(Get-NetTCPConnection -OwningProcess $p.ProcessId -State Listen -ErrorAction SilentlyContinue)
        foreach ($s in $sockets) {
            if ($s.LocalAddress -ne '127.0.0.1') { continue }
            $url = 'http://127.0.0.1:' + [string]$s.LocalPort
            try {
                $body = (Invoke-WebRequest ($url + '/metrics') -UseBasicParsing -TimeoutSec 2).Content
                if (-not $body.Contains($TunnelId)) { continue }
                [PSCustomObject]@{ TunnelId=$TunnelId; PID=$p.ProcessId; Health=$url+'/health'; Started=$p.CreationDate }
            } catch { }
        }
    }
}

function Assert-ClientRuntime {
    if (-not (Test-Path -LiteralPath $Client -PathType Leaf)) {throw 'tunnel-client.exe missing'}
    if (-not (Test-Path -LiteralPath $Runtime -PathType Leaf)) {throw 'Pinned narrow runtime missing'}
    $null = Assert-FortisTunnelRuntime
}

switch ($Action) {
    'Status' {
        $active = @(Get-Repo2Runtime)
        if ($active.Count -eq 0) { Write-Output 'Fortis Repo 2: no running tunnel detected' }
        else { $active | Format-Table -AutoSize }
        return
    }
    'Setup' {
        Assert-ClientRuntime
        Assert-RegularDirectory $Root
        if (@(Get-Repo2Runtime).Count -gt 0) {throw 'Stop ONLY the second tunnel with Ctrl+C before Setup.'}
        $profilePath = Get-ProfilePath
        $body = Assert-Profile $profilePath
        if (([regex]::Matches($body,[regex]::Escape($OldRef))).Count -ne 1) {
            throw 'Expected one env:FORTIS_REPO2_TUNNEL_KEY in the second profile. Nothing changed.'
        }
        if (Test-Path -LiteralPath $SecretDir) {throw 'Secrets directory already exists: refusing to overwrite key or ACL.'}
        if (Test-Path -LiteralPath $InstalledScript) {throw 'Launcher already installed: refusing overwrite.'}

        # Create and lock a NEW local-only directory before handling a key.
        $null = [IO.Directory]::CreateDirectory($SecretDir)
        $security = New-Object Security.AccessControl.DirectorySecurity
        $security.SetAccessRuleProtection($true,$false)
        $rule = [Security.AccessControl.FileSystemAccessRule]::new(
            $who.User,
            [Security.AccessControl.FileSystemRights]::FullControl,
            [Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit',
            [Security.AccessControl.PropagationFlags]::None,
            [Security.AccessControl.AccessControlType]::Allow)
        $security.AddAccessRule($rule)
        Set-Acl -LiteralPath $SecretDir -AclObject $security
        $realSecurity = Get-Acl -LiteralPath $SecretDir
        if (-not $realSecurity.AreAccessRulesProtected) {throw 'Secrets ACL inherits unexpectedly'}
        foreach ($access in $realSecurity.Access) {
            $sid = $access.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
            if ($sid -cne $ExpectedOwnerSid) {throw 'Unexpected principal in secrets ACL; refusing key storage'}
        }

        $secret = Read-Host 'Enter the SECOND account runtime API key (hidden)' -AsSecureString
        $ptr = [IntPtr]::Zero
        $bytes = $null
        try {
            if ($secret.Length -lt 20 -or $secret.Length -gt 4096) {throw 'Unexpected API key length'}
            $bytes = New-Object byte[] $secret.Length
            $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
            for ($i=0; $i -lt $secret.Length; $i++) {
                $character = [Runtime.InteropServices.Marshal]::ReadInt16($ptr,$i*2)
                if ($character -lt 33 -or $character -gt 126) {throw 'API key must be one ASCII token without spaces'}
                $bytes[$i] = [byte]$character
            }
            $file = [IO.File]::Open($KeyFile,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
            try { $file.Write($bytes,0,$bytes.Length) }
            finally { $file.Dispose() }
        } finally {
            if ($ptr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
            if ($null -ne $bytes) { [Array]::Clear($bytes,0,$bytes.Length) }
            if ($null -ne $secret) { $secret.Dispose() }
        }
        $fileAcl = Get-Acl -LiteralPath $KeyFile
        foreach ($access in $fileAcl.Access) {
            $sid = $access.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
            if ($sid -cne $ExpectedOwnerSid) {throw 'Unexpected key-file ACL; check before running.'}
        }

        # Update only the SECOND profile, changing a reference, never embedding the secret.
        $updated = $body.Replace($OldRef,$NewRef)
        [IO.File]::WriteAllText($profilePath,$updated,([System.Text.UTF8Encoding]::new($false)))
        Copy-Item -LiteralPath $PSCommandPath -Destination $InstalledScript -ErrorAction Stop
        # The user explicitly ran the inspected setup file; allow the installed copy to run under RemoteSigned.
        Unblock-File -LiteralPath $InstalledScript -ErrorAction Stop

        # Desktop shortcut is a manual launcher, not autostart.
        $desktop = [Environment]::GetFolderPath('Desktop')
        $shortcutPath = Join-Path $desktop 'Fortis Repo 2.lnk'
        if (Test-Path -LiteralPath $shortcutPath) {
            Write-Warning "Shortcut already exists and was not overwritten: $shortcutPath"
        } else {
            $shell = New-Object -ComObject WScript.Shell
            $link = $shell.CreateShortcut($shortcutPath)
            $link.TargetPath = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
            $link.Arguments = '-NoProfile -NoExit -File "' + $InstalledScript + '" -Action Start'
            $link.WorkingDirectory = $Root
            $link.Description = 'Start only the second Fortis Repo secure MCP tunnel'
            $link.Save()
        }
        Write-Output 'Setup complete: independent key saved with owner-only ACL; second profile points to file:...'
        Write-Output ('Profile: ' + $profilePath)
        Write-Output ('Key path (not content): ' + $KeyFile)
        Write-Output ('Manual launcher: ' + $InstalledScript)
        Write-Output 'To start: double-click Desktop\Fortis Repo 2.lnk, or run FortisRepo2.ps1 -Action Start.'
        return
    }
    'Start' {
    $repo2Guard = Join-Path $PSScriptRoot 'Repo2DirectGuard.ps1'

    if ((Get-FileHash -LiteralPath $repo2Guard -Algorithm SHA256).Hash -ne
        '29A885E33E7B034E13C7CB228E108D9074567FA66FAC69A6A70ED318BA17BB73') {
        throw 'Repo 2 Direct guard fingerprint mismatch.'
    }

    $repo2GuardResult = @(& $repo2Guard -Mode Run -ContainerId $ContainerId)
    if ($repo2GuardResult.Count -ne 1) {
        throw 'Repo 2 shared security Guard failed.'
    }
    $containerMatch = [regex]::Match([string]$repo2GuardResult[0], '^REPO2_DIRECT_GUARD_PASS:([0-9a-f]{64})$')
    if (-not $containerMatch.Success) { throw 'Repo 2 Guard did not return its inspected container ID.' }
    $fortisContainerId = $containerMatch.Groups[1].Value
    $Bridge = $BridgeTemplate.Replace('__FORTIS_CONTAINER_ID__', $fortisContainerId).Replace('__FORTIS_NODE_PATH__', $script:FortisPolicy.LinuxNodePath).Replace('__FORTIS_DIRECT_ENTRY__', $script:FortisPolicy.DirectEntryPath).Replace('__FORTIS_NODE_OPTIONS__', $script:FortisPolicy.QuietNodeOption)

        Assert-ClientRuntime
        $profilePath = Get-ProfilePath
        $body = Assert-Profile $profilePath
        if (-not $body.Contains($NewRef)) {throw 'Second profile does not reference its saved key file'}
        if (-not (Test-Path -LiteralPath $KeyFile -PathType Leaf)) {throw 'Second saved key file is missing'}
        if (@(Get-Repo2Runtime).Count -gt 0) {throw 'Second tunnel already running; refusing duplicate start.'}
        Write-Output ('Checking second tunnel ' + $TunnelId + ' (no changes to first Repo) ...')
        & $Client doctor --profile $ProfileName --profile-dir $ProfileDir --mcp.command "command=$Bridge" --explain *> $null
        if ($LASTEXITCODE -ne 0) {throw 'Second tunnel doctor failed. No runtime started.'}
        Write-Output 'Starting SECOND tunnel via pinned narrow runtime. Ctrl+C stops this instance.'
        & $Runtime run --profile $ProfileName --profile-dir $ProfileDir --mcp.command "command=$Bridge" '--harpoon.additional-transport='
        if ($LASTEXITCODE -ne 0) {throw 'Second tunnel runtime exited with an error'}
        return
    }
}
