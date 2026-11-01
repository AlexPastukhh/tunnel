# Fortis Repo native tunnel #2, owner-only Windows setup and launcher.
# No Sites. Does not read or change the original repo-mode key/profile/runtime.
[CmdletBinding()]
param([ValidateSet('Setup','Start','Status')][string]$Action = 'Setup')
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ExpectedOwnerSid = 'S-1-5-21-303538662-3368424508-2654684973-1001'
$who = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($env:OS -ne 'Windows_NT' -or $who.User.Value -cne $ExpectedOwnerSid) {
    throw 'Run only under the original Windows owner account (alexa), not G2 or Administrator.'
}

$TunnelId = 'tunnel_6adb9a27e544819199cb194e420028d1'
$ProfileName = 'repo-mode-plus2'
$Root = Join-Path $env:LOCALAPPDATA 'FortisRepoPlus2'
$ProfileDir = Join-Path $Root 'profiles'
$SecretDir = Join-Path $Root 'secrets'
$KeyFile = Join-Path $SecretDir 'runtime.key'
$InstalledScript = Join-Path $Root 'FortisRepo2.ps1'
$Client = 'C:\Tools\tunnel-client\tunnel-client.exe'
$Runtime = 'C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe'
$RuntimeSha = 'A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A'
$Bridge = 'docker exec -i --env NODE_OPTIONS=--import=data:text/javascript;base64,Ly8gREMgMC4yLjUyIGVtaXRzIGVhY2ggbG9nZ2luZyBub3RpZmljYXRpb24gaW4gb25lIGNvbXBsZXRlIHN0ZG91dC53cml0ZS4KLy8gVGhpcyBhdmFpbGFiaWxpdHkgcG9saWN5IGlzIG5vdCBhIHNlY3VyaXR5IGJvdW5kYXJ5IG9yIGEgZ2VuZXJpYyBNQ1AgcHJveHkuCi8vIFVucmVjb2duaXNlZCwgbWFsZm9ybWVkLCBmcmFnbWVudGVkIGFuZCBiYXRjaGVkIHdyaXRlcyBwYXNzIHRocm91Z2ggdW5jaGFuZ2VkLgoKY29uc3Qgb3duT3B0aW9uID0gYC0taW1wb3J0PSR7aW1wb3J0Lm1ldGEudXJsfWA7CmlmIChwcm9jZXNzLmVudi5OT0RFX09QVElPTlMgPT09IG93bk9wdGlvbikgewogIC8vIFRoZSBwcmVsb2FkIGJlbG9uZ3MgdG8gdGhlIE1DUCBzZXJ2ZXIsIG5vdCBkZXZlbG9wbWVudCBjb21tYW5kcyBpdCBzcGF3bnMuCiAgZGVsZXRlIHByb2Nlc3MuZW52Lk5PREVfT1BUSU9OUzsKfQoKY29uc3Qgb3JpZ2luYWxXcml0ZSA9IHByb2Nlc3Muc3Rkb3V0LndyaXRlOwpjb25zdCBoYXNPd24gPSBPYmplY3QucHJvdG90eXBlLmhhc093blByb3BlcnR5OwoKZnVuY3Rpb24gaXNMb2dnaW5nTm90aWZpY2F0aW9uKGNodW5rLCBlbmNvZGluZykgewogIGlmIChlbmNvZGluZyAhPSBudWxsICYmIHR5cGVvZiBlbmNvZGluZyAhPT0gJ3N0cmluZycgJiYgdHlwZW9mIGVuY29kaW5nICE9PSAnZnVuY3Rpb24nKSByZXR1cm4gZmFsc2U7CiAgaWYgKHR5cGVvZiBlbmNvZGluZyA9PT0gJ3N0cmluZycgJiYgIUJ1ZmZlci5pc0VuY29kaW5nKGVuY29kaW5nKSkgcmV0dXJuIGZhbHNlOwogIGlmICh0eXBlb2YgY2h1bmsgIT09ICdzdHJpbmcnICYmICFCdWZmZXIuaXNCdWZmZXIoY2h1bmspKSByZXR1cm4gZmFsc2U7CiAgaWYgKHR5cGVvZiBjaHVuayA9PT0gJ3N0cmluZycgJiYgdHlwZW9mIGVuY29kaW5nID09PSAnc3RyaW5nJyAmJgogICAgICAhWyd1dGY4JywgJ3V0Zi04J10uaW5jbHVkZXMoZW5jb2RpbmcudG9Mb3dlckNhc2UoKSkpIHJldHVybiBmYWxzZTsKCiAgY29uc3QgdGV4dCA9IHR5cGVvZiBjaHVuayA9PT0gJ3N0cmluZycgPyBjaHVuayA6IGNodW5rLnRvU3RyaW5nKCd1dGY4Jyk7CiAgLy8gSW5zcGVjdCBvbmx5IGNvbXBsZXRlIHNpbmdsZS1saW5lIG1lc3NhZ2VzLCBhcyB3cml0dGVuIGJ5IHRoZSBwaW5uZWQgREMuCiAgaWYgKCF0ZXh0LmVuZHNXaXRoKCdcbicpIHx8IHRleHQuaW5kZXhPZignXG4nKSAhPT0gdGV4dC5sZW5ndGggLSAxIHx8CiAgICAgICF0ZXh0LmluY2x1ZGVzKCcibm90aWZpY2F0aW9ucy9tZXNzYWdlIicpKSByZXR1cm4gZmFsc2U7CiAgdHJ5IHsKICAgIGNvbnN0IHBhY2tldCA9IEpTT04ucGFyc2UodGV4dCk7CiAgICByZXR1cm4gcGFja2V0ICE9PSBudWxsICYmIHR5cGVvZiBwYWNrZXQgPT09ICdvYmplY3QnICYmICFBcnJheS5pc0FycmF5KHBhY2tldCkgJiYKICAgICAgcGFja2V0Lmpzb25ycGMgPT09ICcyLjAnICYmIHBhY2tldC5tZXRob2QgPT09ICdub3RpZmljYXRpb25zL21lc3NhZ2UnICYmCiAgICAgICFoYXNPd24uY2FsbChwYWNrZXQsICdpZCcpOwogIH0gY2F0Y2ggewogICAgcmV0dXJuIGZhbHNlOwogIH0KfQoKcHJvY2Vzcy5zdGRvdXQud3JpdGUgPSBmdW5jdGlvbiBxdWlldE1jcExvZ3MoY2h1bmssIGVuY29kaW5nLCBjYWxsYmFjaykgewogIGlmICgoY2FsbGJhY2sgPT0gbnVsbCB8fCB0eXBlb2YgY2FsbGJhY2sgPT09ICdmdW5jdGlvbicpICYmCiAgICAgIGlzTG9nZ2luZ05vdGlmaWNhdGlvbihjaHVuaywgZW5jb2RpbmcpKSB7CiAgICBjb25zdCBkb25lID0gdHlwZW9mIGVuY29kaW5nID09PSAnZnVuY3Rpb24nID8gZW5jb2RpbmcgOiBjYWxsYmFjazsKICAgIGlmICh0eXBlb2YgZG9uZSA9PT0gJ2Z1bmN0aW9uJykgcHJvY2Vzcy5uZXh0VGljayhkb25lKTsKICAgIHJldHVybiB0cnVlOwogIH0KICAvLyBQcmVzZXJ2ZSB0aGUgb3JpZ2luYWwgYnl0ZXMsIG92ZXJsb2FkcywgcmV0dXJuIHZhbHVlIGFuZCBiYWNrcHJlc3N1cmUuCiAgcmV0dXJuIFJlZmxlY3QuYXBwbHkob3JpZ2luYWxXcml0ZSwgdGhpcywgYXJndW1lbnRzKTsKfTsK fortis-repo-test node /opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js'
if ($Action -eq 'Setup') { throw 'Side-by-side quiet candidate refuses Setup/profile or shortcut changes.' }
if ($Action -eq 'Start') {
    $quietDocker = (Get-Command docker.exe -CommandType Application -ErrorAction Stop).Source
    $quietRaw = & $quietDocker inspect --type container -- fortis-repo-test 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'Quiet launcher container inspect failed.' }
    $quietInfo = @($quietRaw | ConvertFrom-Json)
    if ($quietInfo.Count -ne 1 -or
        $quietInfo[0].Id -ne '0c0f8cb2d608679b4c3de51c527cbe2aca687cbf1360e6bf116444b2a0928cc2' -or
        -not $quietInfo[0].State.Running) { throw 'Quiet launcher pinned container missing.' }
    $quietEnv = @($quietInfo[0].Config.Env | Where-Object {
        ([string]$_).StartsWith('NODE_OPTIONS=', [StringComparison]::Ordinal)
    })
    if ($quietEnv.Count -gt 1 -or
        ($quietEnv.Count -eq 1 -and $quietEnv[0] -cne 'NODE_OPTIONS=')) {
        throw 'Quiet launcher refuses existing NODE_OPTIONS.'
    }
}
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
    if ((Get-FileHash -LiteralPath $Runtime -Algorithm SHA256).Hash -cne $RuntimeSha) {
        throw 'Narrow runtime SHA256 changed; refusing startup.'
    }
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
        '08AB2A7B3051E6899A47AF8CD09FC2FFE6E560CD7638B8160D1B2C3A40402241') {
        throw 'Repo 2 Direct guard fingerprint mismatch.'
    }

    $repo2GuardResult = & $repo2Guard -Mode Run

    if (
        @($repo2GuardResult).Count -ne 1 -or
        @($repo2GuardResult)[0] -ne 'REPO2_DIRECT_GUARD_PASS'
    ) {
        throw 'Repo 2 Direct security preflight failed.'
    }

        Assert-ClientRuntime
        $profilePath = Get-ProfilePath
        $body = Assert-Profile $profilePath
        if (-not $body.Contains($NewRef)) {throw 'Second profile does not reference its saved key file'}
        if (-not (Test-Path -LiteralPath $KeyFile -PathType Leaf)) {throw 'Second saved key file is missing'}
        if (@(Get-Repo2Runtime).Count -gt 0) {throw 'Second tunnel already running; refusing duplicate start.'}
        $running = & docker inspect --format '{{.State.Running}}' fortis-repo-test 2>$null
        if ($LASTEXITCODE -ne 0 -or $running -ne 'true') {throw 'Existing Fortis Repo Docker container is not running'}
        & docker exec fortis-repo-test test -r /opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js
        if ($LASTEXITCODE -ne 0) {throw 'Existing MCP bridge is not readable'}

        Write-Output ('Checking second tunnel ' + $TunnelId + ' (no changes to first Repo) ...')
        & $Client doctor --profile $ProfileName --profile-dir $ProfileDir --mcp.command "command=$Bridge" --explain *> $null
        if ($LASTEXITCODE -ne 0) {throw 'Second tunnel doctor failed. No runtime started.'}
        Write-Output 'Starting SECOND tunnel via pinned narrow runtime. Ctrl+C stops this instance.'
        & $Runtime run --profile $ProfileName --profile-dir $ProfileDir --mcp.command "command=$Bridge" '--harpoon.additional-transport='
        if ($LASTEXITCODE -ne 0) {throw 'Second tunnel runtime exited with an error'}
        return
    }
}
