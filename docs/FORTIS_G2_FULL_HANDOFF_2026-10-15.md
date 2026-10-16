# Fortis Host G2 — полный хендофф для чистого чата

> **Исторический handoff, superseded E42/E43/E44.**
> Действующий [итог](ISOLATION_GUIDE.md) и [E43](G3_G2_SCOPE_ACCEPTANCE_AND_HOST_RETIREMENT_2026-10-16.md):
> G2 принят(scope), old HOST остановлен, Repo narrow. Ниже старые PENDING/BLOCKED
> и требования прежнего этапа не являются текущими разрешениями/инструкциями.

**Исторический handoff до уточнений этого дня.** Начать с [актуального плана](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) и [CURRENT_STATE](CURRENT_STATE.md). Позднее пользователь принял ежедневный ручной вход и явно разрешил guest own GUI/clipboard; защищаются owner данные/control, безопасная диагностика допускается по доказанной семантике/версии. Прежние unattended gate, общий admin-GET-DENY и old next-work ниже не являются текущими условиями. Фактические результаты и ограничения этого среза сохранены; оригинальный прикреплённый файл не изменялся.

**Дата среза:** 15 октября 2026 года. **Текущий статус: G3 BLOCKED; G4–G6 не приняты.**

> **Задача новому чату:** продолжить работу над защищённым и удобным **Fortis Host G2**, который должен стать основным Windows-инструментом ChatGPT вместо широкого owner HOST. Не начинать G1/G2 заново; не выдавать отдельные успешные пробы за полный G3 PASS. Двигаться от уже доказанных фактов к минимальным безопасным исправлениям, сохраняя действующие owner HOST, Fortis Repo и существующие чаты. Различать подтверждённые наблюдения, синтетические тесты, проекты и недоказанные возможности.

## 1. Главная цель и архитектурное решение владельца

G2 должен полноценно выполнять Windows-задачи — PowerShell, Python, Node, Git, CLI, установленные приложения, необходимые Windows API и диагностику, собственный браузер Edge с CDP, файлы в согласованной рабочей области — **без прав администратора и без доступа к защищённым данным, экрану, буферу обмена и управляющим полномочиям `alexa`**.

Владелец прямо уточнил: **главное — выполнение реальных требований и отсутствие ощутимых неудобств; не выбирать сложный путь, если достаточен простой**. Отдельная «приватная оконная станция» — технический вариант, а не самостоятельная цель. Предпочтительно проверить запуск G2 в собственной Windows-сессии отдельного пользователя, но принять его только после доказательства изоляции и практичного автоматического восстановления.

**Не цель:** переделывать старые HOST и Repo или переводить все туннели на новый клиент ради самого перехода G2. Их нужно сохранить работоспособными. При этом подтверждённые обходы из G2 к owner API нельзя просто проигнорировать: возможна точечная защита *опасных функций*, без блокировки всех localhost-портов или безопасных health/diagnostic маршрутов.

## 2. Контуры, учётные записи, рабочие пути

| Контур | Состояние / роль |
| --- | --- |
| Владелец | `FORTIS_M\alexa`, SID `S-1-5-21-303538662-3368424508-2654684973-1001`; последние локальные проверки — Windows **Session 2**. Личные файлы, credentials, GUI/clipboard, owner-браузер и доверенные процессы защищаются. |
| Ограниченный пользователь G2 | `FORTIS_M\FortisHostG1`, SID `S-1-5-21-303538662-3368424508-2654684973-1009`; обычный **non-admin**. В последних тестах вручную вошёл в собственную Windows **Session 3** через Fast User Switching; SessionId может измениться после входа/перезагрузки. |
| Старый native HOST | Owner SID1001; широкий Windows Desktop Commander, профиль `desktop-commander`, не sandbox. Должен оставаться доступным владельцу и старым чатам. |
| Fortis Host G2 | Отдельная test auth/profile `fortis-host-g2-test`, отдельный ключ, narrow `tunnel-client-runtime.exe`, stdio wrapper; ранее проходил MCP/ACL-тесты под SID1009. **В новой Session 3 постоянный G2 runtime ещё не запущен и не принят.** |
| Fortis Repo | Native `repo-mode`; транспорт Windows от owner SID1001, MCP через Docker `fortis-repo-test`. Linux UID/GID1000, readonly rootfs, cap drop ALL, no-new-privileges; Windows bind mounts RW. Это главный разрешённый контур разработки. |
| Hosted Sites / иные плагины | Независимые маршруты; ограничение одного G2 или Site не отзывает права другого подключённого owner инструмента в том же чате. |

**Git checkout на Windows:** `C:\Users\alexa\Repos\tunnel`. **Через Fortis Repo:** `/workspace/repos/tunnel`. **НЕ путать с** `/workspace/repo` — отдельный внутренний Docker volume. Repo RW mounts: Windows `C:\Users\alexa\Repos` → `/workspace/repos`, Windows `C:\Users\alexa\Workfiles` → `/workspace/files`. Разрешение Linux-container на RW bind не ограничивается ACL `DENY` только для Windows SID1009.

**Безопасный порядок работы:** исходники/документы можно анализировать и править через подключённый **Fortis Repo**; статические Python/Node/Linux проверки допустимы. Прямые Windows security/native проверки выполняет **сам пользователь локально** под точным SID с проверенным SHA256 скрипта. Не запускать удалённые Windows-команды через owner HOST, G2 или другие Windows плагины. Не заявлять Linux compile/static PASS как Windows-native PASS.

В текущем git checkout есть многочисленные прежние tracked/untracked изменения, включая unrelated docs. **Не делать `git clean/reset/checkout`, общий commit/push или Site deployment** без отдельного решения; проверять только собственный scope и `git diff --check` по затронутым файлам.

## 3. G1/G2 — что реально было готово

**G1 PASS в синтетическом объёме.** Под SID1009/non-admin PowerShell/.NET, дочерний PowerShell и Python соблюдали `RW` (read/write), `RO` (read, запись denied) и `DENY` (чтение/запись denied) для `C:\Users\Public\Documents\FortisHostG1Probe\{RW,RO,DENY}`. Историческая ошибка SID1008 исправлена. Не распространять эту проверку автоматически на весь профиль `alexa`.

**G2 PASS в прежней тестовой native MCP конфигурации.** Отдельный тестовый профиль/авторизация; процессы tunnel-client → Python stdio gate → Node Desktop Commander → дочерние PowerShell/Python от SID1009. MCP `initialize`, инструменты, file/shell, RW/RO/DENY, readback/cleanup проверялись. UI cards/resources отключены (`DESKTOP_COMMANDER_DISABLE_MCP_UI=1`); секретные env variables не передавались дочернему Node. Wrapper `runtime/host-g2/g2-stdio-gate.py` **не является жёсткой security boundary против других процессов того же SID**.

**Ранее обнаруженный G3 FAIL общего runtime исправлен:** SID1009 мог открывать общие `C:\Tools` JS/EXE с write/append/delete и потенциально изменять код для последующего запуска owner. По явному согласию владелец вручную применил **ровно четыре scoped DACL**: `C:\Tools` (root), `C:\Tools\tunnel-client`, `C:\Tools\desktop-commander-runtime`, `C:\Tools\desktop-commander`. После этого реальные G2 mutation handles DENY, read/execute ALLOW; AccessCheck **22 758 объектов**: writable=0/errors=0. Backup в owner-private `C:\Users\alexa\AppData\Local\FortisHostG2AclBackup\...`. **Не повторять Apply, не откатывать и не ослаблять эти DACL ради запуска Edge.**

В прежней G2-only миграции тестовый G2 успешно работал с официальным **`tunnel-client-runtime.exe` v0.0.15** SHA256 `A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A`; собственные проверенные admin/UI/Harpoon HTTP endpoints отсутствовали (`404`), а MCP/health работали. Старый full-client owner HOST и Repo **на это не переключались**. Затем старый G2 остановили ради G3 window isolation. Старые PID G2 не считать живыми; **G2 runtime в отдельной Session3 пока не принят**.

## 4. G3 — почему сначала не запускался Edge

Первая архитектура `runtime/host-g2/window-isolation/Start-G2PrivateWindow.ps1` создавала дочерний SID1009 в **owner Windows Session2**, пусть и с новой приватной Window Station. Но это **не создаёт независимую Windows client session** и не исправляет permissions для `\Sessions\2\BaseNamedObjects`.

Наблюдалось: SID1009 в Session2 **не мог создать новый уникальный `Local\` named mutex** (Win32 5, namespace `STATUS_ACCESS_DENIED 0xC0000022`); установленный Edge на собственном тестовом профиле завершался `ProcessSingleton` exit21. Не расширять owner namespace DACL, не запускать guest как admin, не обходить текущие launch guards и не применять owner WinSta0/default ACL в обход согласованного плана.

**Отдельная гостевая Windows Session3 — существенный прогресс:** владелец вручную вошёл в `FortisHostG1` через Fast User Switching, оставив `alexa` в Session2. Non-admin SID1009 в Session3:

- **PASS:** успешно создал случайный `Local\FortisG3GuestCheck-{GUID}` mutex.
- **PASS:** запустил установленный Edge `--headless=new` со стандартным sandbox, изолированным guest-профилем, `about:blank` и собственным CDP `DevToolsActivePort` файлом; unnamed kill-on-close Job завершил Edge и временный профиль удалён. **Это ещё не проверка команд CDP, DOM, storage, всего G2 runtime или owner GUI deny.**
- **PASS:** read-only диагностика станции: `CurrentStationName="WinSta0"`, `CurrentStationVisible=true`, `EnumerationAllowed=true`, `EnumerationWin32=0`, `AccessibleStationNames=["WinSta0","Service-0x0-218d7932$"]`, `AclWrites=0`, `DesktopReads=0`, `OwnerSessionTouched=false`. Станция `WinSta0` в Session3 — **не** `WinSta0` владельца в Session2. Строка `Service-0x0-218d7932$` лишь перечислена; её owner/DACL/пригодность не проверены, **не использовать её для G2**.
- **Не удалось создать отдельную новую приватную станцию:** non-admin не может задавать произвольное имя `CreateWindowStation`. `CreateWindowStation(NULL,CWF_CREATE_ONLY=1,...)` вернул **Win32 183 `ERROR_ALREADY_EXISTS`**, поскольку автоматическое имя для этого logon уже занято. **Не путать 183 с Win32 5 и не убирать `CWF_CREATE_ONLY`, выдавая повторное открытие за новую private station.**

**Решение:** условно предпочесть саму отдельную guest Windows session как GUI/clipboard OS boundary — только если пройдут synthetic проверки фактического запрета доступа к owner screen/clipboard/window objects, не будет inherited owner handles/clipboard bridging и удастся реализовать нормальный невидимый/автоматический жизненный цикл. Не менять owner session ACL ради этой схемы.

## 5. Последний подтверждённый риск: owner HTTP API достижим из Session3

Владелец в обычной PowerShell выполнил pinned **read-only** `runtime/host-g2/Preview-G3TunnelListeners.ps1` (SHA256 `900196F0B19A83968F00DF91A9180DAB5F668433011799E0ED5DD690F223C0BE`). На снимке UTC `2026-10-14T20:04:59.9309689Z` (локально 15 октября):

| Owner процесс | Windows Session | TCP listener |
| --- | --- | --- |
| `tunnel-client.exe`, PID **31064** | 2, SID1001 | `127.0.0.1:52632` |
| `tunnel-client.exe`, PID **28376** | 2, SID1001 | `127.0.0.1:8080` |

`AclWrites=0`, `ProcessStarts=0`, `ProcessStops=0`, `HttpRequests=0`, `SecretValuesRead=false`. **Соответствие PID конкретным профилям HOST/Repo ещё не проверено**; номера портов/PID — снимок, их нельзя жёстко зашивать.

**Затем пользователь под SID1009, non-admin, Session3 отправил только два `GET /api/log-level`, без credentials и без чтения тела ответа**. Реальный ответ:

```json
{"Sid":"S-1-5-21-303538662-3368424508-2654684973-1009","Session":3,"Admin":false,"Method":"GET","CredentialsSent":false,"BodyRead":false,"Results":[{"Port":52632,"HttpStatus":200,"NetworkError":null},{"Port":8080,"HttpStatus":200,"NetworkError":null}]}
```

**Доказано:** G2 user из другой Windows-сессии может обращаться к двум owner-local admin GET endpoints. `127.0.0.1` изолирован от внешней сети binding'ом, но **не по локальным Windows пользователям и session ID**. Это реальный **G3 FAIL для границы owner admin GET**.

**Не доказано:** содержимое ответа (не читалось), возможность изменить настройки через `PUT/POST`, выполнение owner команд, полная компрометация HOST или конкретная принадлежность портов. В старом тесте 13 октября `OPTIONS` для `/api/log-level` указал `Allow: GET, PUT`, но никакой `PUT/POST` по живому owner endpoint не отправляли; **не проводить разрушающие или управляющие пробы на live owner API**.

**Вывод последнего обсуждения с владельцем:** по плану защиты нужно **закрыть доступ G2 к опасным административным функциям** owner HOST/Repo, а не обязательно закрывать полностью два localhost-порта и все health endpoints. Безопасные `healthz/readyz` и ограниченную диагностику можно оставить при отсутствии чувствительных данных. Нельзя считать простой `HTTP 200` доказательством критического RCE, но и игнорировать owner admin API нельзя. Требуется разобраться в точных маршрутах/методах/авторизации и выбрать **минимальную** надёжную защиту; желательно оставить HOST и Repo неизменными, пока нет доказательства необходимости миграции.

## 6. Runtime-only и последнее `Preview`: не путать с применением

В репозитории есть кандидат официального runtime-only клиента без проверенных admin/UI маршрутов. В **старом синтетическом тесте** он сохранил MCP, health/metrics и дал `404` на 20 выбранных admin/UI/Codex/Harpoon путях. G2 уже ранее работал с этим runtime в своём тестовом scope. Но это **не подтверждает** возможность безболезненного перехода действующих owner HOST/Repo.

Владелец выполнил SHA256-pinned `runtime/host-g2/runtime-api-migration/switch-launchers.ps1` (`0D68581ADD6F0126D1E8A0F6DF993C92D52096F7E13028CA9A79D3F602BC2612`) с `-Mode Preview`. **Все три** live файла получили `State=BEFORE`:

1. `C:\Users\alexa\Documents\prot\Start-Desktop-Commander-Secure-Tunnel.ps1` (HOST);
2. `C:\Users\alexa\chatgpt-repo-mode\run-tunnel.ps1` (Repo run);
3. `C:\Users\alexa\chatgpt-repo-mode\control.ps1` (Repo control).

Вывод: `Preview only. No files, processes, ACL or profiles changed.` На этом этапе actual owner runtime/profile/launchers **НЕ менялись**, процессы **НЕ перезапускались**; обнаруженный API-доступ **НЕ закрыт**. `switch-launchers.ps1 -Mode Apply` меняет **сразу все три launcher files**, что противоречит цели минимального независимого изменения. **Не вызывать Apply/Rollback без нового согласованного consequential scope.** Предпочтение владельца — G2 вместо широкого HOST для будущих задач, старые HOST и Repo сохранить. Если runtime-only необходим для owner API remediation, подготовить отдельно проверяемый, одноцелевой, обратимый переход только после доказательства, что более простой надёжной защиты нет.

## 7. Что остаётся в G3 — точные обязательные проверки

| Требование | Доказано сейчас / что ещё нужно |
| --- | --- |
| Ограниченный SID1009, non-admin и собственная Windows Session | **PASS** для отдельных guest Session3 smoke. Проверить каждого descendant реального G2 runtime; SessionId не зашивать как 3. |
| No owner screen, clipboard, window station/desktop access | **Пока НЕ доказано отрицательными тестами.** Нужны безопасные проверки Windows capabilities/отказов без чтения owner clipboard, pixels или приватных окон. Не подменять `not read` на `DENY`. |
| Edge/Node/Python/Git/PowerShell и реальный MCP в Session3 | **PARTIAL**: unique mutex и Edge CDP port-file PASS; полные CDP команды DOM/storage, весь CLI chain, stdio MCP profile, файловые gates/cleanup в этом session-контексте ещё не приняты. |
| Owner local API и IPC/network | **FAIL** для двух GET admin путей; нужны защита опасных функций/авторизация и последующие guest negative тесты без write. Остальные named pipes/loopback debug endpoints/SMB/service handlers не проверены полностью. |
| Личные файлы, credentials, runtime, backups | Runtime DACL исправлены в проверенном scope; реальная конечная G4 матрица RW/RO/DENY и защита secrets по всем маршрутам ещё не принята. Не читать настоящие ключи и личные данные. |
| Whole-chat route isolation | Не доказана: наличие owner HOST/Repo или других широких plugins в одном чате не ограничивается SID1009. Нужна проверка отдельно ограниченного ChatGPT route/tool inventory, без отключения других owner чатов. |
| Удобство startup/recovery | **Не выполнено**: Session3 создана вручную. Нужен способ G2 auto-start после relogon/reboot **без ежедневного переключения пользователей, plaintext passwords, focus stealing, SYSTEM/admin broker**, с ограниченным restart, job cleanup и rollback. |

**Task Scheduler — только варианты для исследования, НЕ созданные задачи:** `INTERACTIVE_TOKEN` требует уже открытой гостевой login session и не закрывает cold boot. `S4U` не хранит пароль, но ограничивает network/encrypted files; вероятно несовместим с tunnel/key до проверки. `PASSWORD` — потенциальный отдельный logon под non-admin, но регистрация credentials и runtime/Edge/network behaviour требуют отдельного review и **явного согласия**. Не выдавать S4U/PASSWORD за уже рабочее решение.

Другие открытые G3 пути: `SERVICE_USER_DEFINED_CONTROL` для выбранных служб ранее показывал ALLOW без отправки кодов (не доказана эксплуатация); `C$`/SMB и альтернативные Windows маршруты; cross-session capabilities, owner chat routes. Не расширять права ОС ради обхода этих вопросов.

## 8. Общие этапы G0–G6

- **G0:** baseline токенов/UAC/ACL, выборочные задачи/службы/localhost inventory — выполнены в ограниченном объёме, отсутствие всех обходов не доказано.
- **G1:** отдельная обычная Windows identity и synthetic NTFS RW/RO/DENY — PASS в ограниченном объёме.
- **G2:** независимый native HOST/MCP под SID1009, CLI/file matrix, UI hidden, отдельная auth; PASS в прежних конкретных тестах; G2 в новой Session3 ещё не принят.
- **G3 (ТЕКУЩИЙ):** устранить обходы owner runtime/GUI/localhost/IPC/SMB/service/route и сохранить совместимость. Runtime ACL PASS; Session3 mutex/Edge startup/station inventory PASS; localhost owner GET FAIL; остальные gates PENDING. **G3 BLOCKED.**
- **G4:** согласовать реальные рабочие каталоги RW/RO/DENY, сделать owner-controlled Preview/Apply/Rollback, проверить политику Windows и отдельно Repo Docker mounts, принять итоговый ограниченный G2 и migration от широкого Windows HOST. NOT ACCEPTED.
- **G5:** отдельно защитить личные документы, browser sessions, credentials, recovery, backups, network/endpoints во всех relevant routes; никаких реальных секретов в тестах. NOT ACCEPTED.
- **G6:** рабочие start/stop/reboot/relogon, ключи/rotation/revoke, обновления pinned runtime, логирование/восстановление/rollback, отсутствие ежедневной возни. NOT ACCEPTED.

## 9. Жёсткие правила безопасности и сохранности

- Никогда не передавать в чат, плагины/логи/Repo/Git `runtime.key`, пароли, G2 test key, cookies, browser profiles, личный экран и буфер `alexa`, env dumps и приватные owner commands. Ключи вводятся пользователем **локально и masked** только в согласованной процедуре. Не копировать owner auth в guest.
- Никаких Windows удалённых shell/process operations через owner HOST/G2 во время security-gate. Локальные Windows тесты выполняет пользователь; источник и временная копия — SHA256; не перезаписывать существующий Public файл и не запускать устаревшие pins. Kaspersky не отключать, не делать exclusions; при срабатывании остановиться.
- Не менять owner `WinSta0`, `Default` desktop, clipboard, оконный input, BaseNamedObjects DACL, user/session ACL, GUI, `C:\Windows`, личные папки, NTFS глобально. Не менять UAC/admin статус гостя.
- Не создавать сервисы, задачи Планировщика, автологин, RDP listener, сохранённый пароль, сетевые firewall правила, публичный localhost control broker без отдельно согласованной threat model и разрешения. Не включать новый сетевой доступ без необходимости.
- Не отключать стандартный Chromium/Edge sandbox, не использовать owner browser/CDP/cookies. Только новый гостевой профиль, synthetic targets, bounded timeout/job/cleanup.
- Не останавливать/перезапускать/переподписывать существующие owner HOST, Repo, Docker container, Sites, Broker или старые чаты. Owner runtime-only migration **не одобрена**. На каждом consequential change нужен точный Preview, before hashes, backup, scope, rollback, approval.
- Гарантии MCP `allowedDirectories`, «попросить перед опасной операцией» и выбор `@G2` — это не Windows ACL и не независимая доверенная среда. Shell может обойти UI-level ограничения, если OS доступ есть.
- При ошибках timeout сначала проверить физическое состояние, не повторять слепо. В отчётах всегда различать `PASS`, `FAIL`, `BLOCKED`, `PENDING`, реальное Windows evidence и source-only draft.

## 10. Ключевые файлы и закреплённые SHA256 (проверенные исходники Repo)

| Файл (от `/workspace/repos/tunnel`) | SHA256 / смысл |
| --- | --- |
| `runtime/host-g2/runtime-api-migration/start-g2-runtime.ps1` | `A0680EB311B1BE2C0F7C3B1F9A0362DAC9F69C59A01C0AC293C3F08626ECF8F4` — старый guest-only launcher; **не запускать как доказательство Session3 acceptance** без нового review. |
| `runtime/host-g2/window-isolation/Test-G3GuestSessionEdge.ps1` | `2A9B2FF45E234E69F7461F8C00421DED0C34BA19C420C17739641CC42B933527` — **actual Session3 Edge startup PASS**. |
| `runtime/host-g2/window-isolation/Test-G3GuestPrivateStation.ps1` | `9F82E0E35D47CE32411AB52139DCDF4C41AFBB42F549562539955C916DC843F6` — actual create-only **Win32 183**. |
| `runtime/host-g2/window-isolation/Inspect-G3GuestStations.ps1` | `941FED61BEB08A9370AEDFF8D4E05511AC4A896B9BCAD293312F2C7792BEB4E4` — actual Session3 `WinSta0` inventory PASS. |
| `runtime/host-g2/Preview-G3TunnelListeners.ps1` | `900196F0B19A83968F00DF91A9180DAB5F668433011799E0ED5DD690F223C0BE` — actual owner listener metadata PASS. |
| `runtime/host-g2/runtime-api-migration/switch-launchers.ps1` | `0D68581ADD6F0126D1E8A0F6DF993C92D52096F7E13028CA9A79D3F602BC2612` — actual three-launcher **Preview BEFORE**, **НЕ Apply**. |
| Installed official G2 narrow runtime | `C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe` — SHA256 `A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A`. |

Не переиспользовать старые многочисленные pins из `docs/CURRENT_STATE.md` как свежую команду. Если source меняется, новый hash, отдельная статическая ревизия и user-local verification обязательны. Репозиторий сам по себе не деплоит код в установленный HOST.

## 11. Документы для нового чата — в порядке приоритета

1. `FORTIS_WINDOWS_SECURITY_CHECKPOINT_G1_G2_2026-10-12.md` — доступная контрольная точка общего Security Plan G1–G6; **не полный v5**.
2. `docs/G2_NATIVE_HOST_TUNNEL_TEST_PLAN_2026-10-12.md` и `docs/G3_G2_RUNTIME_ACCEPTANCE_2026-10-13.md` — исходная цель и настоящее G2 MCP acceptance.
3. `docs/G3_SESSION_BOUNDARY_OUTCOME_DECISION_2026-10-15.md`, `docs/G3_SESSION3_STATIONS_READONLY_2026-10-15.md`, `docs/G3_GUEST_EDGE_SESSION3_SMOKE_2026-10-15.md`, `docs/G3_GUEST_STATION_EXISTING_OBJECT_2026-10-15.md` — новое guest Session3 решение/факты.
4. `docs/G3_LIVE_OWNER_LISTENERS_2026-10-15.md` и `docs/G3_POST_ACL_VERIFICATION_2026-10-13.md` — реальная localhost API проблема (GET200), прошлые ACL и оставшиеся обходы.
5. `docs/G3_OWNER_RUNTIME_ONLY_PREVIEW_2026-10-15.md`, `docs/G3_LOCAL_API_RUNTIME_2026-10-13.md`, `docs/G3_SESSION3_API_LIFECYCLE_GATES_2026-10-15.md` — runtime-only как опция, PENDING unattended lifecycle, actual preview BEFORE.
6. `docs/G4_ACCESS_POLICY_PROPOSAL_2026-10-13.md`, `docs/ACCESS.md`, `docs/ARCHITECTURE.md`, `docs/AUDIT.md`, `docs/OPERATIONS.md`, `docs/INSTRUCTIONS.md`, `docs/CURRENT_STATE.md` — политика, независимые routes и эксплуатация. `AUDIT.md` — проект обязательного gate, **не действующая гарантия**.

Оригинальный `Fortis_Windows_Security_Plan_2026-10-12_v5.md` был выдан в более раннем чате и **не обнаружен в текущем репозитории / доступных источниках**. **Не притворяться, что он прочитан**; при появлении оригинала сопоставить детали G5/G6 и acceptance, но G3 можно продолжать по checkpoint + уже собранным доказательствам.

## 12. Что делать первым в новом чате

1. Подтвердить доступность Fortis Repo и изучить этот хендофф + последние G3 evidence; не читать secrets и не открывать owner HOST. Показать короткий status текущих gates. Не повторять уже выполненные Session3 mutex, Edge startup, станционный read-only inventory, HTTP GET 200 или launcher Preview без конкретной причины.
2. **Source-only и read-only аудит owner локальных HTTP endpoint:** какие реальные пути/методы у full клиента, какие admin/write опасны и какие safe health/metrics допустимы, есть ли официально поддерживаемый способ убрать/аутентифицировать только admin без рестарта/migration. Не делать `PUT/POST` по live owner портам, не читать admin response body/ключи. Разделить известный риск и недоказанные последствия. Составить минимальные варианты и строгую отрицательную приёмку G2 SID1009.
3. Параллельно проектировать следующий **один** безопасный synthetic Session3 G2 compatibility gate: полный CDP протокол + synthetic DOM/storage, обычные CLI/PowerShell/Python/Git, Job+cleanup, свой workspace и native MCP под SID1009. Отдельно — synthetic owner GUI/clipboard deny test **без чтения реального содержимого**. Прежде чем давать Windows команды, сделать pinned source и статические проверки.
4. Изучить возможность безопасного headless/background процесса под обычным SID1009 после reboot без ручного Fast User Switching и без постоянного plaintext password. Task Scheduler варианты — только source-review до согласования. Если Session3 требует ежедневного ручного входа, производственный вариант ещё **не соответствует требованию удобства**.
5. Только после доказанных G3 negative gate и удобного lifecycle двигаться к G4 named-roots policy, G5 защите личных данных и G6 operation/recovery. Изменения старого HOST/Repo — **последний вариант**, узкие, обратимые, по одному маршруту и только по одобрению владельца.

**Главный принцип для следующего ассистента:** практично довести до рабочего безопасного G2; не тратить работу на миграцию всех туннелей или сложный приватный station, если требования могут быть выполнены проще. Но не называть безопасность доказанной, пока фактические обходы G3 не закрыты.
