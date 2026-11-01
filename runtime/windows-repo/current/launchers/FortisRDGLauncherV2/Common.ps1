# Fortis/RDG launcher v2. Windows PowerShell 5.1; user's interactive account.
$ErrorActionPreference = 'Stop'
$script:FortisName = 'fortis-repo-test'
$script:FortisImageId = 'sha256:2c84fabebb34265e53b020f21a11683a4c68cbb41a08f5f11f9b01c7de5ed8c9'
$script:GuardPath = Join-Path $PSScriptRoot '..\FortisRepoPlus2\Repo2DirectGuard.ps1'
$script:UpdaterPath = Join-Path $env:LOCALAPPDATA 'RDG-Server\cicd-bootstrap-ci-20261029t051843803595-4546c7d69e\files\RDG-CICD-Bootstrap\Update-RDG.ps1'
$script:RdgCiRoot = '/workspace/repo/Workfiles/rdg-ci'
$script:ExpectedMounts = @{ '/workspace/repo' = ''; '/workspace/repos' = 'Repos'; '/workspace/files' = 'Workfiles' }
$script:WatcherRegex = 'python3(?:\.\d+)?\s+-B\s+tools/rdg-ci\.py\s+--watch(?:\s|$)'

function Assert-Docker {
    if (-not (Get-Command docker.exe -ErrorAction SilentlyContinue)) { throw 'docker.exe не найден.' }
    $out = @(& docker.exe info --format '{{.ServerVersion}}' 2>$null)
    if ($LASTEXITCODE -ne 0 -or $out.Count -eq 0) { throw 'Docker Engine недоступен. Запусти Docker Desktop.' }
}

function Get-FortisInfo {
    $raw = @(& docker.exe inspect --type container $script:FortisName 2>$null)
    if ($LASTEXITCODE -ne 0 -or $raw.Count -eq 0) { throw 'fortis-repo-test отсутствует. Контейнер не создаётся автоматически.' }
    $info = @(($raw -join "`n") | ConvertFrom-Json)[0]
    if ($info.Name -cne '/fortis-repo-test') { throw 'Неожиданное имя контейнера.' }
    return $info
}

function Assert-FortisSecurity($info) {
    if ($info.Image -cne $script:FortisImageId -or
        $info.Config.User -cne '1000:1000' -or
        $info.Config.WorkingDir -cne '/workspace/repos' -or
        -not $info.HostConfig.ReadonlyRootfs -or $info.HostConfig.Privileged -or
        @($info.HostConfig.CapDrop) -notcontains 'ALL' -or
        @($info.HostConfig.SecurityOpt) -notcontains 'no-new-privileges' -or
        ([long]$info.HostConfig.Memory -lt 4294967296 -or [long]$info.HostConfig.Memory -gt 8589934592) -or
        $info.HostConfig.NanoCpus -ne 2000000000 -or
        ([long]$info.HostConfig.PidsLimit -lt 256 -or [long]$info.HostConfig.PidsLimit -gt 1024)) {
        throw 'Изменились ограничения безопасности или образ Fortis; ничего не запускаем.'
    }
    $mounts = @($info.HostConfig.Mounts)
    if ($mounts.Count -ne 3) { throw 'Ожидались ровно 3 Mounts Fortis.' }
    foreach ($dest in $script:ExpectedMounts.Keys) {
        $m = @($mounts | Where-Object { $_.Target -ceq $dest })
        if ($m.Count -ne 1 -or $m[0].Type -cne 'volume' -or
            $m[0].Source -cne 'fortis-repo-workspace' -or $m[0].ReadOnly -eq $true -or
            [string]$m[0].VolumeOptions.Subpath -cne $script:ExpectedMounts[$dest]) {
            throw "Неверный Mount: $dest"
        }
    }
    if ($info.HostConfig.NetworkMode -cne 'fortis-repo-egress') { throw 'Неожиданный NetworkMode Fortis.' }
    $networks = @($info.NetworkSettings.Networks.PSObject.Properties.Name)
    if ($networks -cnotcontains 'fortis-repo-egress' -or
        @($networks | Where-Object { $_ -cne 'fortis-repo-egress' -and $_ -cne 'rdg-personal_agents' }).Count -gt 0) {
        throw 'Неожиданная сеть Fortis.'
    }
}

function Ensure-Fortis {
    param([switch]$DontStart)
    Assert-Docker
    $info = Get-FortisInfo
    Assert-FortisSecurity $info
    if (-not $info.State.Running) {
        if ($DontStart) { throw 'Fortis остановлен; автоматическая проверка не запускает его принудительно.' }
        Write-Host 'Запускаем существующий контейнер fortis-repo-test...' -ForegroundColor Yellow
        & docker.exe start $script:FortisName | Out-Host
        if ($LASTEXITCODE -ne 0) { throw 'Docker start Fortis завершился с ошибкой.' }
        $info = Get-FortisInfo
        Assert-FortisSecurity $info
        if (-not $info.State.Running) { throw 'Fortis не запустился.' }
    }
    if (-not (Test-Path -LiteralPath $script:GuardPath -PathType Leaf)) { throw 'Нет Repo2DirectGuard.ps1.' }
    $previewRaw = @(& $script:GuardPath -Mode Preview)
    $preview = ($previewRaw -join "`n") | ConvertFrom-Json
    if ($preview.Preflight -eq 'REBOOT_REPAIR_REQUIRED' -and
        $preview.ConfigState -in @('Missing','FactoryDefaults') -and
        $preview.ContainerIdMatched -eq $true -and $preview.DirectModuleHashVerified -eq $true) {
        Write-Host 'Восстанавливаем tmpfs-конфигурацию Desktop Commander через Guard...' -ForegroundColor Yellow
        & $script:GuardPath -Mode Run | Out-Host
        $previewRaw = @(& $script:GuardPath -Mode Preview)
        $preview = ($previewRaw -join "`n") | ConvertFrom-Json
    }
    if ($preview.Preflight -ne 'PASS' -or $preview.ConfigState -ne 'Pinned' -or
        $preview.ContainerIdMatched -ne $true -or $preview.DirectModuleHashVerified -ne $true) {
        throw "Fortis Guard: $($preview.Preflight); config=$($preview.ConfigState)."
    }
    Write-Host 'FORTIS GUARD: PASS' -ForegroundColor Green
    return [string]$info.Id
}

function Get-WatcherMatches {
    $lines = @(& docker.exe top $script:FortisName -eo pid,args 2>$null)
    if ($LASTEXITCODE -ne 0) { throw 'Не удалось прочитать docker top.' }
    return @($lines | Where-Object { $_ -match $script:WatcherRegex })
}

function Ensure-Watcher {
    foreach ($check in @(
        @('-f', '/workspace/repos/rd-graphs/tools/rdg-ci.py'),
        @('-d', $script:RdgCiRoot),
        @('-x', '/workspace/repo/Workfiles/rdg-ci-pwsh-7.6.9/pwsh')
    )) {
        & docker.exe exec $script:FortisName test $check[0] $check[1]
        if ($LASTEXITCODE -ne 0) { throw "CI-файл/каталог недоступен: $($check[1])" }
    }
    $matches = @(Get-WatcherMatches)
    if ($matches.Count -gt 1) { throw 'Уже есть несколько CI watcher. Требуется ручная проверка.' }
    if ($matches.Count -eq 1) { Write-Host 'CI watcher уже запущен; второй не создаём.' -ForegroundColor Green; return }
    & docker.exe exec -d --workdir /workspace/repos/rd-graphs `
        --env DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 `
        --env RDG_TEST_PWSH=/workspace/repo/Workfiles/rdg-ci-pwsh-7.6.9/pwsh `
        $script:FortisName sh -c 'exec python3 -B tools/rdg-ci.py --watch >> /workspace/repo/Workfiles/rdg-ci/watch.log 2>&1'
    if ($LASTEXITCODE -ne 0) { throw 'Не удалось запустить CI watcher.' }
    Start-Sleep -Seconds 2
    $matches = @(Get-WatcherMatches)
    if ($matches.Count -ne 1) { throw "Watcher не подтвердил запуск (count=$($matches.Count)); смотри watch.log." }
    Write-Host 'CI watcher: RUNNING' -ForegroundColor Green
}
