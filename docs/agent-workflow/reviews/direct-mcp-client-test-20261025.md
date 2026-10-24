# C-05: ручная проверка прямого MCP через существующий Fortis Repo

**Ручной C-05 выполнен с настоящим ChatGPT-клиентом и возвратом (PASS в ограниченном scope).** Исходные инструкции и hash guards ниже сохранены как воспроизводимый порядок, но не означают, что нужно запускать TestDirect повторно. Детальный фактический результат — в конце документа. Постоянный launcher/profile/runtime не переводились на direct; сейчас снова Bridge.

25 октября 2026 года, Asia/Bangkok. Пользователь поручил временную ручную проверку прямого подключения и возврата; после подготовки выполнил Windows AST/оба Preview, TestDirect и независимый Restore. Это не принятие постоянного удаления Bridge, сетевых правил или всей C-04.

## Что значит «прямое»

Меняется только программа MCP, запускаемая существующим Windows runtime через docker exec:

| Режим | MCP entry в том же контейнере |
| --- | --- |
| Сейчас / Restore | /usr/local/bin/node /workspace/repo/.fortis/mcp-bridge.mjs |
| TestDirect | /usr/local/bin/node /opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js |

В обоих режимах используются прежние repo-mode/profile/auth references, узкий pinned Windows runtime и тот же контейнер, UID, данные/mounts/ресурсы/сеть. Не создаются новая регистрация, профиль, ключ, Windows-учётка или контейнер; постоянные launcher/probe/profile не редактируются.

Bridge не строит Windows GUI/Observatory. Он меняет MCP presentation и **скрывает** UI-метаданные DC. В установленном server.js get_config связан с config-editor resource, read_file — с file-preview. Поэтому «делает что-то с UI» не доказывает обязательность Bridge: реальный вопрос — работает ли клиент с исходными metadata/resources без адаптера.

[Предыдущий isolated comparison](repo-network-and-mcp-bridge-20261025.md) подтвердил по26 одинаковых tools/input schemas, resources2/0 и UI tool metadata5/0. Но это ещё не Windows tunnel/ChatGPT UI acceptance.

## Граница и последствия

- Временно переподключается **общее** Fortis Repo, используемое другими чатами. Делать тест, когда нет важных активных Repo-команд: MCP terminal sessions могут оборваться.
- Docker container не останавливается. Нет команды StopContainer/docker stop или изменения Windows ACL/network/mounts.
- TestDirect/Restore меняют только текущий runtime invocation через CLI override; источник и saved profile остаются прежними. Обычные runtime/DC counters/cache могут обновляться при старте.
- Не запускается старый probe.mjs: он исполняет Bridge, пишет markers и настройки. Вместо него helper проверяет необходимые baseline constraints read-only до остановки связи.
- Runtime console stdout/stderr подавлены, чтобы не пересылать profile/doctor/payload. Ключ читает штатный runtime по прежнему reference; helper содержимое ключа не читает.
- Junction отложены; тест не обходит их и не меняет размещение проектов. Не принимаются PR-A-07/09/13 авансом.

## Состав C-05

Проверочный subset PR-A-13, WR-T01–06 и EA-T01–05 ниже. User authorization относится к временной проверке; постоянное применение — отдельная единица.

| WR | Критерий |
| --- | --- |
| WR-T01 | Тот же repo-mode/tunnel, owner alexa, pinned runtime/control, immutable container ID и прежние restrictions |
| WR-T02 | До Stop проверены protected direct module и исходный Bridge hashes, current allowed roots/shell/telemetry; неожиданный drift прекращает действие |
| WR-T03 | Останавливается только подтверждённый Repo ID/PID/creation/owner; дубликаты/неизвестная identity не останавливаются |
| WR-T04 | Через реальный клиент проверены serving process chain без Bridge, metadata, чтение известного файла и readonly terminal operation |
| WR-T05 | UI наблюдается пользователем: лишние cards/errors, file preview/config editor; настройки через UI не применяются. Cache/необновлённые metadata ограничивают вывод |
| WR-T06 | Есть независимый ручной Restore без работающего MCP; после него подтверждается прежняя цепочка. Нет постоянных config/permission changes |

| EA | Механизм и проверка |
| --- | --- |
| EA-T01 | Перепутан PID/другой туннель → остановка чужого процесса. Используется pinned controller discovery по Repo ID и fresh PID/creation/owner/exe checks |
| EA-T02 | Старый startup probe выполнен перед direct test → уже исполнен RW Bridge. Helper его не вызывает; preflight — отдельный read-only Node metadata code |
| EA-T03 | Cached metadata/старый процесс принят за direct → ложный PASS. Проверять get_config serving PID и реальную /proc parent/module chain |
| EA-T04 | UI action/feedback/onboarding меняет scope → лишние действия. Только выбранные readonly tools; не нажимать Apply/Send/feedback и не открывать предложенные внешние страницы |
| EA-T05 | После сбоя MCP нет канала отката. Mode Restore и запасные штатные Windows команды доступны локально без Repo tool access |

## Подготовленный helper и проверки кода

[Switch-RepoMcpTest.ps1](../tools/Switch-RepoMcpTest.ps1) имеет Preview (default), TestDirect и Restore. Он сверяет control/runtime hashes, Docker ID/user/readonly root/cap-drop/NNP/ресурсы/network/mounts, actual Linux flags, direct+Bridge hashes и выбранные DC config fields. Не читает raw profiles/key/env, не делает registration/doctor и не пишет конфигурацию.

Для Stop импортируется только hash-совпавший существующий controller; Menu/Start/StopContainer не вызываются. Перед новым запуском helper проверяет отсутствие lingering repo-mode process. Для обоих backend runtime работает в foreground; окно нужно оставить открытым. Mode Restore также использует временный override на прежний Bridge entry; штатный launcher остаётся нетронутым.

Inline read-only JavaScript preflight из WF-022 действительно вернул baseline PASS; marker/tools calls не выполнялись. При подготовке добавлены сверки profile PID/tunnel ID и повторная identity/owner/executable/creation непосредственно до Stop. Независимый [Restore-RepoMcpBridge.ps1](../tools/Restore-RepoMcpBridge.ps1) не вызывает switch-helper и работает из обычного локального PowerShell без MCP; он сверяет host pins, container security/mounts и Bridge hash. **Windows PowerShell AST и Windows Preview обоих файлов ещё не проведены**: их выполняет пользователь до первого TestDirect. Любая ошибка — отмена теста без обхода проверок.

### Подготовка в Windows — до любого переключения

Только **обычный не elevated** Windows PowerShell под `FORTIS_M\alexa`. Закончить важные Repo-команды в других чатах: общий runtime временно будет разорван, MCP terminal sessions могут завершиться. **Оставить этот текст и второе локальное PowerShell-окно доступными даже без MCP.** Контейнер не останавливать. Указанные ниже SHA-256 относятся только к сохранённым scripts; при несовпадении остановиться, не вычислять «новый правильный hash» автоматически. Hash guard обнаруживает drift, но файлы находятся в агент-доступном RW дереве и это не полноценная защита от гонки замены; задача C-05 — временная совместимость, не устранение F-R-05.

```powershell
& {
    $switch = 'C:\Users\alexa\Repos\tunnel\docs\agent-workflow\tools\Switch-RepoMcpTest.ps1'
    $backup = 'C:\Users\alexa\Repos\tunnel\docs\agent-workflow\tools\Restore-RepoMcpBridge.ps1'
    $files = @(
        @{ Path=$switch; Hash='DFE6BE1E1EC04924EB3650721B8361C47D80AEF7A489280CF00CCE366DE9914F' },
        @{ Path=$backup; Hash='042A98B589DD8CC098403BDD2EE57454D5881D09A8DE1572005887A818647E6A' }
    )
    foreach ($item in $files) {
        if ((Get-FileHash -LiteralPath $item.Path -Algorithm SHA256).Hash -ne $item.Hash) {
            throw "Script hash changed: $($item.Path)"
        }
        $tokens = $null; $parseErrors = $null
        [System.Management.Automation.Language.Parser]::ParseFile($item.Path, [ref]$tokens, [ref]$parseErrors) | Out-Null
        if ($null -ne $parseErrors -and $parseErrors.Count -gt 0) { throw "PowerShell AST errors in $($item.Path): $($parseErrors.Count)" }
    }
    & $switch -Mode Preview
    & $backup -Mode Preview
}
```

**Gate:** только если обе команды вывели `Preflight: PASS`, один и тот же ожидаемый Repo PID, идентичность и ограниченный container baseline, можно продолжать. `Preview` не останавливает runtime; parsing/preview подтверждает лишь локальную готовность и не заменяет actual-client test. Если нужны уточнения по ошибке — предоставить текст ошибки, не сырые Docker inspect/profile/key/logs.

### Запуск TestDirect

После успешной подготовки в первом локальном PowerShell-окне:

```powershell
& {
    $s = 'C:\Users\alexa\Repos\tunnel\docs\agent-workflow\tools\Switch-RepoMcpTest.ps1'
    if ((Get-FileHash -LiteralPath $s -Algorithm SHA256).Hash -ne 'DFE6BE1E1EC04924EB3650721B8361C47D80AEF7A489280CF00CCE366DE9914F') {
        throw 'Switch script hash changed; no switch performed.'
    }
    & $s -Mode TestDirect
}
```

Не закрывать окно с работающим runtime. После сообщения `Starting TestDirect`, если процесс не завершился с ошибкой и остался работающим, сообщить в ChatGPT **«direct запущен»**. При ошибке/завершении сообщить только её текст или exit code, без raw runtime/doctor/profile logs.

### Проверка через ChatGPT

Агент делает readonly get_config, сверяет PID/parent/module с direct path, читает небольшой фрагмент уже выданного README и запускает readonly UID/platform metadata. Пользователь сообщает о новых карточках/ошибках/preview. Никакие UI settings/apply/send не нужны.

PASS ограничен реально проверенными tool/transport/UI outcomes. Если клиентские metadata не обновились, отсутствие карточки не доказывает UI-совместимость. Если инструменты работают, но UI ломается, Bridge может быть полезен как адаптер; если direct работает достаточно, можно отдельно подготовить постоянный вариант без него.

### Возврат к прежнему Bridge

В **другом обычном локальном PowerShell** (не через MCP), после direct-проверки:

```powershell
& {
    $s = 'C:\Users\alexa\Repos\tunnel\docs\agent-workflow\tools\Switch-RepoMcpTest.ps1'
    if ((Get-FileHash -LiteralPath $s -Algorithm SHA256).Hash -ne 'DFE6BE1E1EC04924EB3650721B8361C47D80AEF7A489280CF00CCE366DE9914F') {
        throw 'Switch script hash changed; use independent recovery.'
    }
    & $s -Mode Restore
}
```

При ошибке основного helper (включая drift direct-модуля) есть **независимый** путь: файл `Restore-RepoMcpBridge.ps1` из репозитория; он не импортирует основной switch-script и требует лишь работающего локального PowerShell, Docker и исходных pinned controller/runtime/Bridge. Его `Preview` уже должен быть пройден до TestDirect.

```powershell
& {
    $s = 'C:\Users\alexa\Repos\tunnel\docs\agent-workflow\tools\Restore-RepoMcpBridge.ps1'
    if ((Get-FileHash -LiteralPath $s -Algorithm SHA256).Hash -ne '042A98B589DD8CC098403BDD2EE57454D5881D09A8DE1572005887A818647E6A') {
        throw 'Recovery script hash changed; stop and inspect.'
    }
    & $s -Mode Restore
}
```

**Использовать одну из двух команд, не обе подряд.** Восстановление только после проверки PID/creation/owner/executable и неизменного Bridge hash; при ошибке не пытаться остановить процесс вручную по одному имени, не выключать контейнер. Restore запускает прежний Bridge entry в foreground, новое окно оставить открытым. Завершение предыдущего TestDirect runtime ожидается. Если оба пути отвергают изменения fingerprints/identity, остановиться и сообщить конкретную ошибку; штатные `control.ps1`/`run-tunnel.ps1` могут выполнять startup probe с записями, поэтому **не являются безусловным обходом новых guard**.

После возобновления связи сообщить **«Bridge восстановлен»**: агент отдельно проверит настоящую serving `/proc` chain и ограниченный read-only tool smoke. Проверка только `get_config` недостаточна.

## Результат реального теста и границы доказательств — WF-024

**Пользователь (ручной Windows PowerShell):** сообщил о двух успешных `Preflight: PASS` и ожидаемых предупреждениях; показал текст `Starting TestDirect using the existing repo-mode profile`, процесс оставался работающим. При direct-сессии сообщил, что видимых изменений ChatGPT UI не заметил. Позднее сообщил, что выполнил независимый Restore; вывод команды Restore отдельно не предоставлялся, но его эффект подтверждён следующими live tool-вызовами.

**Через настоящий Fortis Repo, во время direct:** в `2026-10-24T22:47:59Z` собственный read-only Python tool command обнаружил Python → bash → `node` PID269634 (`/opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js`), UID1000, без Bridge в цепочке. Работали read_file известного `AGENTS.md`, read-only terminal operation и `get_config`: DC 0.2.52, roots `/workspace/repos`, `/workspace/files`, `/workspace/repo`, shell `/bin/bash`, telemetry=false. Metadata сами по себе не служили доказательством переключения.

**После пользовательского Restore:** в `2026-10-24T22:58:59Z` реальная chain вновь Python → bash → installed DC PID270829 → Bridge PID270817, UID1000. Известный `AGENTS.md` снова читался; Linux read-only terminal и `get_config` работали, настройки совпали с прежними. Это PASS восстановленной serving chain, а не только отображения UI.

**Ограничения:** визуальный UI outcome основан на наблюдении пользователя («вроде ничего не изменилось»); возможен кэш metadata, отдельные UI resources/actions не испытывались, поэтому полного UI PASS нет. Иные tools, длительная стабильность, изменения underlying Windows ACL/network/mounts и состояние других чатов отдельно не тестировались. Переход PR-A-13 на постоянный direct и альтернативное усиление Bridge PR-A-07 остаются pending и требуют отдельного решения. Сетевой collector не проводился; junction отложены. Сохранённые launcher/profile по плану не редактировали; проверка их файлов после теста отдельно не выполнялась.

**Итог C-05:** временный direct actual-client smoke **PASS(scope)**, независимый Restore обратно к Bridge **PASS(scope)**. Ближайший вопрос — принять ли подготовку постоянного direct PR-A-13 с startup validation/recovery или сохранить и защитить Bridge PR-A-07.
