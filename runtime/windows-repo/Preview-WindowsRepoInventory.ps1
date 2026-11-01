# Read-only Windows provenance inventory. No profile/key content is accessed.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows PowerShell required.' }
$root = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..')).TrimEnd('\')
$expected = [IO.Path]::GetFullPath((Join-Path $env:USERPROFILE 'Repos\tunnel')).TrimEnd('\')
if (-not [string]::Equals($root,$expected,[StringComparison]::OrdinalIgnoreCase)) {
    throw 'Use the Windows Git clone at %USERPROFILE%\Repos\tunnel.'
}
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'release-manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$targets = [ordered]@{
    'repo1/control.ps1' = (Join-Path $env:USERPROFILE 'chatgpt-repo-mode\control.ps1')
    'repo1/run-tunnel-quiet-logs.ps1' = (Join-Path $env:USERPROFILE 'chatgpt-repo-mode\run-tunnel-quiet-logs.ps1')
    'repo2/Repo2DirectGuard.ps1' = (Join-Path $env:LOCALAPPDATA 'FortisRepoPlus2\Repo2DirectGuard.ps1')
    'repo2/FortisRepo2-quiet-logs.ps1' = (Join-Path $env:LOCALAPPDATA 'FortisRepoPlus2\FortisRepo2-quiet-logs.ps1')
}
$report = foreach ($rel in $targets.Keys) {
    $source = Join-Path $PSScriptRoot ($rel.Replace('/','\'))
    $installed = $targets[$rel]
    $sourceSha = $(if (Test-Path -LiteralPath $source -PathType Leaf) {
        (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
    } else { $null })
    $installedSha = $(if (Test-Path -LiteralPath $installed -PathType Leaf) {
        (Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash
    } else { $null })
    [pscustomobject]@{
        component = $rel
        source_hash_matches_manifest = ($null -ne $sourceSha -and
            @($manifest.files | Where-Object { $_.path -ceq $rel -and $_.sha256 -ceq $sourceSha }).Count -eq 1)
        installed_path_exists = ($null -ne $installedSha)
        installed_matches_source = $(if ($null -eq $installedSha) { 'UNKNOWN' }
            elseif ($installedSha -ceq $sourceSha) { 'YES' } else { 'NO' })
        source_sha256 = $sourceSha
        installed_sha256 = $installedSha
    }
}
$report | Format-List
Write-Output 'NOTE: installed-path list is a documented guess. Exact live shortcut paths and active process origin are NOT verified.'
