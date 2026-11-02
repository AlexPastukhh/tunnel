# Repo 2: do not bypass the pinned SHA-256, Guard or identity checks.
$ErrorActionPreference = 'Stop'
$readyMarker = $null
$markerTemp = $null
$exitCode = 0
try {
    $prepare = Join-Path $PSScriptRoot 'launchers\FortisRDGLauncherV2\Start-Fortis.ps1'
    $repo2 = Join-Path $PSScriptRoot 'launchers\FortisRepoPlus2\FortisRepo2-quiet-logs.ps1'
    if (-not (Test-Path -LiteralPath $prepare -PathType Leaf)) { throw "Не найден $prepare" }
    if (-not (Test-Path -LiteralPath $repo2 -PathType Leaf)) { throw "Не найден $repo2" }
    $prepareOutput = @(& $prepare)
    if ($prepareOutput.Count -ne 1 -or [string]$prepareOutput[0] -cnotmatch '^[0-9a-f]{64}$') {
        throw 'Подготовка Fortis не вернула один проверенный Container ID.'
    }
    $containerId = [string]$prepareOutput[0]

    # Publish a PID + process-start marker while this worker owns the Repo 2 session.
    $runDir = Join-Path $env:LOCALAPPDATA 'FortisRdgControlCenter\scripts\runs'
    New-Item -ItemType Directory -Path $runDir -Force | Out-Null
    $workerProcess = Get-Process -Id $PID -ErrorAction Stop
    $readyMarker = Join-Path $runDir ('repo2-worker-{0}.xml' -f $PID)
    $markerDoc = New-Object System.Xml.XmlDocument
    $markerRoot = $markerDoc.CreateElement('Repo2Worker')
    $markerRoot.SetAttribute('pid', [string]$PID)
    $markerRoot.SetAttribute('start', [string]$workerProcess.StartTime.ToBinary())
    [void]$markerDoc.AppendChild($markerRoot)
    $markerTemp = $readyMarker + '.tmp'
    $markerDoc.Save($markerTemp)
    Move-Item -LiteralPath $markerTemp -Destination $readyMarker -Force
    $markerTemp = $null

    Write-Output 'Запуск Fortis Repo 2 (оригинальный quiet-logs скрипт)...'
    & $repo2 -Action Start -ContainerId $containerId
    if (-not $?) { throw 'Fortis Repo 2 завершился с ошибкой.' }
} catch {
    [Console]::Error.WriteLine('REPO2 ERROR: ' + $_.Exception.Message)
    $exitCode = 1
} finally {
    if ($markerTemp -and (Test-Path -LiteralPath $markerTemp)) {
        Remove-Item -LiteralPath $markerTemp -Force -ErrorAction SilentlyContinue
    }
    if ($readyMarker -and (Test-Path -LiteralPath $readyMarker)) {
        Remove-Item -LiteralPath $readyMarker -Force -ErrorAction SilentlyContinue
    }
}
exit $exitCode
