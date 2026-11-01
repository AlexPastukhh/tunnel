# Windows Git-clone entry. Dispatches to the byte-exact current Control Center workers.
# Default = read-only Preview. Start requires a clean main clone and typed owner confirmation.
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
$expectedManifestHash = 'D47234936171E7E47B870533AB06452BFA13E0DAA30F90ABB1367C4B66EC91E0'
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
    'launchers/FortisRepoPlus2/FortisRepo2-quiet-logs.ps1'
)
if ($manifest.schema_version -ne 1 -or
    $manifest.status -cne 'BYTE_EXACT_MIRROR_OF_CURRENT_SCRIPT_CONTROL_CENTER_WORKING_CHAIN' -or
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
$branch = (& git -C $actualRoot branch --show-current)
if ($LASTEXITCODE -ne 0 -or $branch.Trim() -cne 'main') {
    throw 'Windows tunnel clone must be on main. Nothing started.'
}
$dirty = @(& git -C $actualRoot status --porcelain --untracked-files=normal)
if ($LASTEXITCODE -ne 0 -or $dirty.Count -ne 0) {
    throw 'Windows tunnel clone must be clean. Nothing started.'
}
$confirmation = Read-Host ('Type START ' + $Repo + ' to launch only that profile (no other tunnel is stopped)')
if ($confirmation -cne ('START ' + $Repo)) { throw 'Owner confirmation missing. Nothing started.' }
Write-Output ('Launching unchanged current ' + $Repo + ' worker chain...')
if ($Repo -eq 'Repo1') {
    & $repo1Worker
} else {
    & $repo2Worker
}
if (-not $?) { throw ($Repo + ' worker returned an unsuccessful status.') }
