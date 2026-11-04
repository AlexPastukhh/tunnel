# E42 — начальный scope G2, приёмка и порядок работы

> **HISTORICAL SNAPSHOT — 2026-10-16.** Это scope/runbook старого G2 этапа. Mount и runtime assumptions не являются текущей картой Fortis Repo на 2026-11-03; актуальные mounts и trust boundaries описаны в `/workspace/repos/fortis-container/docs/`.

16 октября 2026. **Scope принят; old HOST остановлен, after-check выполнен E43.**
[Фактический итог E43](G3_G2_SCOPE_ACCEPTANCE_AND_HOST_RETIREMENT_2026-10-16.md).
[JSON](G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.json) ·
[Канонический план](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md).

Этот документ конкретизирует принятый E41/P01 → E42/P01. G3 bounded baseline ACCEPTED(scope); G4 initial Workspace policy ACCEPTED(scope); G5 полная personal-security программа не принята; G6 manual daily/normal recovery ACCEPTED(scope). Whole-chat1.4 PENDING; universal PASS не заявляется. Исторические runbooks и PID ниже по ссылкам не заменяют эту
инструкцию для текущего guest-session entry.

## Принятый начальный scope — E42/P01, решение E43

Использовать существующий G2 как Windows-инструмент под FortisHostG1, обычным SID1009,
в его собственной интерактивной Windows-сессии. Fortis Repo остаётся основной средой разработки.
Прежний owner HOST выведен по согласованию E43; локальное восстановление сохранено.

| Область | Начальный рабочий scope |
|---|---|
| Проекты и результаты G2 | Основной каталог: C:\Users\FortisHostG1\AppData\Local\FortisHostG2\Workspace. Для начала не нужны новые grants к owner-каталогам |
| CLI и приложения | PowerShell, Python, Node, Git, необходимые установленные программы в пределах действующих Windows-прав |
| Собственная GUI | Разрешены свои окна, экран и clipboard, собственный Edge/CDP. Не вводится требование headless |
| Собственное состояние | Рабочие browser profiles, cache, результаты, собственные scoped credentials и необходимые AppData/Temp разрешены по задаче. Их не удаляют ради самого факта очистки |
| Сеть | Интернет, собственные локальные servers/CDP разрешены по задаче; права к чужим API от этого не появляются |
| Общие tools | C:\Tools\tunnel-client, C:\Tools\desktop-commander-runtime, C:\Tools\desktop-commander доступны в проверенном read/execute scope. Проверенные mutation rights закрыты E26/E32 |
| Защищаемая область | Вся owner GUI/clipboard, включая обычные окна без elevation; owner credentials/private data, runtime и управляющие интерфейсы |
| Работа с owner-проектом | Repo работает с уже разрешёнными mounts. Если именно G2 нужен новый путь — сначала конкретная задача и минимальный grant. Общий доступ к Windows-диску не подразумевается |

G2 работает с тем же компьютером, но не получает автоматически все права alexa к его файлам.
Рабочие операции G2 ограничиваются его Windows token/ACL и согласованной задачей.
Desktop Commander allowedDirectories — guardrail файловых MCP tools, а не OS sandbox для всего shell.
Gate убирает лишние переменные среды; он не является защитой от другого процесса с тем же SID.

Приняты доказанные границы в их scopes с сохранёнными ограничениями ниже.
Это не утверждение, что неизвестных обходов вообще не существует, и не ослабление цели защиты owner.

## Какие доказательства уже достаточны и чего они не доказывают

| Свойство | Имеющееся evidence | Предел |
|---|---|---|
| Полезная работа | E18/E19: native MCP/file/CLI, source iteration, synthetic local Git; E20: browser DOM/storage; E22: own clipboard roundtrip | Не проверены все будущие программы, Git remote/auth и новые проекты |
| Owner GUI | E21: четыре fresh-open station rights DENY5; desktop paths blocked at station root. E22: выбранные owner DUP_HANDLE DENY; E24: обычное межсессионное наследование не поддерживается | Это не индивидуальная проверка DACL каждого desktop и не доказательство отсутствия всех переданных handles |
| Runtime и namespaces | E26/E31/E32: read positives, mutation DENY и synthetic/selected real-object alternate paths | Не универсальная модель всех junction/SMB/IPC |
| Owner assets | E40: семь конкретных файлов и два backup parents,130 normal/C$ opens DENY5 | Не все личные файлы, credentials и backup носители |
| Broker | E41: известные queue/control/parent paths,78 DENY5; installed worker hash совпал | Не полный аудит Bridge, permits и любых посредников. Независимый Repo сохраняет свой разрешённый маршрут |
| Services | E03/E30/E41: standard dangerous controls DENY; matching MySQL source custom handler сообщает статус | Installed-source binding неполон; ALLOW custom control сам по себе не доказывает выполнение команд |
| API Repo | E38: narrow runtime/MCP/control; selected guest admin GET404. E35: scoped stdio read-surface review | Не закрывает прежний full owner HOST. Health/metrics намеренно сохранены |
| Ручной цикл | E20/E28: reboot/manual start, обычные stop/restart, old chain/listener gone; E29: один synthetic peer failure | Не все crash/logoff/произвольные descendants. Exit0 runtime не равен успешности MCP-задачи |
| Монитор | E39:11 tests и actual Windows automatic discovery UP/initialized | Source collector проверен; старая installed панель и постоянное хранение журналов не доставлены |

Остаются184 PSS entries без type names, relative desktop names, неполная проверка clipboard
bridges и source/binary binding selected services. Их фиксируем как Evidence Limitations;
новая конкретная существенная поверхность требует адресной проверки до расширения scope.
Полный scan/fuzzing и повтор достаточных тестов не назначаются автоматически.

**Граница чата:** независимый Repo имеет RW Windows mounts; другие инструменты сохраняют свои
полномочия. Изолированный G2 не делает весь чат изолированным. Остановка прежнего HOST закрывает
конкретный широкий owner route, но не отзывает доступ Repo и не удаляет чаты.
Общий пункт1.4 остаётся отдельным. Нельзя принимать универсальную защиту owner от всех доступных
чатов по одним тестам G2.

## Свежая сверка версии без повторения security-тестов

В01:19:06Z (08:19:06 Asia/Bangkok) actual G2 MCP выполнил read-only CLI:
SID1009, no Administrators group, Session2, Win32NT.
Node32272 → Python18956 → runtime25920; даты создания совпали с E28.
Все три процесса имеют SID1009/Session2; EXE hashes совпали с проверенными.
Profile и Workspace существуют; содержимое профиля не читалось.
Операций GUI/clipboard, launch/stop/restart не было.

| Артефакт | SHA256 |
|---|---|
| Public guest entry,10355bytes | 0638D14A92F78006526281BEC98C391FAD96F6C0F3F70D9C02475DA3A56C481D |
| Gate,2564bytes | 146E60B028276F871353A113571306002942461F0446E519A63B28DCC068418D |
| Runtime v0.0.15 | A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A |
| Python3.13 | 31FE10B4ED82A2F960AF0EF9931F46A4B84FF286F8B6FFD9DEE098CF4F10F17F |
| Node | 2FFE3ACC0458FDDE999F50D11809BBE7C9B7EF204DCF17094E325D26ACE101D8 |

Desktop Commander0.2.52, defaultShell powershell.exe,33 blockedCommands.
allowedDirectories: Workspace и три C:\Tools каталога из scope выше; конфигурация не менялась.
Session/PID/ports — датированный срез. После нового входа их сверяют, а не требуют прежние номера.

## Ежедневный запуск G2

Сейчас G2 уже работает; эту последовательность повторять не нужно.

1. После reboot или обычной остановки войти в Windows как FortisHostG1. Нужен отдельный login:
   PowerShell «от другого пользователя» в сессии alexa не подходит. Административный PowerShell не нужен.
2. Открыть обычный Windows PowerShell в guest-сессии. Следующая команда читает Public entry,
   проверяет pin и выполняет Preview без запуска runtime.
3. Если Preview показывает правильные SID/владельца session/WinSta0/Default, profile/Workspace
   и отсутствие existing own-session tunnel, выполнить ту же команду с последним аргументом
   -Mode LaunchTest вместо -Mode Preview. Separate G2 key ввести только в локальный SecureString prompt.
4. Оставить launcher console открытой. Через смену пользователя вернуться в alexa,
   сохранив guest login; не выполнять Sign out гостя.
5. Через G2 проверить identity и полезную операцию в Workspace. Полный security audit каждый день не нужен.

~~~powershell
& {
    param([ValidateSet('Preview','LaunchTest')][string]$Mode='Preview')
    $ErrorActionPreference='Stop'
    $p=Join-Path $env:PUBLIC 'Documents\Fortis-G2-GuestEntry-0638D14A.ps1'
    $b=[IO.File]::ReadAllBytes($p)
    $sha=[Security.Cryptography.SHA256]::Create()
    try {
        $h=([BitConverter]::ToString($sha.ComputeHash($b))).Replace('-','')
    } finally {
        $sha.Dispose()
    }
    if($h -cne '0638D14A92F78006526281BEC98C391FAD96F6C0F3F70D9C02475DA3A56C481D'){
        throw 'Launcher SHA256 mismatch'
    }
    & ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($b))) -Mode $Mode -CapturedSHA256 $h
} -Mode Preview
~~~

Preview не читает profile contents и не вводит ключ. Если G2 уже запущен,
LaunchTestPrerequisitesPass=false из-за existing tunnel — ожидаемая защита от дубля.
Launcher также удерживает exclusive lock и повторно проверяет session перед стартом.
Lock не обходят и не удаляют для принудительного старта.

Preview запускать из локального guest PowerShell, не через нынешний sanitized MCP gate:
gate намеренно не передаёт OS env var, от которой зависит platform check launcher.
Для MCP continuity использована API-проверка Win32NT. Из этого не следует сбой Windows.

Имена profile fortis-host-g2-test и режима LaunchTest остаются прежними.
Поля WindowsAcceptance=PENDING/ProductionAccepted=false в старом launcher — его фиксированные
исторические labels, а не динамический реестр приёмки. Их не меняем ради видимости PASS;
решение о приёмке хранится в каноническом плане и этом документе.

## Обычная остановка и восстановление G2

1. В реальной guest launcher console нажать Ctrl+C один раз и дождаться возврата приглашения.
   Это пользовательский ручной шаг, не разрешение ассистенту управлять owner desktop.
2. Проверить прекращение выбранной runtime/Python/Node chain и её listener. E28 уже доказал normal
   cleanup этой версии; без drift не нужен новый обязательный stop/reboot test.
3. Для восстановления повторить pinned Preview → LaunchTest и ввести separate key локально.
   Не запускать init/provision, не копировать owner credentials и не создавать новый tunnel.
4. После timeout/неясного результата сначала проверить реальные processes/listener. Если chain осталась,
   повторный старт не выполнять; разобраться с её identity и отдельно выбрать адресное завершение.
5. После восстановления проверить actual G2 MCP/CLI identity и Workspace. Успех запуска процесса
   сам по себе не доказывает готовность MCP.

Ручной ежедневный login/start принят пользователем. Не нужны autologon, task с сохранённым паролем,
новый supervisor/Job или постоянный privileged broker. Cleanup не должен удалять полезные profiles,
cache и результаты. Произвольные descendants/crash/logoff этим runbook не объявляются проверенными.

Если канал перестал отвечать: сначала различить local process, MCP и control-plane/network failure.
503/504 polling сами по себе не доказывают отказ Windows runtime или AV.
Новый security denial не обходить; по нему нужна адресная диагностика.
Историческое PDM событие не является отдельным незакрытым gate и не требует отключать защиту.
Repo/контейнер и другие туннели из-за одиночной ошибки не останавливать.

## Выполненный шаг — retirement прежнего owner HOST

**Пользователь согласовал Stop; адресный CLI Stop и after-check выполнены E43.
Ниже — подготовленный порядок и before metadata; старый HOST теперь не работает.
Live owner recovery не выполнялось. Будущая остановка shared route требует решения.**
Ни миграция старого HOST на narrow EXE, ни новый helper для такой миграции не требуются.

Read-only owner metadata в01:25:05Z подтвердила прежний HOST:
profile desktop-commander (mapping E25), SID1001/Session1, full EXE, listener127.0.0.1:8080.
Launcher hash прежний, Windows AST errors0; profile/key/secret argv/env не читались.
В01:26:41Z G2 отдельно прочитал bounded process/listener metadata. Доступ к этим metadata
достаточен для последующего after-check без продолжения работы owner MCP.

| Цепочка / сосед | PID | CreatedUtc | Роль |
|---|---|---|---|
| Старый HOST | 13520 | 2026-10-15T18:57:19.7775460Z | Выбранный выводимый runtime |
| Его cmd | 16092 | 2026-10-15T18:57:20.0262350Z | Проверить завершение потомка |
| Его Node | 24724 | 2026-10-15T18:57:20.0652940Z | Проверить завершение потомка |
| G2 runtime | 25920 | 2026-10-15T21:01:23.7848810Z | Сохранить; listener54647 |
| Repo runtime | 31420 | 2026-10-16T00:06:04.3124340Z | Сохранить; listener50385 |

Порядок после решения:
1. Подтвердить, что сейчас допустимо прервать именно прежний owner HOST для других чатов.
   Снять свежие fingerprint выбранной chain, profile mapping и listeners; убедиться, что G2/Repo доступны.
   При новых process identity/descendants сначала пересмотреть scope, не применять старый PID вслепую.
2. Остановить именно старый HOST: обычный Ctrl+C пользователем в его launcher console
   либо отдельно согласованная адресная CLI-остановка по свежему fingerprint.
   Не делать kill всех node/tunnel-client, StopContainer, общий StopAccess или logout/reboot.
3. Через G2 проверить: прежние три process identities завершились, старый listener больше
   не принадлежит старому HOST и8080 не остался открытым route. Если порт занял другой процесс,
   определить его отдельно; это не PASS. Оставшийся orphan не считать cleanup PASS и не убивать вслепую.
4. Проверить actual G2 identity/MCP и actual Repo MCP. У соседей сверить fingerprints/listeners
   с новым before-срезом. Это point-in-time after-check, не доказательство непрерывного uptime.
5. Зафиксировать фактический вывод и пересчитать только затронутые статусы плана.
   Отзыв connector credentials, удаление plugin/чатов, изменение автозапуска не входят в этот шаг.
   Обычный ручной запуск старого HOST позже вновь откроет этот route; permanent revoke не заявляется.

### Локальное восстановление прежнего HOST при необходимости

Сохраняется existing owner launcher:
C:\Users\alexa\Documents\prot\Start-Desktop-Commander-Secure-Tunnel.ps1,
1114bytes, SHA256
0F644D4239E60886354EB83B6438CC888D8BDF3202B944B0304508E7C1336DFE.

Сохраняется full EXE C:\Tools\tunnel-client\tunnel-client.exe, SHA256
1946DE55A038313A9B9B2458D05FE1719FA9CF1F20A94DD5F38FC26A98BFDD42.
Owner profile и key не меняем и не переносим в G2/Docker.

Если действительно нужно вернуть прежний доступ, владелец в обычной owner Windows-сессии:
сначала проверяет отсутствие duplicate и hashes launcher/EXE, затем запускает existing launcher
обычным способом. Не запускает его из G2 и не повышает G2 права.
Если hash/identity изменились — сначала выясняет причину, не подменяет expected hash автоматически.
Восстановление вновь даёт прежний широкий owner route, поэтому это отдельное осознанное решение;
оно не происходит автоматически после retirement. Live recovery именно прежнего HOST сейчас
не репетировалось: перезапуск работающего shared route не нужен ради документа.

## Критерий завершения — выполнено в scope E43

Scope принят, selected retirement и after-check выполнены. Следующая таблица сохраняет смысл
согласованного плана, не назначает повтор тех же действий.

| Действие | Зачем нужно / от чего защищает | Цена и условие |
|---|---|---|
| Принять или скорректировать E42/P01 | Устанавливает проверяемый начальный scope и допустимые Evidence Limitations; предотвращает ложную универсальную гарантию | Решение пользователя; новые grants/tests не нужны, если scope подходит |
| Согласовать и выполнить выбранный old HOST retirement | Убирает известный широкий owner route и full API, оставшиеся после запуска G2 | Прерывает только прежний HOST, в том числе для других чатов; отдельное разрешение |
| Выполнить after-check | Подтверждает фактическое закрытие старой chain/listener и сохранение G2/Repo | Несколько адресных metadata/MCP calls; после uncertain mutation сначала effect check |
| Зафиксировать итоговую scoped приёмку | Разделяет доказанный результат, ограничения, accepted решения и оставшуюся whole-chat задачу | Документация; не требуется автоматический commit/push |

Полный повтор GUI/clipboard/ACL/lifecycle, reboot, универсальный IPC/service scan,
приватный recursive inventory, установка панели и новая архитектура сейчас не обязательны.
Новый доступ/программа/посредник или существенный drift могут потребовать адресной проверки.
Не закрывать2.5/2.6/5.4/5.8/7.6/1.4 универсальным PASS по принятию ограниченного baseline.

На этапе E42 подготовлено в Repo; native Windows continuity/metadata проверены через G2 и один адресный owner call.
Позднее E43 выполнил отдельно согласованный Stop/acceptance. No-stop срез ниже относится к E42.
Runtime/source/config/ACL/mounts/network/AV/tasks/services/credentials не менялись, туннели не
перезапускались, GUI/clipboard не использовались. Commit/push и публикация не выполнялись.
