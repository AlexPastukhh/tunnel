# Repo 1: starts independently and preserves all checks in the installed quiet launcher.
$ErrorActionPreference = 'Stop'
try {
    # The installed Repo 1 launcher enforces its own Docker/Guard/bootstrap checks.
    # No dependence on the Repo 2 Windows process is imposed by this adapter.
    $script = Join-Path $PSScriptRoot 'launchers\chatgpt-repo-mode\run-tunnel-quiet-logs.ps1'
    if (-not (Test-Path -LiteralPath $script -PathType Leaf)) { throw "Не найден $script" }
    Write-Output 'Запуск Fortis Repo 1 (существующий quiet-logs скрипт)...'
    & $script -Mode Run
    if (-not $?) { throw 'Fortis Repo 1 завершился с ошибкой.' }
} catch {
    [Console]::Error.WriteLine('REPO1 ERROR: ' + $_.Exception.Message)
    exit 1
}
