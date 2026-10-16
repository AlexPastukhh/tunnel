# Fortis — итог G2/Repo, доказательства и повторная настройка

Дата актуализации: 16 октября 2026. Это документированный срез, а не runtime policy или installer.
[Канонический план](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) хранит 58 критериев и E01–E44;
[E42](G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md) — точные guest-local start/stop/recovery;
[E43](G3_G2_SCOPE_ACCEPTANCE_AND_HOST_RETIREMENT_2026-10-16.md) — согласованное решение и after-check.

## Принято (решение пользователя E43)

G2 — отдельный Windows login обычного FortisHostG1 (SID1009/non-admin) вместо широкого owner HOST.
Допустимы свои GUI, clipboard, Edge/CDP, persistent state, Workspace, scoped credentials,
нужная сеть и CLI. Защищаются owner GUI/clipboard, secrets/private data, shared runtime и
опасные owner control surfaces. Ручной guest login → Preview/LaunchTest → switch-back,
Ctrl+C для normal stop/recovery принят, без time gate и нового supervisor.
G3 bounded baseline ACCEPTED(scope); G4 initial Workspace ACCEPTED(scope);
G6 manual daily/normal recovery ACCEPTED(scope). G5 selected assets PASS(scope),
но полная personal-security/backup программа не принята.
Whole-chat1.4 PENDING: другие connectors и независимый Repo RW не становятся ограниченными
от выбора G2 или инструкции ассистента.

## Проверено (evidence с пределами)

| Evidence | Проверенное и его граница |
|---|---|
| E01–E06 | Initial Windows/G2/ACL baseline; четыре shared-runtime DACL исправлены owner. Старые FAIL не удалять |
| E07–E17 | Windows sessions/private-station/Edge/mutex prototypes; private-station attempt не текущий launcher |
| E18–E20 | Guest SID1009/non-admin actual MCP/CLI, synthetic Git, own window и Edge/CDP DOM/storage/reload PASS(scope) |
| E21–E24 | Selected owner GUI station fresh-open DENY, own clipboard marker, selected owner DUP_HANDLE DENY; incomplete handle census |
| E26–E29 | Scoped runtime ACL controls, normal G2 stop/restart, один synthetic MCP peer failure; не arbitrary crash |
| E30–E33 | Selected services/namespace/alternate paths/TCP; не полная IPC/handle/service проверка |
| E35–E39 | Guarded E38 Repo narrow live migration, native MCP/health/metrics; E39 source monitor fix не обновлял installed panel |
| E40–E41 | Selected private assets/backups и known Broker controls, не все personal roots или bindings |
| E42–E43 | Принятый bounded scope и один exact-instance old HOST Stop; selected old PIDs/8080 ушли, G2/Repo сохранялись |
| E44 | Прямой Linux Repo command UID/caps/mounts и source SHA; это metadata/docs, не новый Windows security PASS |

Исторические failures, Candidate/BLOCKED/NEXT в источниках не переписываются в ложный PASS:
их дата и tested target отличаются от поздних E42/E43 решений.
[Исторический хендофф](FORTIS_G2_FULL_HANDOFF_2026-10-15.md) и полный [реестр](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md).

## Хронология инженерных решений

| Этап | Почему сделано именно так | Что осталось ограниченным |
|---|---|---|
| E01–E06 | Первые native/MCP/ACL проверки нашли широкий owner route и writable shared runtime; owner адресно исправил четыре DACL | Старые FAIL сохранены, новое поведение доказано только выбранными controls |
| E07–E17 | Private station, RunAs, mutex, Edge/launcher attempts не стали рабочей схемой; выбран обычный отдельный Windows login | Failed approaches — исторические методы, не текущая обязательная работа |
| E18–E20 | Repo → малая pinned копия в own guest Workspace → actual guest CLI/test/readback; browser/CDP и own window | Guest positives не доказывают owner GUI/clipboard read denial |
| E21–E24 | Fresh-open owner station и selected duplicated handles DENY; own clipboard marker PASS | 184 PSS entries без полного type-name coverage; unknown bridges остаются |
| E25–E29 | Цель уточнена: G2 заменяет старый owner HOST. Current ACL, normal stop/restart, один synthetic failure | Crash/logoff, произвольные descendants не проверены. Exit0 не означает MCP success |
| E30–E33 | Selected service/IPC/namespace/TCP и alternate path исследования | Не exhaustive service/IPC/SMB/API audit. MySQL actual account NetworkService |
| E34–E39 | Repo-only guarded Preview, actual narrow Apply E38 и source discovery correction E39 | Live rollback не исполнялся; старая installed dashboard не менялась |
| E40–E41 | Проверены выбранные owner files/backups и Broker queue/control paths | Нет доказанной полноты всех personal roots и IPC |
| E42–E43 | Exact entry/stop/recovery, явное принятие bounded scope и адресный old HOST Stop | Launcher/key/connector сохранены; стоп был point-in-time и не permanent revoke |
| E44 | Linux Repo uid/caps/mount/Bridge source-live evidence + current docs | Это не новый Windows runtime, Docker daemon или full security PASS |

В E26 отмечены 48 denied mutations, 16 allowed reads и 12 own controls;
в E40 — 130 denied opens и 15 own positives; в E41 — 78 denied Broker opens
и 6 positives. Это выбранные cases с исходным scope, а не распространение на все
возможные assets, services, namespace paths и endpoints.
Предыдущие невыполненные планы и incident investigation нельзя повторять лишь потому,
что слово NEXT сохранилось в датированном разделе. False-positive/AV причина PDM не установлена.
Источник подробностей — [реестр E01–E44](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md).

Передача целых файлов между HOST и ChatGPT по исходному handoff имеет предел
1 000 000 байт на логический набор в обе стороны, без обхода разбиением на части.
Обработка на месте в разрешённых Repo mounts не означает право раскрывать owner secrets.
Комментарии source WindowsAcceptance=PENDING и ProductionAccepted=false — исторические
фиксированные labels, не живой реестр приёмки; их не надо менять ради PASS.

## Контуры и ограничения

G2: guest Windows login → narrow runtime → Python environment gate → Node MCP.
Gate убирает environment variables, но не является OS sandbox для любого кода same-SID.
Owner Windows GUI/clipboard нельзя автоматизировать из этого контекста.

Fortis Repo: Windows launcher от alexa → narrow Repo API (E38) → Linux Docker MCP UID1000.
Точный checkout: /workspace/repos/tunnel; Windows checkout: C:\Users\alexa\Repos\tunnel.
Repos/Workfiles являются Windows RW mounts: Docker-команды меняют файлы Windows, включая scripts,
которые owner может впоследствии запустить. /workspace/repo — отдельный внутренний volume.
Отсутствие двух стандартных docker.sock paths, caps=0, NoNewPrivs1/seccomp2 — только
адресный metadata scope. Не выполнен полный daemon/flags/network/version/vulnerability audit.
[Подробности E44](G3_DOCS_CONSOLIDATION_AND_REPO_BOUNDARY_2026-10-16.md).

Old owner HOST: E43 остановил выбранные процессы и listener 8080. Его launcher, credentials,
profile и connector оставлены для осознанного recovery. Не запускать для документации,
ротации ключа или проверки G2. Native Repo, hosted Sites и Snapshot Broker независимы.
Source files не равны deployed Windows artifact, installed dashboard или published Site.

## Порядок повторения похожей системы

### 1. Определить полезные функции и threat model
Отделить собственные Windows CLI/GUI/clipboard/browser/network и защищённые owner surfaces.
Сформулировать, нужна ли полная гарантия всего чата; она не доказана одним Windows SID.

### 2. Установить фактические пути и baseline
Read-only проверить owner/guest SID, session, checkout, mounts, root и git status; сделать
контролируемые pin/backup. Не переносить старые PID, UID, SID или Docker identity как константы.

### 3. Подготовить обычный guest login
Отдельно provision Windows account/profile/auth и необходимые Python/Node/runtime.
RunAs внутри owner GUI не эквивалентен отдельному interactive guest login.
Настройка учётной записи и secrets не автоматизирована этим пакетом.

### 4. Проверить narrow source и shared runtime ACL
Сверить hash и exact targets с source map ниже; исходный ACL helper содержит machine-specific
SID/paths и default Preview. Owner-admin Apply допустим только в отдельном scope и с guards.
Не подменять ожидаемый hash после расхождения.

### 5. Выполнить guest-local Preview/LaunchTest
Пользоваться [E42](G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md).
Ввести scoped guest key локально; сохранять guest login/console.
OS env sanitize в MCP gate означает, что Preview через MCP не заменяет local PowerShell.

### 6. Проверить функциональность и selected boundaries
Own CLI/Git synthetic, browser, GUI, clipboard и cleanup; затем строго выбранные owner-negative
probes без чтения содержимого чужих secrets. Все inconclusive оставить явными.

### 7. Отдельно оценить Repo
Проверить Windows launcher/control, Linux user/caps/mounts, source vs live Bridge,
не выдавать Dockerfile за полный набор container flags. E38 migration уже выполнена здесь.

### 8. Проверить normal stop и recovery
Ctrl+C в guest, адресные before/after fingerprints и MCP result. Один peer failure не покрывает
любые crash/logoff/descendants. При MCP 409 сначала проверить effect и существующий listener;
не делать blind restart.

### 9. Согласовать замену широкого route
Только явное owner решение, exact-instance guards, after-check. Выполненный E43
[Stop-LegacyOwnerHost.ps1](../runtime/host-g2/runtime-api-migration/Stop-LegacyOwnerHost.ps1)
одноразовый, журнал не удалять, на другую машину без review не переносить.

### 10. Зафиксировать решение и limits
Хранить raw evidence и отдельное accepted/scope/unknown; после нового runtime/ACL/scope
повторять только relevant gates. Изменение Markdown не есть deploy/install/publish.

## Что не является принятым итогом

- Полная гарантия всех маршрутов ChatGPT при независимо полномочных Repo и прочих connectors.
- Защита каждого owner asset/backup, clipboard bridge, процесса, token/handle, service/IPC.
- Невозможность восстановить старый owner HOST: его credentials и launcher сохранены.
- Готовая новая installed панель observability, постоянный audit log или runtime policy gate.
- Полный Docker inspect/daemon/network/version/vulnerability review.
- Универсальный launcher/installer с переносимыми SID, именами контейнеров, key и PID.
- Автоматический accepted PASS для произвольных crash/logoff и Windows owner runtime после E43.

## Source map (не инструкции немедленного Apply)

| Назначение | Источник | Ограничение |
|---|---|---|
| Guest entry | [start-g2-guest-session.ps1](../runtime/host-g2/runtime-api-migration/start-g2-guest-session.ps1) | Existing guest profile/key, default Preview |
| Environment gate | [g2-stdio-gate.py](../runtime/host-g2/g2-stdio-gate.py) | Не same-SID sandbox |
| Shared ACL | [protect-shared-runtime.ps1](../runtime/host-g2/protect-shared-runtime.ps1) | Exact machine SID/paths, owner-admin Apply |
| Current Repo AFTER launcher/control | [repo-run-tunnel.ps1](../runtime/host-g2/runtime-api-migration/repo-run-tunnel.ps1), [repo-control.ps1](../runtime/host-g2/runtime-api-migration/repo-control.ps1) | Именно эти pins доставлены E38; старые repo-mode copies BEFORE |
| Linux Bridge | [fortis-mcp-bridge.mjs](../runtime/repo-mode/fortis-mcp-bridge.mjs) | Source/live hash match E44, volume отдельно |
| Repo rollback procedure | [E38 recovery](G3_REPO_RUNTIME_ONLY_RECOVERY_2026-10-16.md) | Fixtures проверены, live rollback не выполнялся |
| Session prototypes | [window-isolation](../runtime/host-g2/window-isolation/README.md) | Исторические методы, private station conditional |
| Docker baseline examples | [Dockerfile](../runtime/repo-mode/Dockerfile), [config](../runtime/repo-mode/workspace-config.example.json) | Не задают реальные mounts/flags и credentials |

Не существует проверенного одношагового installer для provisioning guest account, keys,
Docker create и всего acceptance. Источник истины для нынешних operational commands — E42,
для решений — E43, для bounded Repo metadata — E44.

## Основания для технических механизмов

[Docker bind mounts](https://docs.docker.com/engine/storage/bind-mounts/),
[Windows permission requirements](https://docs.docker.com/desktop/setup/install/windows-permission-requirements/),
[Docker Engine security](https://docs.docker.com/engine/security/).
Они объясняют механизм, но не заменяют actual metadata или Windows acceptance.
