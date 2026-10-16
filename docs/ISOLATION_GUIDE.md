# Fortis — итог изоляции, доказательства и повторная настройка

Обновлено 16 октября 2026 после E43/E44. Это обзор результата и порядок повторения подхода; действующие условия и точные команды находятся у владельцев, перечисленных ниже.

## Что получилось

Windows-инструмент ChatGPT — G2 под отдельным обычным пользователем `FortisHostG1`, SID с окончанием `1009`, в его собственной интерактивной Windows-сессии. Ему разрешены собственные GUI, экран, clipboard, браузер/CDP, рабочие профили и результаты, нужные программы, CLI, сеть и собственные credentials для согласованных задач. Защищаемая область — личные данные и credentials владельца, вся его GUI/clipboard, shared runtime и управляющие интерфейсы. Защита касается и обычных owner-окон без elevation.

Основная разработка остаётся в Fortis Repo. Прежний Windows HOST под `alexa` остановлен по отдельному разрешению. Само подключение G2 его не останавливало; фактический вывод выполнен позднее, E43.

| Компонент | Итог | Граница |
|---|---|---|
| G2 | Отдельный Windows SID, non-admin, отдельный интерактивный login; narrow runtime → Python gate → Node MCP | Windows token, session/object access, ACL и проверенные маршруты |
| Repo | Windows launcher под `alexa` → narrow runtime → Docker exec → Linux Bridge/MCP | Контейнер, его user/capabilities, mounts и доступные интерфейсы |
| Прежний owner HOST | Выбранные runtime/cmd/Node завершены, listener8080 отсутствует, E43 | Credentials/connector и локальный launcher сохранены; повторный запуск вновь откроет route |
| Монитор | Автоматический Repo collector исправлен и проверен, E39 | Старая installed панель не обновлялась; постоянная история журналов не внедрялась |
| Sites и Snapshot Broker | Независимые контуры | Они не являются обязательным маршрутом native Repo/G2 и не ограничивают автоматически другой connector |

## Где читать действующие условия

- [Канонический план и реестр E01–E44](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md): определения scope, критерии, статусы и оставшиеся ограничения.
- [Рабочая инструкция E42](G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md): текущий pinned guest entry, normal stop/recovery, восстановление старого HOST.
- [Итог перехода E43](G3_G2_SCOPE_ACCEPTANCE_AND_HOST_RETIREMENT_2026-10-16.md): разрешение пользователя, фактическая остановка и независимый after-check.
- [Текущее состояние](CURRENT_STATE.md): датированные наблюдения. PID/ports и названия Session не считать постоянной конфигурацией.
- [Архитектура](ARCHITECTURE.md), [доступ](ACCESS.md), [операции](OPERATIONS.md), [доставка изменений](INSTRUCTIONS.md): владельцы общих определений.

Этот обзор не заменяет перечисленные документы и не создаёт новые разрешения. Исходники в `runtime/` не применяются к установленной версии автоматически.

## Что реально проверено

| Свойство | Доказательства | Предел вывода |
|---|---|---|
| Отдельная guest chain, MCP, файлы и CLI | E18/E19/E24/E28/E42/E43 | После смены session/process/version сверять затронутую identity; не переносить PID на новый запуск |
| Свой браузер и GUI | E20: окно, CDP/DOM/storage/reload, default sandbox; E22: authorized own clipboard marker/cleanup | Это разрешённые guest-возможности, а не owner GUI test |
| Owner GUI и selected handles | E21: четыре fresh-open station rights DENY5, desktop paths blocked at station root; E22: selected owner DUP_HANDLE DENY; E24: ordinary cross-session inheritance restriction | Не доказана DACL каждого desktop и полнота всех переданных handles/clipboard bridges |
| Runtime ACL | E04/E08/E26/E32: read/execute positives, mutation DENY, selected alternate paths | Не вся файловая система; E26/E32 не являются повтором полного старого scan |
| Scheduler, Docker pipes, standard service controls | E03 | Конкретные объекты и права, без запуска tasks/services и destructive operations |
| Service custom controls | E30/E41: matching MySQL source custom handler сообщает статус; service metadata исправлена | Installed-source binding неполон. ALLOW отдельного custom-control права не равен RCE; live fuzzing не выполнялся |
| Namespace/SMB effective access | E31/E32: synthetic controls и selected runtime objects через normal/extended/localhost C$ | Это effective rights перечисленных путей, не полный SMB/namespace audit |
| Выбранные owner assets и backup | E40: семь файлов, два backup parents,130 denied opens;15 own positives | Не все личные данные, keys и backups; отсутствие пути не является DENY |
| Известный Snapshot Broker | E41: queue/control/parents78 denied opens,6 own positives; installed worker hash matches source | Запросы в очередь/snapshot не отправлялись; полный Bridge/permits audit не выполнялся |
| Repo admin API | E35/E38: scoped source graph; narrow artifact, native MCP, выбранные admin GET404, безопасная диагностика сохранена | Не все owner API вообще и не запрет любого localhost доступа |
| Repo monitor discovery | E39:11 tests, actual Windows automatic UP/initialized | Source collector проверен; installed dashboard/GUI не доставлены |
| Daily/normal recovery | E20/E28: actual reboot/manual start, normal stop/restart; E29: один synthetic peer failure | Не все crash/logoff и произвольные будущие descendants. Runtime exit0 не доказывает успех MCP-задачи |
| Вывод old HOST | E43: old13520/cmd16092/Node24724 gone,8080 absent; G2/Repo actual MCP/CLI и fingerprints сохранены | Адресный Process.Kill, не graceful Ctrl+C; point-in-time проверка, не continuous uptime или permanent revoke |

Статусы слоёв после решения E43: G3 bounded baseline принят(scope), G4 initial Workspace policy принят(scope), G6 manual daily/normal recovery принят(scope). Полная G5 personal-security программа и whole-chat1.4 не приняты. PARTIAL универсальных свойств остаются ограничениями доказательств.

## Отдельно о Docker и запуске Repo под alexa

Команды MCP Repo выполняются в Linux-контейнере; Windows-учётная запись launcher не передаёт им автоматически полный Windows token владельца. Административную API-поверхность Windows runtime убрали E38. При компрометации самого Windows-компонента его учётная запись всё же определяет возможные последствия.

Адресный read-only осмотр E44 после E43 установил для выполнявшегося Repo Python-процесса:

- UID/GID1000; CapInh/CapPrm/CapEff/CapBnd=0.
- NoNewPrivs=1; Seccomp=2.
- `/var/run/docker.sock` и `/run/docker.sock` отсутствуют. Это не отдельное исключение всех возможных Docker API endpoints.
- В mount namespace видны Windows shares `/Users/alexa/Repos` → `/workspace/repos` и `/Users/alexa/Workfiles` → `/workspace/files`, оба RW.
- `/workspace/repo` — отдельный ext4 Docker volume.

Датированный повтор metadata осмотра в09:00 Asia/Bangkok сохранён в [E44](G3_DOCS_CONSOLIDATION_AND_REPO_BOUNDARY_2026-10-16.md) и его JSON. Это не полный `docker inspect`.

Repo намеренно может менять или удалять доступные Windows-файлы внутри двух RW roots. Это не требует container escape. Если владелец позже запустит изменённый скрипт на Windows, такой запуск пересечёт границу исполнения по обычному рабочему процессу. Поэтому Docker не заменяет review/backup для разрешённых проектов.

Полный аудит Docker Desktop version, сетевых путей, всех endpoints и известных уязвимостей сейчас не выполнялся. Основания автоматически переносить Repo под G2 только из-за owner launcher не установлены. Изменение mounts/прав — отдельное решение по конкретной потребности.

## Как прошла работа

| Этап | Что выяснили или сделали | Что переиспользовать |
|---|---|---|
| Начальные G2/E/F/G и E01–E06 | Проверили фактические SID/tools/file права и shared-runtime проблему; owner применил согласованные ACL; native G2 и scoped stop/restore подтверждены | Метод effective-access проверки с own positives; исходный scope и raw evidence |
| E07–E17 | Исследовали private station, narrow runtime, owner API и отдельную Windows session; часть старых подходов не подошла | Обоснование выбора; failed attempts сохраняются как история, не список обязательных повторов |
| E18/E19 | Перешли на user-local guest entry и actual G2 MCP в отдельном login; настроили Repo → guest Workspace → CLI/test без email | Обычная итерация через существующие контуры с source pin/read-back |
| E20–E24 | Проверили own GUI/browser/clipboard, owner fresh-open/selected handles, launch/inheritance; перечислили gaps | Достаточные positive/negative controls без чтения owner GUI/clipboard |
| E25–E29 | Разобрали owner routes; уточнили, что G2 заменяет старый HOST; подтвердили current ACL, normal recovery и один failure case | Сохранение соседних контуров, scoped lifecycle и честные limits |
| E30–E37 | Адресно проверили services/namespaces/selected IPC и подготовили независимый Repo cutover/recovery | Не использовать исторический all-three Apply; не требовать полный scan без конкретного вопроса |
| E38/E39 | Применили Repo narrow runtime, проверили MCP/API/control; устранили discovery timeout source collector | Реальный receipt/backup/recovery; source fix не равен installation панели |
| E40/E41 | Проверили selected private assets/backups и известный Broker; исправили ошибочное описание MySQL account | Защита конкретных существующих объектов, сохранение raw данных и явная correction |
| E42/E43 | Подготовили runbook, пользователь принял scope и old HOST stop; проверили фактическое завершение и сохранность G2/Repo | Явное решение, bounded after-check и разделение scoped acceptance/whole-chat гарантии |

PDM/AV и 503/504 сохранились как диагностическая история. Причинность и true/false positive не установлены. Нельзя превращать их в доказанный единый инцидент, обязательный незакрытый gate или основание отключить защиту.

## Повторная настройка похожей системы

Это последовательность воспроизведения подхода, не готовый универсальный installer. Точные grants, учётные записи и окна обслуживания выбирает владелец новой системы. Перед применением прочитать актуальные sources/README и сопоставить их с установленными версиями.

### 1. Зафиксировать нужный сценарий и границы

Определить owner, отдельного guest-пользователя, разрешённые файлы, собственные GUI/browser/clipboard/network и защищаемые owner assets/interfaces. Решить, достаточно ли ручного guest login/start. Отдельно определить, требуется ли изоляция всего чата с учётом других connectors.

Не наследовать сюда запрет собственных guest GUI/clipboard, обязательный headless, autologon или universal ACL manager: в этой настройке они не нужны.

### 2. Подтвердить реальные пути и возможность восстановления

На новой системе проверить существующие проекты, Git status, mounts, runtime locations и полномочия. Сохранить точные backup/restore данные перед consequential изменениями. Учётные записи, SID, profile names, paths, binaries и hashes этой машины не являются переносимыми параметрами по умолчанию. Нельзя копировать её credentials.

### 3. Подготовить non-admin Windows-контекст и runtime

Под отдельное согласованное решение создать или выбрать обычного Windows-пользователя и отдельный профиль/auth для нужного tunnel. Проверить primary token, отсутствие Administrators group и действующего impersonation. Защитить выбранные shared runtime files/parents от guest mutation при нужном read/execute доступе; использовать E04/E08/E26/E32 как метод, не применять старую DACL вслепую.

Для shared runtime проверить замену/append/delete, parent DELETE_CHILD, WRITE_DAC/WRITE_OWNER с own positive controls. Не выполнять разрушительные записи для проверки отказа. Missing path и ошибка в probe не являются security DENY.

### 4. Выбрать узкий transport и проверить artifact

Получить выбранную официальную версию narrow runtime из доверенного источника, проверить artifact/source provenance и SHA. Отдельно подтвердить native MCP и отсутствие ненужных admin routes/Harpoon transport. Проверка404 случайного пути недостаточна; использовать известный route graph выбранной версии. Нужную безопасную диагностику не запрещать автоматически.

При сохранении Repo обновлять его launcher/control вместе по независимому Preview/backup/apply/recovery. Пример этого случая — E35–E38 и Repo recovery. Старый owner HOST, который должен быть выведен, не требуется предварительно мигрировать на другой EXE.

### 5. Запускать G2 из настоящего guest login

Войти в Windows как guest и открыть обычный PowerShell. Проверить token SID, владельца Windows session и собственные WinSta0/Default. Run as guest внутри owner session не заменяет отдельный login.

Адаптировать `runtime/host-g2/runtime-api-migration/start-g2-guest-session.ps1` под новую систему с review и собственным pin. Сначала Preview, затем локальный запуск с отдельным guest key. Сохранить duplicate/session checks и exclusive lock. Названия LaunchTest/test в старом source не являются самостоятельной приёмкой.

Оставить launch console и guest login открытыми, переключиться к owner. Из фактического MCP проверить ancestry, SID/session, deployed gate/EXE hashes и полезную Workspace операцию. Не переносить ключ через email/чат. Для разработки передавать малые проверенные sources Repo → guest Workspace с read-back; сохранять действующие лимиты передачи.

Gate очищает лишние env variables, но не является OS security boundary против кода того же SID. В текущем gate нет OS env var: launcher Preview запускается из local Windows PowerShell, а не через sanitized MCP shell. Уточнить этот контракт при адаптации.

### 6. Проверить полезность и релевантные границы

В новой конфигурации проверить нужные CLI/files/Git/browser/CDP и собственные GUI/clipboard на synthetic объектах. Clipboard содержимое owner не читать и не менять. Положительные controls обязательны для интерпретации negative tests.

Адресно проверить fresh-open owner station/desktop path capabilities, selected owner process rights, relevant owner API/brokers/services и конкретные private/backup assets. Использовать metadata владельца для corroboration target. Недоступность QUERY_LIMITED_INFORMATION не превращать в автоматический FAIL изоляции; разделять метод проверки и проверяемое право.

Не требовать полного исключения всех неизвестных handles/IPC посредством конечного scan. Зафиксировать найденные ограничения и выбрать достаточный evidence scope до решения о приёмке.

### 7. Подтвердить границы Repo отдельно

Если Repo сохраняется, проверить actual Linux user, capabilities, NoNewPrivs/seccomp, mounts, доступ к Docker engine и релевантные network interfaces. Проверка двух стандартных socket paths не равна полному исключению Docker API.

Не монтировать весь home или Docker socket ради удобства. Разрешённые RW roots намеренно остаются изменяемыми. Не называть их черновыми копиями и не считать Windows ACL гостя ограничением независимого Docker share. Любое изменение mounts/сети/прав требует отдельного решения.

### 8. Проверить обычную остановку и восстановление

Снять before fingerprints runtime/gate/MCP и listeners. В согласованный момент выполнить обычный stop, проверить завершение выбранной chain/listener, затем повторный pinned guest start и полезный actual MCP вызов. Сверить ожидаемо неизменных соседей.

Один обоснованный synthetic failure полезен для конкретной угрозы. Новый supervisor, Job, forced crash/logoff matrix и повтор reboot не требуются автоматически. Чётко отделять normal cleanup от всех возможных descendants/failures.

### 9. Принять scope и вывести прежний широкий доступ

Подготовить понятный итог, limits, daily/recovery и конкретный план вывода shared owner route. Получить решение на его остановку. Снять свежие identities; остановить только выбранные процессы; через оставшиеся независимые каналы проверить old chain/listener gone и работу G2/Repo.

`Stop-LegacyOwnerHost.ps1` — одноразовый exact-instance helper этой машины: жёстко зафиксированные PID/native timestamps/profile/hashes/journal. Он не универсальный stop tool. На новой системе нельзя менять пару PID и запускать его без полного review. Не удалять existing journal ради повторной мутации; после timeout сначала проверить effect. Не применять all-process-name kill, общий StopAccess/StopContainer или reboot для выбранного перехода.

### 10. Сохранить итог и правило будущей проверки

Раздельно записать: source подготовлен; проверено в Repo; native Windows проверено; реально доставлено/перезапущено; принято в указанном scope; опубликовано/commit/push или нет. Сохранить evidence JSON, corrections, актуальные pins и recovery locations без secret contents. Старые failures и alternative approaches сохранять с датой как историю.

Ежедневно сверять достаточную identity/readiness, а не повторять весь аудит. После version/path/session/grant/mount изменения проверять затронутую границу. Новые существенные surfaces требуют адресной оценки. Без изменений и нового вопроса достаточные тесты не повторять.

## Что нельзя считать результатом этой работы

- Полную изоляцию чата при сохранении независимого Repo RW и иных полномочных connectors.
- Защиту всех личных файлов/backups по тестам выбранных объектов.
- Отсутствие любого неизвестного IPC/clipboard bridge или уязвимости Docker/Windows runtime.
- Невозможность повторного owner HOST запуска: ключ/connector/launcher сохранены.
- Установленную новую панель, постоянный журнал всех вызовов или policy enforcement всех shell операций.
- Универсальное воспроизведение по старым SID/PID/ports/hashes и historical all-three Apply.

## Какие исходники нужны для повторения

Пути ниже относятся к этому checkout; ссылки указывают на проверенные источники. Это не набор команд для немедленного Apply.

| Назначение | Источник | Ограничение переноса |
|---|---|---|
| Shared runtime ACL | [protect-shared-runtime.ps1](../runtime/host-g2/protect-shared-runtime.ps1) | Default Preview; Apply/Rollback требуют owner-admin. SID1001/1009 и четыре C:\Tools targets зафиксированы в коде. Нужен review новой системы |
| Guest entry | [start-g2-guest-session.ps1](../runtime/host-g2/runtime-api-migration/start-g2-guest-session.ps1) | Default Preview; existing profile/Workspace обязательны. Не создаёт учётную запись, профиль или credentials |
| Env hygiene | [g2-stdio-gate.py](../runtime/host-g2/g2-stdio-gate.py) | Фиксированные Node/DC paths; не OS sandbox для same-SID кода |
| GUI/session диагностика | [window-isolation/README](../runtime/host-g2/window-isolation/README.md) | Датированные методы и прототипы; private-station launch не текущий launcher |
| Current-runtime ACL test | [Test-G2CurrentRuntimeAcl.ps1](../runtime/host-g2/runtime-api-migration/Test-G2CurrentRuntimeAcl.ps1) | Проверять identities/targets/pin под новую систему; не повторять старый полный scan без причины |
| Lifecycle test | [Test-G2Lifecycle.ps1](../runtime/host-g2/runtime-api-migration/Test-G2Lifecycle.ps1) | Before/after fingerprints, без встроенной остановки; PID старого baseline не переносится |
| Repo launcher/control | [repo-run-tunnel.ps1](../runtime/host-g2/runtime-api-migration/repo-run-tunnel.ps1), [repo-control.ps1](../runtime/host-g2/runtime-api-migration/repo-control.ps1) | Именно эти source bytes доставлены E38. Старые runtime/repo-mode run/control — dated BEFORE, не current deployment |
| Repo migration/recovery | [Invoke-RepoRouteMigration.ps1](../runtime/host-g2/runtime-api-migration/Invoke-RepoRouteMigration.ps1), [recovery](G3_REPO_RUNTIME_ONLY_RECOVERY_2026-10-16.md) | Exact two-file guards/pins/backup; параметры и BEFORE/AFTER требуют review, не универсальный installer |
| Linux Bridge | [fortis-mcp-bridge.mjs](../runtime/repo-mode/fortis-mcp-bridge.mjs) | Установлен в /workspace/repo/.fortis; E44 source/live hash match. Изменение source само не меняет volume |
| Docker baseline | [Dockerfile](../runtime/repo-mode/Dockerfile), [workspace-config.example.json](../runtime/repo-mode/workspace-config.example.json), [probe.mjs](../runtime/repo-mode/probe.mjs) | Dockerfile не задаёт mounts/network/security flags; example содержит старые machine/container identities, не готовая переносимая конфигурация |

Точные hashes launcher/gate/runtime и локальные live paths — в E42; AFTER Repo hashes и recovery backup — в E38.
ACL source на момент E44: SHA256 0A7E0F496F314A7A5C272FEA9032DC6E4F274147E6E1AAEE3D2937E428CF5B76.
Для новой версии нужен собственный provenance/pin; нельзя просто заменить expected hash после неожиданного несовпадения.

Начальный provisioning Windows-account/auth/profile и установка зависимостей не собраны в универсальный
проверенный installer. Исторический [G2 test plan A–D](G2_NATIVE_HOST_TUNNEL_TEST_PLAN_2026-10-12.md)
содержит исходную подготовку; требования допуска/старые ограничения чтения в нём заменены текущим
планом. На новой машине эти подготовительные действия остаются отдельным согласованным шагом.
Текущая инструкция позволяет воспроизвести архитектуру и приёмку, но не обещает полностью
автоматическую установку одной командой.

## Документирование результата

[E44](G3_DOCS_CONSOLIDATION_AND_REPO_BOUNDARY_2026-10-16.md) фиксирует обзор, source/live сверку,
текущий metadata scope и восстановление MCP-сеанса после409. Действующий процесс Repo и listener
оставались видны через G2; после повторного выбора того же плагина native Repo вызовы снова прошли.
Ассистент не перезапускал tunnel/container и не менял безопасность для восстановления доступа.

Документы записаны в Windows checkout через Repo RW mount. Runtime/ACL/mounts/network/AV/
tasks/services/autostart/credentials не менялись. Commit/push и публикация не выполнялись.


## Основания Docker

Официальные документы: [bind mounts](https://docs.docker.com/engine/storage/bind-mounts/), [Windows permission requirements](https://docs.docker.com/desktop/setup/install/windows-permission-requirements/), [Docker Engine security](https://docs.docker.com/engine/security/). Они объясняют механизмы; фактическую конфигурацию этой машины подтверждают только датированные наблюдения.
