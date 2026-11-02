# Repo2 orchestration. Shared security decisions live only in launchers/shared.
$ErrorActionPreference = 'Stop'
$policyPath = Join-Path $PSScriptRoot '..\\shared\\FortisContainerPolicy.ps1'
if (-not (Test-Path -LiteralPath $policyPath -PathType Leaf)) { throw 'Shared Fortis policy is missing.' }
. $policyPath

$script:FortisName = $script:FortisPolicy.ContainerName
$script:UpdaterPath = Join-Path $env:LOCALAPPDATA 'RDG-Server\cicd-bootstrap-ci-20261029t051843803595-4546c7d69e\files\RDG-CICD-Bootstrap\Update-RDG.ps1'
$script:RdgCiRoot = '/workspace/repo/Workfiles/rdg-ci'
$script:WatcherRegex = 'python3(?:\.\d+)?\s+-B\s+tools/rdg-ci\.py\s+--watch(?:\s|$)'
$script:FortisContext = $null
$script:FortisContainerId = $null

function Assert-Docker {
    $null = Get-FortisDockerPath
}

function Ensure-Fortis {
    param([switch]$DontStart)
    $context = Get-FortisContainerContext -AllowStopped
    if (-not $context.Info.State.Running) {
        if ($DontStart) { throw 'Fortis is stopped; read-only checks do not start it.' }
        Write-Host 'Запускаем существующий контейнер fortis-repo-test...' -ForegroundColor Yellow
        $context = Start-FortisContainer -Context $context
    }
    $script:FortisContext = $context
    $script:FortisContainerId = $context.ContainerId
    return [string]$script:FortisContainerId
}

function Get-WatcherMatches {
    if ($null -eq $script:FortisContext) { throw 'Run Ensure-Fortis before checking the CI watcher.' }
    $lines = @(& $script:FortisContext.DockerPath top $script:FortisContainerId -eo pid,args 2>$null)
    if ($LASTEXITCODE -ne 0) { throw 'Не удалось прочитать docker top.' }
    return @($lines | Where-Object { $_ -match $script:WatcherRegex })
}

function Ensure-Watcher {
    if ($null -eq $script:FortisContext) { throw 'Run Ensure-Fortis before starting the CI watcher.' }
    foreach ($check in @(
        @('-f', '/workspace/repos/rd-graphs/tools/rdg-ci.py'),
        @('-d', $script:RdgCiRoot),
        @('-x', '/workspace/repo/Workfiles/rdg-ci-pwsh-7.6.9/pwsh')
    )) {
        $null = Invoke-FortisDockerExec -Context $script:FortisContext -Command @('test', $check[0], $check[1])
    }
    $matches = @(Get-WatcherMatches)
    if ($matches.Count -gt 1) { throw 'Уже есть несколько CI watcher. Требуется ручная проверка.' }
    if ($matches.Count -eq 1) { Write-Host 'CI watcher уже запущен; второй не создаём.' -ForegroundColor Green; return }
    $null = Invoke-FortisDockerExec -Context $script:FortisContext `
        -Options @('-d', '--workdir', '/workspace/repos/rd-graphs',
            '--env', 'DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1',
            '--env', 'RDG_TEST_PWSH=/workspace/repo/Workfiles/rdg-ci-pwsh-7.6.9/pwsh') `
        -Command @('sh', '-c', 'exec python3 -B tools/rdg-ci.py --watch >> /workspace/repo/Workfiles/rdg-ci/watch.log 2>&1')
    Start-Sleep -Seconds 2
    $matches = @(Get-WatcherMatches)
    if ($matches.Count -ne 1) { throw "Watcher не подтвердил запуск (count=$($matches.Count)); смотри watch.log." }
    Write-Host 'CI watcher: RUNNING' -ForegroundColor Green
}
