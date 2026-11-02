# Windows Git-clone entry. Default Preview; Start requires a clean canonical main and typed owner confirmation.
# Default = read-only Preview of the isolated candidate tree.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('Repo1','Repo2')][string]$Repo,
    [ValidateSet('Preview','Start')][string]$Action='Preview'
)
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows PowerShell required.' }
$expectedRoot = [IO.Path]::GetFullPath((Join-Path $env:USERPROFILE 'Repos\tunnel')).TrimEnd('\')
$actualRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..')).TrimEnd('\')
if (-not [string]::Equals($actualRoot,$expectedRoot,[StringComparison]::OrdinalIgnoreCase)) {
    throw 'Refusing launch outside the Windows Git clone %USERPROFILE%\Repos\tunnel.'
}
$currentRoot = Join-Path $PSScriptRoot 'current'
$manifestPath = Join-Path $currentRoot 'source-manifest.json'
$expectedManifestHash = '0B7277548FAFCBF153680BADE1A54A75978CD5D2F0C165964A0DD10004EE87A1'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf) -or
    (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash -cne $expectedManifestHash) {
    throw 'Current worker source manifest fingerprint mismatch.'
}
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$expectedFiles = @(
    'Repo1-Worker.ps1',
    'Repo2-Worker.ps1',
    'launchers/chatgpt-repo-mode/control.ps1',
    'launchers/chatgpt-repo-mode/run-tunnel-quiet-logs.ps1',
    'launchers/FortisRDGLauncherV2/Common.ps1',
    'launchers/FortisRDGLauncherV2/Start-Fortis.ps1',
    'launchers/FortisRepoPlus2/Repo2DirectGuard.ps1',
    'launchers/FortisRepoPlus2/FortisRepo2-quiet-logs.ps1',
    'launchers/shared/FortisContainerPolicy.ps1'
)
if ($manifest.schema_version -ne 1 -or
    $manifest.status -cne 'TUNNEL_CANONICAL_SHARED_GUARD_POLICY_GO3C' -or
    $manifest.source_repository -cne 'tunnel' -or
    $manifest.source_ref -cne 'tunnel:main' -or
    $manifest.source_revision_type -cne 'sha256_file_inventory_v1' -or
    $manifest.source_revision -cne 'FF1052F8DD3527861FBE663FF34A10A44A2752A55F02CC2678DFA0D6229C4471' -or
    @($manifest.files).Count -ne $expectedFiles.Count) {
    throw 'Unexpected current worker manifest schema/status. Nothing started.'
}
foreach ($rel in $expectedFiles) {
    $entries = @($manifest.files | Where-Object { $_.path -ceq $rel })
    if ($entries.Count -ne 1 -or ([string]$entries[0].sha256) -cnotmatch '^[0-9A-F]{64}$') {
        throw ('Missing or invalid current worker hash: ' + $rel)
    }
    $file = Join-Path $currentRoot ($rel.Replace('/','\'))
    if (-not (Test-Path -LiteralPath $file -PathType Leaf) -or
        (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -cne $entries[0].sha256) {
        throw ('Current worker source hash mismatch: ' + $rel)
    }
}
$repo1Worker = Join-Path $currentRoot 'Repo1-Worker.ps1'
$repo2Worker = Join-Path $currentRoot 'Repo2-Worker.ps1'
$repo1Preview = Join-Path $currentRoot 'launchers\chatgpt-repo-mode\run-tunnel-quiet-logs.ps1'
$repo2Guard = Join-Path $currentRoot 'launchers\FortisRepoPlus2\Repo2DirectGuard.ps1'
$repo2Status = Join-Path $currentRoot 'launchers\FortisRepoPlus2\FortisRepo2-quiet-logs.ps1'
if ($Action -eq 'Preview') {
    Write-Output ('SOURCE_CHECK_PASS; Repo=' + $Repo + '; Action=Preview; no stop/restart requested')
    if ($Repo -eq 'Repo1') {
        & $repo1Preview -Mode Preview
    } else {
        & $repo2Guard -Mode Preview
        if (-not $?) { throw 'Repo 2 Guard Preview failed.' }
        & $repo2Status -Action Status
    }
    return
}
# Explicit Windows owner gate. No git pull, service stop, or Docker restart here.
$origin = @(& git -C $actualRoot remote get-url origin)
if ($LASTEXITCODE -ne 0 -or $origin.Count -ne 1 -or $origin[0] -cnotmatch '^https://github\.com/AlexPastukhh/tunnel(?:\.git)?$') {
    throw 'Windows tunnel clone has an unexpected origin. Nothing started.'
}
$branch = (& git -C $actualRoot branch --show-current)
if ($LASTEXITCODE -ne 0 -or $branch.Trim() -cne 'main') {
    throw 'Windows tunnel clone must be on main. Nothing started.'
}
$sync = @(& git -C $actualRoot rev-list --left-right --count 'HEAD...origin/main')
if ($LASTEXITCODE -ne 0 -or $sync.Count -ne 1 -or ([string]$sync[0]).Trim() -notmatch '^0\s+0$') {
    throw 'Windows tunnel main must be synchronized with origin/main. Nothing started.'
}
$dirty = @(& git -C $actualRoot status --porcelain --untracked-files=normal)
if ($LASTEXITCODE -ne 0 -or $dirty.Count -ne 0) {
    throw 'Windows tunnel clone must be clean. Nothing started.'
}
$confirmation = Read-Host ('Type START ' + $Repo + ' to launch only that profile (no other tunnel or container is stopped)')
if ($confirmation -cne ('START ' + $Repo)) { throw 'Owner confirmation missing. Nothing started.' }
Write-Output ('Launching current ' + $Repo + ' worker chain; this dispatcher does not stop or recreate Fortis...')
if ($Repo -eq 'Repo1') {
    & $repo1Worker
} else {
    & $repo2Worker
}
if (-not $?) { throw ($Repo + ' worker returned an unsuccessful status.') }
