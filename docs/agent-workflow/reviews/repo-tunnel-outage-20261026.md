# Сбой двух Fortis Repo: evidence и адресная диагностика

26.10.2026, WF-055. Это исследование текущего инцидента и предложение следующего owner-действия. Восстановление обоих подключений не подтверждено. Владелец сообщил о выполнении диагностического блока; проверочные MCP-вызовы приведены ниже. Владелец предоставил allowlist-экспорт, выполнил Preview и запустил отдельный quiet canary Repo1. Его реальные проверки приведены ниже; Repo2 и постоянный default ещё не исправлены.

## Что проверено

Пользователь сообщил об отказах обоих Repo в разных браузерных профилях и других чатах. Проверка нового чата больше не является необходимым следующим шагом. Ассистент имеет прямой инструментальный доступ только к Repo1; отказ Repo2 — сообщение владельца.

| Источник | Наблюдение | Предел |
| --- | --- | --- |
| Owner Docker inspect/cgroup | Контейнер running, paused=false, OOMKilled=true, RestartCount=0; memory.max=1073741824, pids.max=256 | Running не доказывает сохранность всех дочерних процессов |
| Owner counters и Docker event | memory.events oom=15, oom_kill=1, max=93894; event 1792957537 = 26.10 02:45:37 +07 | Жертва и причина не установлены; событие раньше runtime PID4728, запущенного в 05:11, и WARN в 05:16. Причинная связь с нынешними таймаутами не доказана |
| Повторный owner docker exec | DOCKER_EXEC_OK; pids.current=100, memory.current=634314752; oom/oom_kill/max и pids.events max=316 не выросли относительно предыдущего замера | Этот замер не показывает нового исчерпания лимитов; старый OOM не отменяет |
| Owner временный Direct stdio probe | Pin модуля проверен; initialize и tools/call(start_process с /bin/echo) вернули ответы, ECHO_OK=True, TEMP_MCP_CLOSED=True | Только новый временный MCP-процесс, protocolVersion запроса 2024-11-05. Существующий дочерний процесс Tunnel и все его вызовы не проверены |
| Инструмент ассистента через Repo1 | После запуска одно чтение AGENTS успешно; последующие запросы, включая /bin/echo без cd в bind mount, получили MCP timeout примерно через 124–126 с | Timeout не доказывает, что команда не исполнялась. Разовый read не считать восстановлением |
| Owner Windows HTTPS | /v1/models вернул HTTP401 примерно за 0.93 с без ключа | Есть общий TLS/HTTP маршрут; аутентифицированный Tunnel не проверен этим запросом |

При раннем census наблюдались три Direct Node-процесса по ~106–133 МиБ RSS/23 threads. Не установлены их владельцы/каналы; третий процесс не объявлять утечкой и не завершать по номеру из старого снимка.

## Компонентный снимок Repo1

Owner GET /health?details=true: PID2032, runtime 0.0.15+a390c168ff1b2d14e73a95991c186c6aba3ff5a0, flavor=runtime, lifecycle=running, live=true, ready=true; started_at=25.10 23:26:04.362 UTC (26.10 06:26:04.362 +07), uptime ~1552.57 с.

| Компонент | Наблюдение | Интерпретация |
| --- | --- | --- |
| mcp | stdio, child_state=running, initialize_epoch=2, evidence=same_child; initialize OK, desktop-commander 0.2.52, protocol 2025-11-25 | Успешный initialize этого поколения наблюдался в 06:30:23 +07. Это историческое protocol evidence, не свежий проверочный вызов |
| tools_list | ok=false, retained_count=0, complete=false, partial=false | В текущей эпохе не наблюдалось успешного списка. Это НЕ доказательство пустого каталога сервера |
| control-plane | polling, consecutive_failures=0, успешный poll в 06:51:28 +07; wait=30 с, deadline=35 с | Polling на момент снимка работает; возраст long poll ~29 с сам по себе нормален |
| queue | depth=0/capacity=20, enqueued=12, dequeued=12 | Локальная очередь не забита; ничего не говорит о размере hosted queue |
| dispatcher | active=0, pool_limit=10, completed=12, failures=4, timeouts=4, accepting=true | Были четыре таймаута; процесс принимает следующую работу. Последняя операция длилась примерно 119.50 с |
| response-delivery | degraded/failed/timeout; attempts=1841, retries=0, accepted=1837, completed=1837, terminal_failures=4 | Счётчики относятся к операциям отправки, включая уведомления. Это не 1837 успешных MCP-вызовов и не доказательство четырёх неудачных отправок именно финального MCP-ответа |

Последняя принятая отправка — 06:51:26.254 +07; timeout зарегистрирован в 06:51:26.384 +07. Даже близкий HTTP200 не доказывает доставку конечного результата.

## Проверочные вызовы после owner диагностического запуска

Владелец ответил «сделано» на целый guarded блок. Ассистент выполнил только два последовательных коротких вызова start_process, без параллельной нагрузки:

| Вызов | Начало, +07 | Наблюдение |
| --- | --- | --- |
| /bin/echo FORTIS_DIAG_OK | 26.10 07:14:05.788 | Успех за 12.274 с; PID48869 и ожидаемый stdout |
| /bin/echo FORTIS_DIAG_REPEAT_OK | 26.10 07:14:45.209 | MCP timeout через 124.124 с; выполнение команды и конечный ответ не подтверждены |

Воспроизведён прежний сценарий первого успешного вызова и последующего timeout. Это не восстановление. Свежий RunId/PID Runtime и наличие журнала пока не получены; следующий шаг — read-only exporter ниже, без ещё одного restart или серии MCP-вызовов. Метаданные запроса нужны до выбора исправления.

## Проверенные исходники

Предоставленный tunnel.zip — snapshot Git HEAD c06f56a2133514399e3c0e534036631c84739d44 с чужой текущей работой Checker. Для разбора использована отдельная локальная копия; Windows-установка и live Git не изменялись. Секретные профили, ключи и .git/config не читались.

1. [Repo1 PR-A-15 source](../../../runtime/host-g2/runtime-api-migration/repo-run-tunnel-two-profile-reboot.candidate.ps1): SHA256 9f3f3bad533415a21121e1f33f7f844d7d7d7a5640c6711326f4916679907483 совпал с ранее проверенным installed pin. Вызов неизменённого runtime заканчивается `*> $null`: вывод всех PowerShell streams подавляется. Две строки на скриншоте — сообщения самого launcher. Это объясняет отсутствие журнала в окне, но не устанавливает причину timeout.
2. Launcher передаёт Direct `docker exec -i ... node .../dist/index.js`; Bridge не используется. LOG_FILE/LOG_LEVEL/LOG_FORMAT/LOG_HTTP_RAW_UNSAFE в этом launcher не переопределяются. Отдельного запрета такого диагностического окружения в его исходнике нет.
3. [Repo2 guard source](../../../runtime/host-g2/runtime-api-migration/repo2-direct-guard.candidate.ps1): SHA256 88d5be54f5e651bbd658bd9f84751511f9d178061efacf4aa0f2507827cc8533 совпал с прежним installed pin. Полная installed FortisRepo2.ps1 в архиве не найдена; не объявлять её просмотренной и не менять второй launcher по предположению.
4. В upstream tunnel-client **tag v0.0.15** проверены docs/health.md, docs/configuration.md, pkg/runtimeapp/app.go, pkg/log/logger.go, pkg/controlplane/health.go, pkg/controlplane/internal/tunnel_service_client.go, pkg/dispatcher/internal/processor.go, stdio forwarding и protocol observation. Компонентные GET пассивны и доступны narrow runtime. `PostResponse` учитывает уведомления тем же DeliveryHealth, что и конечные ответы. `forwardResponses` синхронно ожидает POST очередного уведомления перед следующим чтением MCP. Повторы в owner snapshot отсутствуют.
5. В upstream DesktopCommanderMCP **tag v0.2.52**, src/custom-stdio.ts и src/index.ts проверено преобразование console/log output в `notifications/message` и воспроизведение буфера при initialized. Это механизм конкретной версии, но не наблюдение типов/содержимого фактического потока установленного процесса. Source index.ts не является хешем установленного compiled dist/index.js.

Первичные источники: [Tunnel v0.0.15 health](https://github.com/openai/tunnel-client/blob/v0.0.15/docs/health.md), [dispatcher](https://github.com/openai/tunnel-client/blob/v0.0.15/pkg/dispatcher/internal/processor.go), [response uploads](https://github.com/openai/tunnel-client/blob/v0.0.15/pkg/controlplane/internal/tunnel_service_client.go), [logger](https://github.com/openai/tunnel-client/blob/v0.0.15/pkg/log/logger.go), [DC stdio v0.2.52](https://github.com/wonderwhy-er/DesktopCommanderMCP/blob/v0.2.52/src/custom-stdio.ts), [DC startup](https://github.com/wonderwhy-er/DesktopCommanderMCP/blob/v0.2.52/src/index.ts).

## Рабочая гипотеза и следующий шаг

Поток **notifications/message подтверждён** owner-экспортом диагностического журнала runtime-diag-11405c5a54af49269cb6cc0bc4209e0e.jsonl. В окне последних 6000 строк выбранные 624 события включали 610 логовых уведомлений: req4/tools/call — 20, req5/иной method — 152, req6/initialize — 188, req8/tools/call — 250. Это разные события одного диагностического запуска; не объединять эти счётчики с более ранним health PID2032.

Последние уведомления req8 приходят перед отдельными POST с интервалами преимущественно ~0.27–0.29 с; в показанном хвосте есть ~0.44 с. Это интервал между наблюдениями, не изолированное измерение HTTP. recv конечного tools/call response: **07:17:50.8496589 +07**, delivery: **07:17:51.1392684 +07**, без JSON-RPC error. Наш повторный вызов уже получил timeout около07:16:49.333. Request aliases анонимизированы: сопоставление req8 с конкретным инструментальным request_id напрямую не установлено; последовательность и время согласуются с повторным вызовом.

Механизм избыточного логового трафика и последовательной пересылки подтверждён кодом и метаданными. Оценка порядка70с для250 таких отправок — экстраполяция хвоста, а не измерение полного интервала. Точный источник генерации логов и исключительность этой причины ещё не установлены; окончательное end-to-end подтверждение требует canary с удалением именно этого потока. Реальные ошибки JSON-RPC не отфильтровывать.

Подготовленная ограниченная операция — один диагностический перезапуск **только Repo1** с JSON debug log в существующей защищённой Windows-папке launcher, один короткий echo через ChatGPT, затем вывод строго выбранных метаданных и возврат к обычному запуску. Это не попытка исправить установленный бинарник и не обещание восстановления. Владелец выполнил предложенный блок после запроса ручных инструкций; это отдельное согласование только диагностического окна Repo1, не разрешение будущих stops/изменений. Repo2 и общий Docker вне этого stop scope. Следующий шаг — прочитать выбранные метаданные текущего журнала; запуск повторять для этого не требуется.

### Owner-команды диагностического запуска — владелец сообщил о выполнении

Обычный non-admin PowerShell под FORTIS_M\alexa. Весь блок выполняется целиком: guards должны предшествовать StopAccess. Проверки версии и hash привязаны к текущему инциденту, не являются разрешением для другой установки.

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if ($identity.Name -ine 'FORTIS_M\alexa' -or
        $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Use the existing non-admin FORTIS_M\alexa account.'
    }
    $ctl = 'C:\Users\alexa\chatgpt-repo-mode\control.ps1'
    $runner = 'C:\Users\alexa\chatgpt-repo-mode\run-tunnel.ps1'
    $runtime = 'C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe'
    $pins = @{
        $ctl = '605F9D54A0A35FF3011DC44356A733F975A8993F1225FF53378A6B7880A193C5'
        $runner = '9F3F3BAD533415A21121E1F33F7F844D7D7D7A5640C6711326F4916679907483'
        $runtime = 'A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A'
    }
    foreach ($entry in $pins.GetEnumerator()) {
        if ((Get-FileHash -LiteralPath $entry.Key -Algorithm SHA256).Hash -ine $entry.Value) {
            throw 'An installed fingerprint changed. Nothing stopped.'
        }
    }
    $before = (& $ctl -Action Status) | ConvertFrom-Json
    if (@($before.tunnel).Count -ne 1 -or -not $before.running -or
        $before.containerId -ne 'c6d7be9fe6eb4138a9dc47db3f82c32c377007c2d461c1f03ad37fe9bb3d074a') {
        throw 'Expected one Repo1 runtime and the existing running container. Nothing stopped.'
    }
    & docker exec --user 1000:1000 --workdir /workspace/repo fortis-repo-test python3 -c "from pathlib import Path; import sys; c=Path('/sys/fs/cgroup'); v=lambda n:int((c/n).read_text()); sys.exit(0 if v('memory.max')-v('memory.current')>=268435456 and v('pids.max')-v('pids.current')>=48 else 2)" 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'Resource headroom check failed. Nothing stopped.' }

    $runId = [Guid]::NewGuid().ToString('N')
    $logFile = Join-Path (Split-Path -Parent $runner) ('runtime-diag-' + $runId + '.jsonl')
    if (Test-Path -LiteralPath $logFile) { throw 'Diagnostic filename already exists.' }
    $names = @('LOG_FILE','LOG_LEVEL','LOG_FORMAT','LOG_HTTP_RAW_UNSAFE')
    $prior = @{}
    foreach ($name in $names) {
        $prior[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
    }
    try {
        & $ctl -Action StopAccess
        $stopped = (& $ctl -Action Status) | ConvertFrom-Json
        if (@($stopped.tunnel).Count -ne 0) { throw 'Repo1 is still detected. No duplicate start.' }
        $env:LOG_FILE = $logFile
        $env:LOG_LEVEL = 'debug'
        $env:LOG_FORMAT = 'json'
        $env:LOG_HTTP_RAW_UNSAFE = 'false'
        "RunId=$runId"
        'Keep this window open for one diagnostic request.'
        & "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -File $runner
        "LauncherExitCode=$LASTEXITCODE"
    }
    finally {
        foreach ($name in $names) {
            [Environment]::SetEnvironmentVariable($name, $prior[$name], 'Process')
        }
    }
}
```

Так используется прежний pinned launcher и его Direct guards. Native logging file открывается отдельно от stdout, поэтому `*> $null` не подавляет запись в файл. ENV выше действуют только в этом процессе и его дочерних процессах; после выхода блока восстанавливаются. Профили, ключи, binaries, ACL, mounts и firewall не редактируются. Существующий StopAccess может оставить Docker background processes; эта операция не очищает чужие jobs и не обещает освободить их память.

После запуска — один `/bin/echo FORTIS_DIAG_OK` через Repo1. Успех одного вызова не объявлять устойчивым восстановлением. При timeout не запускать серию новых запросов; собрать метаданные ниже.

### Вывод метаданных в другом PowerShell

Owner выполнил exporter и предоставил его метаданные. Блок сам выбирает последний runtime-diag-<32hex>.jsonl только в папке Repo1. Учитываются последние 6000 строк; выводятся выбранные события/известные methods и числовой RPC error code. Request IDs заменяются локальными req1/req2 aliases. Поля data, params, error, headers, URLs, исходные IDs и полные строки не выводятся; сырой журнал остаётся на Windows вне Docker mounts.

```powershell
& {
    $file = Get-ChildItem -LiteralPath 'C:\Users\alexa\chatgpt-repo-mode' -Filter 'runtime-diag-*.jsonl' -File -ErrorAction Stop |
        Where-Object Name -Match '^runtime-diag-[0-9a-f]{32}\.jsonl$' |
        Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
    if (-not $file) { throw 'Diagnostic log not found.' }

    $events = @{
        'dispatcher received notification from MCP server; forwarding to control plane' = 'mcp_notification'
        'dispatcher received response from MCP server' = 'mcp_response'
        'dispatcher delivered response to control plane' = 'response_delivered'
        'dispatcher acknowledged notification with control plane' = 'notification_ack'
        'context canceled while forwarding notification to control plane' = 'notification_timeout'
        'failed to forward notification to control plane; continuing to terminal response' = 'notification_failed'
        'MCP connection context canceled while delivering response' = 'response_timeout'
        'failed to post response to control plane' = 'response_failed'
        'MCP connection context canceled while reading response' = 'mcp_wait_timeout'
        'failed to read response from MCP server' = 'mcp_read_failed'
        'dispatcher posted terminal downstream error response to control plane' = 'downstream_error'
        'command response deadline reached; dropping without posting a response' = 'deadline'
    }
    $methods = @('initialize','ping','tools/list','tools/call','logging/setLevel',
        'notifications/initialized','notifications/message','notifications/progress',
        'notifications/tools/list_changed','notifications/resources/list_changed',
        'notifications/resources/updated','notifications/prompts/list_changed',
        'notifications/roots/list_changed','notifications/cancelled')
    $aliases = @{}
    $rows = @(Get-Content -LiteralPath $file.FullName -Encoding UTF8 -Tail 6000 -ErrorAction Stop | ForEach-Object {
        try { $r = $_ | ConvertFrom-Json -ErrorAction Stop } catch { return }
        $msg = [string]$r.msg
        if (-not $events.ContainsKey($msg)) { return }
        $method = 'other'
        if ($r.method -in $methods) { $method = $r.method }
        elseif ($r.rpc_method -in $methods) { $method = $r.rpc_method }
        $request = '-'
        $key = [string]$r.request_id
        if ($key) {
            if (-not $aliases.ContainsKey($key)) { $aliases[$key] = 'req' + ($aliases.Count + 1) }
            $request = $aliases[$key]
        }
        $at = [DateTimeOffset]::MinValue
        $time = $null
        if ([DateTimeOffset]::TryParse([string]$r.time, [ref]$at)) { $time = $at.ToString('o') }
        $errorCode = $null
        if ($r.rpc_error_code -is [int] -or $r.rpc_error_code -is [long]) { $errorCode = $r.rpc_error_code }
        [pscustomobject]@{
            time=$time; request=$request; event=$events[$msg]; method=$method
            has_error=($r.has_error -eq $true); error_code=$errorCode
        }
    })
    "Log=$($file.Name); selected=$($rows.Count); window=last6000lines"
    $rows | Group-Object request,event,method | Select-Object Count,Name | Format-Table -AutoSize
    $rows | Select-Object -Last 20 | ConvertTo-Json -Depth 3
}
```

Экспорт подтвердил сотни notifications/message перед ответами. После quiet canary тот же exporter проверяет исчезновение этого потока и доставку повторных вызовов. Содержимое log data/ключей для этой проверки не нужно.

### Возврат и пределы проверки

В рамках согласованного окна после получения метаданных остановить диагностический Repo1 через существующий control StopAccess с теми же hash/identity guards. Дождаться выхода его launch-окна и finally, затем использовать прежний обычный shortcut Repo1 из нового обычного PowerShell/окна. Перед новым стартом повторить headroom guard; при отказе не завершать произвольные Docker процессы. Repo2, Docker и сохранённые данные остаются вне stop scope. Никаких установленных bytes для отката нет: менялись только process ENV и создавался локальный журнал.

Launcher намеренно бросает исключение после любого завершения native Runtime. Поэтому LauncherExitCode=1 после согласованного StopAccess сам по себе не доказывает новую аварию Runtime; учитывать underlying exit code в его сообщении и собственный момент остановки.

Исторический итог WF-056: запуск диагностического блока, file log и работа exporter подтверждены владельцем; quiet canary тогда ещё не выполнялся. Последующая проверка Repo1 записана в WF-058 ниже. Raw HTTP logging и выгрузка raw log/profile не нужны. Реальные вызовы обоих Repo, включая повторный короткий вызов, остаются условием полного восстановления.

## Проверочный вариант PR-A-17 (SOURCE ONLY)

Состояние 26.10/WF-058: owner выполнил guarded copy/hash/parser/Preview и запустил side-by-side Repo1 canary без RestartRepo1, поскольку оба подключения уже остановил. **Repo1 live smoke PASS(scope)**; Repo2, постоянный default и длительная эксплуатация ещё не приняты. Команды ниже сохраняют точную процедуру; повторять их для уже работающего canary не нужно.

| Артефакт | Назначение / SHA256 |
| --- | --- |
| [quiet-log-preload.mjs](../../../runtime/repo-mode/quiet-log-preload.mjs) | Читаемые 2034 байта фильтра; a18a0d409cd1e40bcb6bbb82935a041297aec43de34c65ac26015fa1f7422eb3 |
| [repo-run-tunnel-quiet-logs.candidate.ps1](../../../runtime/host-g2/runtime-api-migration/repo-run-tunnel-quiet-logs.candidate.ps1) | Отдельная копия Repo1, default Preview, UTF-8/CRLF; adc6b15de27f845eb0fd451e63e699d711e6a18e3bd4b16d5d32943a4b4c3d4c |
| [test-quiet-log-preload.mjs](../../../runtime/repo-mode/test-quiet-log-preload.mjs) | 10 локальных Node tests; без внешних dependencies |

Политика исключает только полную одиночную JSON-RPC строку `notifications/message` без поля id. DC0.2.52 пишет такие сообщения за один stdout.write; слой ставится до запуска DC через Node --import в NODE_OPTIONS. Иные bytes/ответы/error responses/progress/tools-list changes/ID-bearing calls проходят неизменёнными. Неверные, фрагментированные и batched writes не переписываются; это намеренно узкая политика конкретного write-pattern, не универсальный stream proxy. Логовые notifications всех severity не доходят до ChatGPT; ошибки самих JSON-RPC ответов сохраняются. Это не DLP, авторизация или OS-изоляция.

Фильтр встроен в проверяемую Windows-копию как data URL; изменяемый .mjs из Docker workspace не загружается. Нет второго Bridge-процесса или новых mounts. Node argv и установленный entry/index.js остаются прежними, поэтому прежний census не теряет процесс. Прелоад удаляет **только собственное точное** значение NODE_OPTIONS до запуска development child processes. Candidate отвергает непустой исходный NODE_OPTIONS контейнера, вместо перезаписи чужой политики.

Все прежние identity/container/mount/capability/resource/DC hash/config/bootstrap guards сохранены. Canary требует warm pinned DC config; холодное восстановление не аттестуется этим изменением. После успешных проверок `-Mode Run -RestartRepo1` дополнительно требует ровно один existing Tunnel/profile и вызывает существующий pinned Stop-RepoAccess с повторной ID/PID/creation-time проверкой. После Preview return остановки нет; Preview запускает только фиксированный synthetic Node smoke с log/progress/reply и headroom guard, реальный DC не стартует. Run пишет отдельный частный JSON debug log, raw HTTP=false, с новым RunId.

**QA:** `node --test runtime/repo-mode/test-quiet-log-preload.mjs` — 10/10 PASS на локальном Linux Node24.22.1. Проверены 610 logging messages перед progress/reply, точные сохранённые bytes, error/ID/null/Unicode, callbacks/return, native argument errors, child env/execArgv, совпадение embedded bytes/hash и восстановление исходного PR-A-15 после удаления только объявленных additions. Это локальные tests; дополнительно owner Preview подтвердил synthetic probe внутри фактического Docker и Windows parser/hash checks, а live canary проверен отдельными вызовами ниже. Upstream v0.0.15 parser сохраняет запятую data URL в command tail; payload не содержит channel/URL override segments.

### 1. Только после review/согласования: отдельная копия и Preview

Скачать только candidate .ps1; читать изменение удобно по маленькому preload и diff. В обычном non-admin FORTIS_M\alexa PowerShell следующий блок копирует **новый** файл рядом со старым, сверяет SHA, снимает метку скачивания только с этой проверенной копии и проверяет Windows syntax перед Preview. Старый run-tunnel.ps1 не перезаписывается, Runtime не заменяется, профили/ключи/ACL не редактируются. ExecutionPolicy не меняется.

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    if ($identity.Name -ine 'FORTIS_M\alexa' -or
        $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Use the existing non-admin FORTIS_M\alexa account.'
    }
    $source = Read-Host 'Full path to downloaded repo-run-tunnel-quiet-logs.candidate.ps1'
    $expected = 'ADC6B15DE27F845EB0FD451E63E699D711E6A18E3BD4B16D5D32943A4B4C3D4C'
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ine $expected) {
        throw 'Downloaded candidate fingerprint mismatch.'
    }
    $target = 'C:\Users\alexa\chatgpt-repo-mode\run-tunnel-quiet-logs.ps1'
    if (Test-Path -LiteralPath $target) {
        if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ine $expected) {
            throw 'Another side-by-side candidate already exists; not overwriting.'
        }
    } else {
        Copy-Item -LiteralPath $source -Destination $target
    }
    if ((Get-Item -LiteralPath $target).Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw 'Unexpected reparse target.'
    }
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ine $expected) {
        throw 'Copied candidate fingerprint mismatch.'
    }
    Unblock-File -LiteralPath $target
    $tokens = $null; $parseErrors = $null
    $null = [System.Management.Automation.Language.Parser]::ParseFile($target, [ref]$tokens, [ref]$parseErrors)
    if (@($parseErrors).Count -ne 0) { throw 'Candidate Windows syntax check failed.' }
    & "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -File $target -Mode Preview
}
```

Owner получил Preflight=PASS, ConfigState=Pinned, LinuxUid=1000, DirectHashVerified=true, QuietPreloadProbe=PASS и ожидаемый SHA preload. ExistingTunnelCount/ExistingProfileCount=0: оба подключения к этому моменту остановлены, контейнер running/paused=false. Поэтому владелец выполнил следующий Run **без -RestartRepo1**. При ошибке остановку не выполнять и не ослаблять guards. Новый файл может остаться для review; удаление не автоматизировано.

### 2. В том же согласованном canary-окне, после Preview PASS

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $target = 'C:\Users\alexa\chatgpt-repo-mode\run-tunnel-quiet-logs.ps1'
    $expected = 'ADC6B15DE27F845EB0FD451E63E699D711E6A18E3BD4B16D5D32943A4B4C3D4C'
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ine $expected) {
        throw 'Candidate fingerprint changed; nothing stopped.'
    }
    & "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -File $target -Mode Run -RestartRepo1
}
```

Если Repo1 уже остановлен, параметр -RestartRepo1 **опустить**, как в выполненном owner запуске WF-058. Если ещё работает ровно один Repo1, этот switch разрешает guarded stop после preflight; при нуле existing процессов он намеренно отказывает. Repo2 и Docker вне scope. После Run нужны последовательные вызовы и отдельная оценка дальнейшей эксплуатации. Обычный control Start всё ещё указывает на старый run-tunnel.ps1: постоянный default не переключён.

### 3. Возврат при отказе или окончании согласованного окна

Проверить доступный headroom как в диагностическом плане выше. Затем в обычном owner PowerShell:

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $ctl = 'C:\Users\alexa\chatgpt-repo-mode\control.ps1'
    $normal = 'C:\Users\alexa\chatgpt-repo-mode\run-tunnel.ps1'
    if ((Get-FileHash -LiteralPath $ctl -Algorithm SHA256).Hash -ine '605F9D54A0A35FF3011DC44356A733F975A8993F1225FF53378A6B7880A193C5' -or
        (Get-FileHash -LiteralPath $normal -Algorithm SHA256).Hash -ine '9F3F3BAD533415A21121E1F33F7F844D7D7D7A5640C6711326F4916679907483') {
        throw 'Original recovery fingerprint changed; nothing stopped.'
    }
    & $ctl -Action StopAccess
    $state = (& $ctl -Action Status) | ConvertFrom-Json
    if (@($state.tunnel).Count -ne 0) { throw 'Repo1 still detected; not starting a duplicate.' }
    & "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -File $normal
}
```

Это возврат к прежней цепочке, не обещание исчезновения исходного timeout. Оба файла и журналы остаются, удаления/переписывания старого launcher нет. После успешного Repo1 canary отдельно получить/read-review фактический Repo2 launcher; текущий source package **не** обновляет Repo2, не меняет его профиль/guard и не закрывает F-R-12/P-10/P-11.


## WF-058: owner Preview и live Repo1 canary

Владелец сообщил «остановил все». Дополнительный owner inspect: container running, paused=false. Затем выполнен guarded copy в C:\Users\alexa\chatgpt-repo-mode\run-tunnel-quiet-logs.ps1 с ожидаемым SHA, Windows parser и Preview. Preview JSON: Preflight=PASS, ConfigState=Pinned, правильный containerId, FORTIS_M\alexa, LinuxUid1000, DirectHashVerified=true, ExistingTunnelCount=0, ExistingProfileCount=0, SavedProfileEdits=false, QuietPreloadProbe=PASS, ожидаемый preload SHA. Это owner evidence, не независимый remote Windows ACL audit.

Owner запустил -Mode Run без RestartRepo1; RunId **7027db02148f4c02a47a3da045d3c2a0**, ожидаемый canary banner. Результаты доступного Repo1 инструмента, 26.10 +07:

| Проверка | Начало | Наблюдение |
| --- | --- | --- |
| echo FORTIS_QUIET_CALL_1_OK |08:24:18.066| Успех7.390с, PID48980 |
| echo FORTIS_QUIET_CALL_2_OK |08:24:30.820| Успех8.033с, PID48982; прежний срыв второго вызова не повторился |
| Дочерний Node |08:24:47.961| Успех6.441с, PID48984; NODE_OPTIONS отсутствует, --import отсутствует в execArgv |
| read_file AGENTS.md |08:27:41.738| Успех7.521с, все21строка |
| Read-only live Git/files/cgroup |после file smoke| start_process и read_process_output успешны; HEAD c06f56a...,8 чужих tracked dirty, собственные пути соответствуют архивной базе |

Ресурсы последнего Linux snapshot: pids.current78/256, memory.current582598656/1073741824, memory.events max93894/oom15/oom_kill1 — не выросли. Это не установление жертвы прежнего OOM. Существующие другие Direct процессы не завершались ассистентом.

Live source sync завершён в commit b5e0063062a8dcd1644bb4eed8eb17d14d1d157c: девять собственных source/docs paths, точные read/staged/committed bytes, восемь чужих tracked dirty и их index/worktree сохранены. В фактическом Docker Node22.23.3 полный набор из 10 tests PASS (0 fail/cancelled/skipped). Receipt metadata: sync7132231f49aa469490fa404c624f2ef1, phase=complete. Это перенос исходников в dev Git, без push и без обновления installed Windows launcher.

**Предел PASS:** доступные command/file/output routes Repo1 в текущем canary. Новый Windows log ещё не экспортирован, поэтому фактический нулевой notification count отдельно не заявлен. Repo2 по-прежнему без quiet launcher; полного installed FortisRepo2.ps1 в архиве нет. Обычный control Start и старый shortcut ещё запускают прежний launcher; постоянный перенос требует отдельного owner шага после проверки второго. Cold boot/P-10 и security gates остаются OPEN/PENDING.


### Следующий owner read-only шаг: metadata Repo2 launcher

Выполнить в отдельном PowerShell, оставив текущий Repo1 canary открытым. Блок проверяет прежний SHA и разбирает AST установленного скрипта, не выполняя его. Вывод ограничен именами/ValidateSet параметров, номерами строк и точным известным Direct command literal; другие строковые значения, профили, ключи и private URL не выводятся. Изменение файлов, процессов и контейнера не требуется. Если старый SHA изменился или нужной статической команды нет, не применять автоматическую замену.

```powershell
$rp2 = Join-Path $env:LOCALAPPDATA 'FortisRepoPlus2\FortisRepo2.ps1'
$rp2Hash = (Get-FileHash -LiteralPath $rp2 -Algorithm SHA256).Hash
if ($rp2Hash -ne '13C1956DA1E7B7405F50B495A40225D51E42E568965A68AAFFBE404616093CDB') { throw 'Repo2 SHA changed; stop.' }
$rp2Tokens = $null; $rp2Errors = $null
$rp2Ast = [System.Management.Automation.Language.Parser]::ParseFile($rp2, [ref]$rp2Tokens, [ref]$rp2Errors)
if ($rp2Errors.Count) { throw 'Repo2 parse failed; stop.' }
$rp2Params = @($rp2Ast.ParamBlock.Parameters | ForEach-Object {
    $rp2Param = $_
    [pscustomobject]@{
        Name = $rp2Param.Name.VariablePath.UserPath
        Allowed = @($rp2Param.Attributes | Where-Object { $_.TypeName.Name -eq 'ValidateSet' } | ForEach-Object {
            $_.PositionalArguments | ForEach-Object {
                if ($_ -is [System.Management.Automation.Language.StringConstantExpressionAst] -and $_.Value -match '^[A-Za-z0-9_-]{1,40}$') { $_.Value } else { '<redacted>' }
            }
        })
    }
})
$rp2Direct = 'command=docker exec -i fortis-repo-test /usr/local/bin/node /opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js'
$rp2Literals = @($rp2Ast.FindAll({ param($n)
    $n -is [System.Management.Automation.Language.StringConstantExpressionAst] -and ($n.Value -eq $rp2Direct -or $n.Value -eq $rp2Direct.Substring(8))
}, $true) | ForEach-Object { [pscustomobject]@{ Line = $_.Extent.StartLineNumber; Command = $_.Value } })
$rp2Calls = @($rp2Ast.FindAll({ param($n)
    $n -is [System.Management.Automation.Language.CommandAst] -and $n.Extent.Text -match '--mcp|Repo2DirectGuard'
}, $true) | ForEach-Object { $_.Extent.StartLineNumber })
[pscustomobject]@{ Sha256 = $rp2Hash; Parameters = $rp2Params; DirectLiterals = $rp2Literals; BindingOrGuardLines = $rp2Calls } | ConvertTo-Json -Depth 6
```

Эти metadata нужны для следующего ограниченного patch-review; они не означают, что полное тело второго launcher уже проверено или обновлено.

### WF-059: Repo2 owner AST metadata (read-only, 26.10.2026)

Владелец выполнил WF-058 read-only PowerShell parser/metadata блок над фактическим installed `FortisRepo2.ps1`. Выход: SHA256=`13C1956DA1E7B7405F50B495A40225D51E42E568965A68AAFFBE404616093CDB` (предыдущий pin совпал), параметры: единственный `Action`, ValidateSet `Setup|Start|Status`; `DirectLiterals=[]`; `BindingOrGuardLines=[181,209,212]`. Блок не исполнял launcher, не читал ключи/профили и не останавливал процессы. Совпадение SHA относится к установленным bytes; пустой список точных literals не исключает динамическую сборку Direct-команды. Полный body всё ещё не прочитан.

**Owner follow-up, вторая структурная проекция:** `Sha256Matched=true`; строки присваиваний 146,148,153,160,161,165–170,181,188,198,199,203, все имена их target были сведены к `<other>`. Два `CommandAst` на 209/212 имеют идентичные 9 типов элементов: variable, string, string, variable, string, variable, string, expandable-string, string. Наличие expandable-string само по себе не доказывает, какой аргумент является `--mcp.command`; значение и точный binding не раскрыты. Вывод не содержал содержимого ключей, профилей или строковых значений.

**Третья owner AST-проекция (allowlist):** SHA matched; $repo2Guard присваивается на 181 и вызывается на 188; $profilePath на 198, $body на 199, $running на 203. На стр.205 есть статический элемент с desktop-commander. Стр.209: вызов $Client, стр.212: $Runtime; в обоих после литерала --mcp.command расположен ExpandableStringExpressionAst, ссылающийся на $Bridge. Следовательно, фактический MCP binding зависит от $Bridge, но это историческое имя **не доказывает** запуск legacy Bridge. Содержимое этой переменной ещё неизвестно. Структура CLI различается: последним литералом Runtime-call на 212 является --harpoon.additional-transport=, а полный смысл других скрытых аргументов не проверен.

**Следующий gate:** адресный read-only AST поиск присваивания $Bridge, классификация его строкового значения по известному Direct path/legacy marker без вывода payload и строгая форма expandable string в обоих вызовах. Не менять Repo2 и не стартовать/останавливать процессы до source review.  До такого review не изготавливать предполагаемую замену для Repo2 и не запускать `-Action Start` / `Setup` ради диагностики. Repo1 quiet canary и общий Docker не трогать. Ни Repo2 patch/apply, ни полный smoke, ни default switch не выполнены.

## WF-060: Repo2 quiet preparer — SOURCE ONLY

Owner read-only AST: SHA of installed Repo2 matches V-08 pin. Unique $Bridge assignment line24 has docker exec, Direct DC index.js and no legacy mcp-bridge.mjs/NODE_OPTIONS. ExactKnownDirect=false means that unreviewed extra Docker exec flags remain possible. Both --mcp.command bindings at Client line209 and Runtime line212 are expandable exact command=$Bridge. No raw launcher/profile/key/logs were transmitted.

Added source-only [repo2-quiet-preparer.candidate.ps1](../../../runtime/host-g2/runtime-api-migration/repo2-quiet-preparer.candidate.ps1), SHA-256 c2fb28a84aadacda4c99764827ccb8d3e01a0b0a671aa1be2d35cb6ade61d4cc (12,095 bytes). Default Mode=Preview: read-only checks exact SHA of installed Repo2, Repo2 guard and working Repo1 quiet launcher, PowerShell AST assignment and both MCP bindings, pinned container identity and nonempty pre-existing NODE_OPTIONS; reads Repo1 data-URL preload and verifies source SHA a18a0d40...; constructs and re-parses a candidate entirely in memory and calculates candidate digest. No Windows file write in Preview and neither mode runs Repo2 or stops Docker/Repo1.

Only three strict Direct Bridge forms are supported: basic docker exec -i, optional --user 1000:1000 or -u 1000:1000, followed by pinned container, node and DC entry. Unknown original exec flags fail closed. If and only if owner Preview passes, separate owner Mode=Stage may create NEW same-folder FortisRepo2-quiet-logs.ps1 via CreateNew, with no overwrite or change to the original. It modifies only the static Bridge literal to insert docker exec --env NODE_OPTIONS=--import=data:... and inserts a Start-only read-only Docker Config.Env check (fail closed). Both original command=$Bridge bindings are left unchanged. Side-by-side candidate explicitly refuses Setup to avoid modifying shortcut or saved profile. The installed source and Repo2 guard stay intact; rollback remains original launcher. The filter suppresses all-severity logging notifications but retains error responses and other RPC. It is not a security boundary.

**QA:** source static intent/allowlist checks PASS, existing preload tests were 10/10 PASS on Node22.23.3 (WF-058). NOT_RUN: Windows parser/Preview of the preparer, actual Bridge compatibility classification, candidate Stage and read-back/ACL verification, second profile live MCP calls, persistent shortcuts, cold boot. PowerShell is not installed in the Docker; static checking cannot replace Windows execution.

**Next gate:** owner verifies exact builder SHA, performs side-by-side copy into controlled Windows folder, syntax parse, then only -Mode Preview. Return sanitized JSON or failure, not installed source contents. No Stage/Start until separate review and owner decision; leave Repo1 running.
