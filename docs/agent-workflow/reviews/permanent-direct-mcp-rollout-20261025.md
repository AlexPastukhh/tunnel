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

## Штатный Start через контроллер и проверка остаточных Bridge — WF-027

**Ручные Windows-действия пользователя:** при свободных других чатах после pinned hash/Preview был выполнен `Stop-RepoAccess` и получено `STOP PASS - Direct MCP stopped; container preserved.` Затем `control.ps1 -Action Start` запустил новое PowerShell-окно с `Starting pinned direct Desktop Commander using existing repo-mode runtime.` Процесс остался в foreground. Старый launcher не восстанавливали, Windows профиль не меняли.

**Наблюдение Fortis Repo после штатного Start:** `read_file` вернул фрагмент `AGENTS.md`; `get_config` сообщил DC 0.2.52, три исходных roots, `/bin/bash`, telemetry=false. Повторный `start_process` был заблокирован системой безопасности OpenAI; поэтому терминальный smoke и tool-serving ancestry **после именно этого перезапуска** не подтверждены этим инструментом (они были проверены при более раннем прямом запуске).

**Независимый read-only Windows Docker/PID census от пользователя:** в контейнере обнаружены `direct DC` PID149 под Bridge PID137, `direct DC` PID195 под Bridge PID183 и отдельный прямой DC PID276507 (PPid=0). Слово `DIRECT` в Docker-census обозначает **исполняемый installed DC module**, а не прямое туннельное соединение: PID149/195 — дочерние процессы Bridge. Все пять на момент проверки `S (sleeping)`; PPid0 сам по себе не доказывает безопасность завершения. По безопасной read-only Windows проверке pinned controller `RepoTunnelCount=1`; действительная command line единственного Windows Repo Tunnel: `DirectEntry=True`, `BridgeEntry=False`. Полную командную строку и credentials не публиковали. **Штатный control Start и active Windows direct entry PASS(scope)**, хотя оставшиеся Bridge существуют в контейнере и не доказаны безопасными для удаления.

**Итог PR-A-13:** установленный launcher работает после штатного Stop/Start в пределах доступа к файлам/config и подтверждённого Windows direct entry. Действующий runtime **не вызывает Bridge** в командной строке. Старые PID137/149/183/195 **не удалены**; не убивать по PID без отдельной проверки идентичности, времени старта, владения другими сеансами и контролируемого плана отката. Не утверждать полного lifetime/reboot/UI-resources PASS или общей сетевой/Windows security isolation. Ранее независимый C-05 Restore PASS, но откат после *постоянной установки* не тестировали. Дальше — необязательный read-only аудит наследованных процессов и отдельное решение о cleanup/тесте backup recovery; PR-A-09 network policy и PR-A-12 junction остаются отдельными.

**Дальнейший gate:** не прерывать работающий Direct MCP ради повторения уже успешного штатного Start. F-R-05: текущий active invocation больше не зависит от mutable Bridge entry; наследованные Bridge-процессы и другие системные границы остаются отдельно.

## WF-028 — 2026-10-25: закрытие старых Windows-клиентов и очистка Bridge PASS(scope)

**Наблюдения Windows со слов пользователя:** второй Fortis Repo был открыт в отдельном профиле браузера. После его закрытия Windows Bridge docker.exe PID22520 завершился, из контейнера исчезла цепочка Bridge183 → DC195. Позднее после закрытия другого старого окна Windows docker.exe PID20428 также STOPPED; действующий Direct docker.exe PID18268 продолжил работать. Этот результат подтверждён read-only Windows PID проверкой пользователя.

**Read-only Linux:** перед очисткой оставались Bridge137 (PPid0, UID1000, startTicks 6910, stdio pipes) и его дочерний DC149 (PPid137, startTicks 6939), отдельно работающий DC276507 (PPid0, startTicks 4984095). Внутри контейнера у stdio pipes Bridge137 не обнаружены другие владельцы, но это само по себе не доказывает, что нет host-side клиентских handles; отсутствие соответствующих Windows клиентов было отдельно проверено пользователем.

**Точечная ручная остановка:** пользователь запустил guarded Windows PowerShell: старые Windows PID20428/22520 должны отсутствовать, новый direct PID18268 проверен по точному argv-модулю, в /proc идентичность Bridge137/DC149/DC276507 проверена по argv, PPid, startTicks; найден ровно один Bridge. Отправлен SIGTERM **только Bridge137**. Вывод: SIGTERM SENT - verified legacy Bridge PID 137; Direct MCP PID 276507 was not signaled. Агент не запускал Windows/G2 операции и не отправлял сигналы.

**После SIGTERM:** живой Fortis Repo read-only start_process перечислил **только один MCP-модульный процесс** DC276507 (PPid0, sleeping); Bridge137/DC149 отсутствуют. read_file успешно прочёл AGENTS.md, get_config вернул DC0.2.52, исходные roots, defaultShell и telemetry. **Очистка исторических Bridge-процессов и доступность нынешнего direct — PASS(scope).**

**Ограничения:** census отражает момент проверки, а не бессрочную гарантию или запрет второму профилю вновь запустить Bridge. Windows reboot, полный UI/tools ресурсный охват, проверка independent Restore после постоянной установки, network enforcement/ACL остались отдельными. Сохранять работающий PowerShell foreground direct, новых restart не требуется.

## PR-A-14 / WF-030 — reboot-safe startup candidate (SOURCE ONLY; Windows not installed)

25 октября 2026. После перезагрузки Windows текущий Windows direct launcher и controller сохранили SHA; контейнер fortis-repo-test был running. Но /home/node — Docker tmpfs, и DC config.json оказался со stock allowedDirectories=[], defaultShell=/bin/sh, telemetryEnabled=true вместо трёх рабочих корней, /bin/bash, false. Pinned Preview поэтому справедливо отказал. После закрытия старого MCP процесса пользователь вручную восстановил три DC settings, Preview PASS, запустил привычный ярлык. Live read_file/get_config PASS, /proc census показал один DC PID740 и ноль Bridge. Это временное recovery, не reboot-persistence PASS. Также /home/node/.gitconfig отсутствовал и Git в /workspace/repos/tunnel выдал dubious ownership: прежний mutating probe создавал global safe.directory/core.autocrlf, а direct launcher его больше не исполняет.

Подготовлен исходник runtime/host-g2/runtime-api-migration/repo-run-tunnel-reboot-safe.candidate.ps1 (CRLF, SHA256 7488b87355cdcaa86fdb9bcf143e0b09f2d6bd46769ba80a3e8857c412beae77). Основной Windows/Docker/Linux pin guard из PR-A-13 сохранён. Preview только читает, показывает ConfigState=Pinned|FactoryDefaults|Missing; при полном stock reset или отсутствии DC config выводит Preflight=REBOOT_REPAIR_REQUIRED, не пишет. Частичный/неожиданный drift — fail closed. В Run после identity/security/hash/mount checks и контроля отсутствия Windows Repo/profile sessions Node bootstrap дополнительно проверяет UID, home/config metadata и отсутствие любых запущенных MCP Bridge/DC в контейнере. Только тогда можно восстановить DC config из полного factory reset либо отсутствующего файла, без изменения прочих полей. Если /home/node/.gitconfig отсутствует, создаётся только owner-local safe.directory=/workspace/repos/tunnel и core.autocrlf=true; существующий Git config не переписывается и должен иметь ожидаемые ownership/mode/selected entries. Boot writes выполняются атомарно с последующей проверкой. Старый Bridge/probe, Docker start/stop, registration/profile edit, запись в Git-репозиторий не выполняются. Agent-writable config/ Git не являются отдельной security boundary.

Проверки SOURCE: SHA/CRLF и чтение изменения относительно PR-A-13; извлечённые Node probe/bootstrap проходят node --check; mock-тесты без записи в live /home/node: pinned DC + missing Git PASS, factory DC + missing Git PASS, missing DC + missing Git PASS, factory DC + pinned Git PASS, partial DC drift REJECTED, Git drift REJECTED, active MCP process REJECTED. PowerShell AST и Windows Preview НЕ проведены; реальная установка, cold reboot acceptance и полная модель ACL/junction пока неизвестны.

Manual gate 1, пока Direct уже работает (без остановки): из обычного не elevated PowerShell FORTIS_M/alexa проверить SHA кандидата, прежнего installed launcher (4fdc681b261cb14687dc8d1411d71d06c3cac7691cbc9beb0dd50c26a1f61a71) и control (605f9d54a0a35ff3011dc44356a733f975a8993f1225ff53378a6b7880a193c5); Parser.ParseFile candidate AST без errors; read-only candidate -Mode Preview ожидается PASS, ConfigState=Pinned, DirectHashVerified=true и counts (Tunnel=1,Profile=1). Любой drift: STOP.

Manual gate 2, только после gate 1: owner создаёт и hash/ACL-проверяет новый отдельный backup C:/Users/alexa/chatgpt-repo-mode/run-tunnel.direct.pre-reboot-bootstrap.bak.ps1; НЕ перезаписывает старый Bridge backup. Проверяет единственный действующий прямой Windows Repo Tunnel; через pinned controller Stop-RepoAccess (НЕ Docker stop), затем удостоверяется в отсутствии Windows Repo/profile. Скопировать pinned candidate из Windows Repos в installed run-tunnel.ps1; проверить read-back SHA + прежний ACL; installed -Mode Preview без живого tunnel; после PASS один Start через прежний ярлык. Проверить actual-client read_file/get_config/readonly terminal, Windows direct entry и Linux /proc ancestry. Только owner выполняет Windows операции. При ошибке вернуть старый Direct launcher из отдельного backup с PIN/ACL, а при необходимости применить документированный независимый Restore + отдельно восстановить Bridge launcher. Ничего не менять в runtime автоматически на этапе подготовки.

Завершение: будущий естественный Windows/Docker reboot должен пройти ярлыком, когда Docker Engine и тот же container уже running. Bootstrap не обходит unexpected drift, не запускает остановленный Docker container и не восстанавливает чужую/нестандартную Git config. Нужны Windows AST/Preview, пользовательское применение, новый reboot smoke; второй Fortis Repo и его Bridge — отдельная конфигурация.

## WF-031 / PR-A-15 — исправление совместимости двух Repo (только source)

25 октября 2026. Owner проверил PR-A-14 кандидата через Windows AST+Preview PASS, сделал отдельный backup установленного Direct (DIRECT BACKUP PASS), остановил только первый Tunnel и установил отредактированный staged launcher. REBOOT FIX INSTALL PASS, фактический Windows installed SHA256 **6F72642832AD692D44DE342951C7CBCB7F85250720553F724F104C6DBB77D51F** (изменён stdout sentinel PowerShell до `@($fortisBootOutput)[0]`). Работающий Windows launcher сейчас **не** старый 4fdc... .

После установки первый `Run` остановился на Docker bootstrap, поскольку во втором браузерном профиле всё ещё работал отдельный Bridge PID867 → DC PID879 в том же контейнере. Пользователь подтвердил это и закрыл второй Fortis Repo. После этого первый Repo успешно запущен штатным ярлыком: `read_file` PASS, `get_config` DC 0.2.52, три pinned roots, /bin/bash, telemetry=false, один DC PID3017 в /proc, Bridge отсутствует. После запуска Git global config `/home/node/.gitconfig` существует (UID1000, mode 0600) и содержит safe.directory=/workspace/repos/tunnel и core.autocrlf=true. Это текущий session PASS(scope), **не** проверка следующего reboot и не совместного запуска.

Причина несовместимости: PR-A-14 bootstrap проверяет отсутствие любого MCP-процесса даже когда DC config уже Pinned и править DC не нужно. Второй Repo должен иметь возможность работать одновременно. Просто пропускать весь bootstrap в Pinned нельзя: Git config после reboot отсутствует и должен восстанавливаться независимо. Поэтому подготовлен **новый SOURCE ONLY PR-A-15**, НЕ установлен в Windows: `runtime/host-g2/runtime-api-migration/repo-run-tunnel-two-profile-reboot.candidate.ps1`, SHA256 **9f3f3bad533415a21121e1f33f7f844d7d7d7a5640c6711326f4916679907483**, CRLF.

Поведение: при Pinned DC config не мутировать и не проверять отсутствие других MCP; Git file при отсутствии создавать через temp+exclusive hardlink, без перезаписи файла конкурирующим процессом; при наличии проверять user ownership/no-symlink, 0600 или 0644 и выбранные значения. Для stock/missing DC configuration guard требует отсутствие всех Bridge/DC, прежде чем править общую конфигурацию. Иначе fail closed. Независимые Windows Repo/profile duplicate и pinned identity/security/hash/mount checks сохранены. Старый Bridge/probe/Windows secrets/pins/Docker start/stop не затрагиваются.

Проверки нового source: Node --check для извлечённых probe/bootstrap PASS, CRLF и SHA. Девять изолированных mock-сценариев: pinned/missing Git, factory/missing Git, missing DC/missing Git, factory/valid Git, pinned DC+active second, pinned DC+active second+legacy Git 0644 PASS; partial DC drift, unexpected Git drift, stock reset while MCP active REJECTED. **Windows AST/Preview и установка PR-A-15 НЕ выполнены**. User должен выполнить pinned SHA+Windows AST+read-only Preview при работающем первом; затем отдельный backup текущего launcher SHA 6F7264..., controlled Stop/Install/Start и live проверка. Не перезапускать контейнер ради теста.

До миграции второго connection нужно owner-read точный Windows `Объект` второго ярлыка, профайл, расположение trusted startup и rollback. Второй остаётся закрытым до проверки; не копировать pins/установку первого вслепую. Пока оба используют общий контейнер, нет полной filesystem/process isolation; отдельный контейнер — самостоятельное решение.
