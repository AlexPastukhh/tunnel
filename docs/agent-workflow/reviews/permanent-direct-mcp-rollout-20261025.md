# PR-A-13: установка прямого MCP entry — live smoke PASS(scope)

25 октября 2026, Asia/Bangkok. После [C-05](direct-mcp-client-test-20261025.md) пользователь вручную выполнил Windows AST/Preview, backup исходного launcher, остановку общего Repo, установку кандидата и Run. **Новый direct сервер фактически обслуживает ChatGPT: live smoke PASS(scope).** Подробные доказательства и ограничения — в разделе WF-026 ниже. Инструкции подготовки и аварийного возврата сохранены для воспроизводимости, **не повторять Stop/Install на уже работающем direct**.

## Выбранный узкий кандидат

[Source launcher](../../../runtime/host-g2/runtime-api-migration/repo-run-tunnel-direct.candidate.ps1) заменяет только установленный `C:\Users\alexa\chatgpt-repo-mode\run-tunnel.ps1` после ручного owner-controlled deployment. Существующий `control.ps1` по Start уже ссылается на этот filename. Новый launcher использует pinned `C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe`, saved `repo-mode` и прежний runtime-key reference. Entry: `docker exec -i fortis-repo-test /usr/local/bin/node /opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js`.

В отличие от старого `probe.mjs` кандидат проверяет container ID, user/privileges/cgroups/mounts/network, Linux UID/capabilities/NNP/seccomp/RO-root, installed DC module hash, allowed roots/defaultShell/telemetry **read-only**. При drift — fail closed, без автоматически исполняемого Bridge, marker-тестов, Git/DC config writes, network/ACL/mount changes и container start/stop. `-Mode Preview` делает проверки без запуска runtime; без параметров `Run`, совместим с нынешним `control.ps1 -Action Start`. Не стартует, если виден уже запущенный Repo tunnel/profile process.

**Baseline:** исходный установленный launcher был ранее подтверждён ручным Windows hash `52848cda49fecb4d78589e9979781a28d114a92f694cf75bc66ea6d4412eb93b`; control `605f9d54a0a35ff3011dc44356a733f975a8993f1225ff53378a6b7880a193c5`; runtime EXE `A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A`. Последние Windows значения перед новой установкой нужно перепроверить. Пин кандидата — см. ниже после source Git фиксации (замены без обновления пина запрещены).

## Разрешения и ограничения

- Исходник `runtime/` — **копия для ручной установки**, не действующая Windows-конфигурация. Linux Repo не меняет локальные Windows launcher/profile, контейнер, runtime, службы, ACL или сеть; push отдельно.
- Не трогать другие подключённые чаты, пока идёт обычная работа. При будущем ручном Stop/Start общий Repo на время отключится; MCP terminal sessions могут оборваться. `docker stop` / `StopContainer` запрещены.
- Установленный `run-tunnel.ps1` и backup должны находиться **вне** агент-доступных Repos/Workfiles. Корни Repos содержат потенциальные junction: без независимого Windows проверки нельзя гарантировать, что доступ к одному пути означает недоступность всех aliases.
- Hash guard помогает выявлять drift/ошибки, но не является аппаратной аттестацией и сам не устраняет Windows F-R-07 или RW roots; кэшированный UI metadata не даёт доказательства всей совместимости.
- Отказ от старого probe означает также отказ от его автозапуска контейнера, Git safe.directory/core.autocrlf настройки и DC config repair. Уже установленный профиль/контейнер должны пройти новые проверки, а если нет — остановиться и согласовать отдельную настройку. Это сознательный fail-closed tradeoff, а не готовая замена всех административных функций probe.

## Первый Windows gate — пока ничего не переключать

Открыть обычный **не elevated** Windows PowerShell от `FORTIS_M\alexa`. Проверить ожидаемые fingerprints, парсер и два источника. Код здесь read-only; при любой ошибке остановиться, **не обновлять hash автоматически**.

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $src = 'C:\Users\alexa\Repos\tunnel\runtime\host-g2\runtime-api-migration\repo-run-tunnel-direct.candidate.ps1'
    $installed = 'C:\Users\alexa\chatgpt-repo-mode\run-tunnel.ps1'
    $control = 'C:\Users\alexa\chatgpt-repo-mode\control.ps1'
    $expected = @(
        @{ File = $src; Sha = '4FDC681B261CB14687DC8D1411D71D06C3CAC7691CBC9BEB0DD50C26A1F61A71' },
        @{ File = $installed; Sha = '52848CDA49FECB4D78589E9979781A28D114A92F694CF75BC66EA6D4412EB93B' },
        @{ File = $control; Sha = '605F9D54A0A35FF3011DC44356A733F975A8993F1225FF53378A6B7880A193C5' }
    )
    foreach ($x in $expected) {
        if ((Get-FileHash -LiteralPath $x.File -Algorithm SHA256).Hash -ne $x.Sha) {
            throw "Hash guard rejected: $($x.File)"
        }
    }
    $tokens=$null; $parseErrors=$null
    [System.Management.Automation.Language.Parser]::ParseFile($src,[ref]$tokens,[ref]$parseErrors) | Out-Null
    if ($null -ne $parseErrors -and $parseErrors.Count -ne 0) { throw 'Candidate Windows AST rejected.' }
    & $src -Mode Preview
}
```

**Gate:** ожидается JSON `Preflight: PASS` с прежним container ID и `DirectHashVerified: true`, пока Bridge работает. Если `ExistingTunnelCount` или `ExistingProfileCount` не соответствует наблюдаемой ситуации, сначала разбираться, не переключаться. Исполнение реального постоянного перехода — отдельный ручной этап после этого результата.

## Ручная установка (НЕ исполнять на стадии подготовки)

1. Закончить важные Repo-команды и открыть **второе локальное PowerShell-окно** с доступной [независимой командой Restore](../tools/Restore-RepoMcpBridge.ps1). Держать оба окна и этот текст доступными без MCP. Backup исходного launcher — один файл в `C:\Users\alexa\chatgpt-repo-mode`, не в Repo.
2. Установку выполнять только под `FORTIS_M\alexa`, если Windows hash guards повторно подтвердились. Сначала записать резервную копию прежнего `run-tunnel.ps1` под новым фиксированным именем `run-tunnel.bridge.pre-direct.bak.ps1`, проверив ее исходный SHA. Если уже существует — STOP, не перезаписывать.
3. Через hash-проверенный `control.ps1`, импортированный dot-source, вызвать только `Stop-RepoAccess` и остановить идентифицированный Repo tunnel. **Контейнер не останавливать.** Если Repo не остановился или процесс неузнаваемый — STOP.
4. Копировать pinned candidate в штатный `run-tunnel.ps1` и повторно сверить hash установленного файла. `& $installed -Mode Preview` обязан пройти. При отказе немедленно вернуть original launcher из backup, не обходя ошибку.
5. Только после PASS запустить штатный `& $installed` в foreground или `control.ps1 -Action Start`, но **не оба**. Проверить настоящий serving ancestry без Bridge, read_file, readonly terminal и UI с учётом кэша. На ошибке использовать независимый Restore и вернуть исходный launcher из backup; только затем считать предыдущий baseline восстановленным.
6. Длительное наблюдение / полный UI/resource coverage / maintenance и новая точка восстановления — отдельные gates до объявления PR-A-13 окончательно применённым. `PR-A-07` остаётся альтернативой, не внедряется автоматически.

### Точные команды будущего ручного применения (НЕ запускать до Windows Preview PASS)

На этапе выполнения нужны две обычные локальные PowerShell-сессии. В одной остаются этот текст и аварийная команда, другая используется для установки. **Осторожно: следующий блок остановит общее Repo-подключение.**

```powershell
& {
    $ErrorActionPreference = 'Stop'
    $src='C:\Users\alexa\Repos\tunnel\runtime\host-g2\runtime-api-migration\repo-run-tunnel-direct.candidate.ps1'
    $root='C:\Users\alexa\chatgpt-repo-mode'
    $installed=Join-Path $root 'run-tunnel.ps1'
    $backup=Join-Path $root 'run-tunnel.bridge.pre-direct.bak.ps1'
    $control=Join-Path $root 'control.ps1'
    $oldHash='52848CDA49FECB4D78589E9979781A28D114A92F694CF75BC66EA6D4412EB93B'
    $newHash='4FDC681B261CB14687DC8D1411D71D06C3CAC7691CBC9BEB0DD50C26A1F61A71'
    if ((Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash -ne $newHash -or
        (Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash -ne $oldHash -or
        (Get-FileHash -LiteralPath $control -Algorithm SHA256).Hash -ne '605F9D54A0A35FF3011DC44356A733F975A8993F1225FF53378A6B7880A193C5') {
        throw 'Pre-install fingerprint drift; no switch.'
    }
    if (Test-Path -LiteralPath $backup) { throw 'Existing backup; do not overwrite.' }
    $originalAcl = (Get-Acl -LiteralPath $installed).Sddl
    $pre = & $src -Mode Preview | ConvertFrom-Json
    if ($pre.Preflight -ne 'PASS' -or $pre.ExistingTunnelCount -ne 1 -or $pre.ExistingProfileCount -ne 1) {
        throw 'Expected one existing Repo session before stop.'
    }
    Copy-Item -LiteralPath $installed -Destination $backup -ErrorAction Stop
    if ((Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash -ne $oldHash) {
        throw 'Backup verification failed; no switch.'
    }
    . $control
    $null = Stop-RepoAccess
    Start-Sleep -Seconds 1
    $stopped = & $src -Mode Preview | ConvertFrom-Json
    if ($stopped.Preflight -ne 'PASS' -or $stopped.ExistingTunnelCount -ne 0 -or $stopped.ExistingProfileCount -ne 0) {
        throw 'Repo did not stop cleanly. Original launcher remains installed.'
    }
    Copy-Item -LiteralPath $src -Destination $installed -Force
    if ((Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash -ne $newHash -or
        (Get-Acl -LiteralPath $installed).Sddl -ne $originalAcl) {
        throw 'Installed direct launcher fingerprint/ACL mismatch. Restore from backup.'
    }
    $installedPreview = & $installed -Mode Preview | ConvertFrom-Json
    if ($installedPreview.Preflight -ne 'PASS' -or $installedPreview.ExistingProfileCount -ne 0) {
        throw 'Installed candidate Preview failed. Restore from backup.'
    }
    'Candidate installed but not started. Launch with the next separate command.'
}
```

Только если эта команда завершилась без ошибок и пользователь готов проверять live client, запустить **в том же обычном Windows PowerShell**, не через MCP:

```powershell
& {
    $s='C:\Users\alexa\chatgpt-repo-mode\run-tunnel.ps1'
    if ((Get-FileHash -LiteralPath $s -Algorithm SHA256).Hash -ne '4FDC681B261CB14687DC8D1411D71D06C3CAC7691CBC9BEB0DD50C26A1F61A71') {
        throw 'Installed direct launcher version differs.'
    }
    & $s -Mode Run
}
```

Окно с запущенным процессом оставить открытым. В ChatGPT проверить действительную direct ancestry и доступные tools, затем визуальные UI outcomes. В следующих обычных стартах `control.ps1 -Action Start` запустит этот же установленный launcher. Новый startup guard не запускает контейнер, если тот остановлен: это намеренный отказ, а не приглашение дать агенту Docker control.

### Действия при аварии

Если непосредственный `Run` отказал или ChatGPT потерял Repo, выполнить `Restore-RepoMcpBridge.ps1 -Mode Restore` во втором обычном Windows PowerShell с сохранённым SHA guard из [C-05](direct-mcp-client-test-20261025.md). Он не зависит от нового launcher. После восстановления Bridge отдельным контролируемым действием скопировать `run-tunnel.bridge.pre-direct.bak.ps1` обратно в `run-tunnel.ps1` с обязательной проверкой старого hash. Для второго шага в локальном PowerShell, **когда прежний Bridge уже восстановлен независимым helper**:

```powershell
& {
    $ErrorActionPreference='Stop'
    $root='C:\Users\alexa\chatgpt-repo-mode'
    $installed=Join-Path $root 'run-tunnel.ps1'
    $backup=Join-Path $root 'run-tunnel.bridge.pre-direct.bak.ps1'
    $old='52848CDA49FECB4D78589E9979781A28D114A92F694CF75BC66EA6D4412EB93B'
    $new='4FDC681B261CB14687DC8D1411D71D06C3CAC7691CBC9BEB0DD50C26A1F61A71'
    if ((Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash -ne $old -or
        (Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash -ne $new) {
        throw 'Backup or installed launcher drift; do not overwrite.'
    }
    Copy-Item -LiteralPath $backup -Destination $installed -Force
    if ((Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash -ne $old) {
        throw 'Original launcher restoration failed.'
    }
    'Original Bridge startup file restored; keep currently running Bridge open.'
}
```

Если установка оборвалась **до копирования** нового launcher, проверка installed hash должна вернуть прежний hash; не выполнять этот блок повторно «на всякий случай». **Временное восстановление MCP через Bridge само по себе не возвращает файл постоянного launcher.** При несовпадении identity/pins не завершать неизвестные процессы по имени и не обходить guard.

## Реальная Windows установка и direct actual-client smoke — WF-026

**Пользователь:** сообщил PASS для Windows hash/AST/Preview кандидата, затем выполнил резервную копию Bridge launcher с контролем SHA, сообщил STOP PASS после guarded Stop и INSTALL PASS после pinned copy/ACL/read-back/Preview. После запуска `Run` сообщил «сделал». Консольный вывод самого Run и Windows installed-file hash после запуска отдельно не предоставлялись; утверждение об установленной версии опирается на сообщение пользователя об успешном INSTALL PASS.

**Live Fortis Repo:** в `2026-10-24T23:31:55Z` read-only terminal-команда выполнилась из настоящего клиента. Собственная `/proc` process ancestry: Python → bash → **installed DC node PID275748**, аргумент `/opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js`, UID1000, **без Bridge**. `read_file` прочёл начало `/workspace/repos/tunnel/AGENTS.md`. `get_config` вернул DC `0.2.52`, allowedDirectories `/workspace/repos`, `/workspace/files`, `/workspace/repo`, defaultShell `/bin/bash`, telemetry=false. Доказательство переключения — именно ancestry, а не только `get_config`/UI.

**Итог:** PR-A-13 direct entry **установлен пользователем по проверенному сценарию и работает сейчас (PASS(scope))**; прежний Bridge launcher сохранён владельцем в `run-tunnel.bridge.pre-direct.bak.ps1`. Это не полная Windows runtime attestation и не security PASS: новую startup-конфигурацию **не проверяли после перезапуска Windows/обычного control Start**, альтернативную аварийную процедуру *после* постоянной установки ещё не запускали (ранее C-05 Restore PASS); не проверяли полный UI/resources и все 26 tools, совместную работу других чатов, сетевую изоляцию, все Windows aliases/ACL или долговременную стабильность. Старые shutdown/startup команды не повторять на работающем Repo без необходимости. Текущее PowerShell окно с Run сохранять открытым; не запускать второй Tunnel.

**Дополнительная пользовательская проверка ChatGPT UI:** после фактического PR-A-13 Run пользователь сообщил «нормально все». Это **визуальный UI PASS(scope) по сообщению пользователя**, не проверка списка ресурсов/всех UI actions, недопущения metadata cache или долгосрочной работы. Ошибок интерфейса пользователь не наблюдал.

**Дальнейший gate:** позднее при отдельно согласованном обслуживании проверить штатный restart через `control.ps1 -Action Start` и независимый Restore/launcher rollback (без ненужного нарушения работы других чатов). F-R-05 — узкая эксплуатация mutable Bridge entry на текущем serving-path устранена; все остальные границы защиты и Windows tool ACL остаются отдельными. Сетевой enforcement PR-A-09 и junction PR-A-12 отдельно.
