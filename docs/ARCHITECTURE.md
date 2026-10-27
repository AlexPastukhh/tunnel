# Архитектура: ChatGPT, native Tunnel, MCP, Sites и Broker

**Назначение:** единая карта компонентов и границ доверия. Даты, версии и фактическое состояние — в [CURRENT_STATE](CURRENT_STATE.md); запуск — в [OPERATIONS](OPERATIONS.md); идентификаторы hosted Sites — в [SITES](SITES.md).

## Действующие независимые контуры после E43

G2 native: отдельный Windows guest SID/login, narrow runtime → Python gate → Node MCP.
Own GUI/clipboard/browser/Workspace разрешены в bounded scope; owner GUI/private защищаются
в доказанных пределах. Old owner HOST остановлен E43, connector/key сохранены для recovery.

Repo native: Windows launcher от alexa → narrow API E38 → Docker UID1000.
Рабочие файлы — `/workspace/repo/Workfiles` во внутреннем Docker volume; это НЕ guest Windows SID. Прежние Windows binds ещё не отключены; актуальная граница и оставшийся шаг — в security-реестре.
Hosted Sites и Snapshot Broker — независимые authority/routes, не whole-chat isolation.
[Итог и source map](ISOLATION_GUIDE.md), [E44](G3_DOCS_CONSOLIDATION_AND_REPO_BOUNDARY_2026-10-16.md).

## Историческая схема до E43 (не считать live)

> Следующая схема и слова о непринятом G2 относятся к этапу ДО решения E43.
> Сохранено для истории; текущая инструкция находится в E42/E43.

#### Прежние четыре поверхности

```text
ChatGPT
  ├─ native HOST Tunnel ─ tunnel-client ─ Desktop Commander (Windows)
  ├─ native Fortis Repo ─ tunnel-client ─ docker exec ─ MCP Bridge
  │                                                    └─ Desktop Commander (Linux container)
  │                                                        ├─ /workspace/repos  [Windows bind, RW]
  │                                                        ├─ /workspace/files  [Windows bind, RW]
  │                                                        └─ /workspace/repo   [Docker volume]
  ├─ HOST Site ─ hosted Worker /mcp ─ configured upstream (HOST route)
  └─ Repo Site ─ hosted Worker /mcp ─ upstream gate (не активирован на проверке)
```

Это схема **маршрутов**, не доказательство доступности каждого компонента в данный момент. Site → upstream существует лишь при фактической настройке/подключении Site. Native HOST и native Repo **не проходят автоматически** через соответствующие Sites.

#### Native HOST

Профиль `desktop-commander` запускает доверенную Windows-обёртку и Desktop Commander. Исполнение файловых и терминальных операций происходит **на HOST Windows**. Ни `project root` hosted Site, ни инструкции модели не превращают это подключение в sandbox. Где расположен launcher и как остановить профиль — [OPERATIONS](OPERATIONS.md). Реальные разрешения определяются Windows-процессом, ACL и настройками инструмента — [ACCESS](ACCESS.md).

#### Restricted G2 — отдельный guest Windows-контекст

G2 использует отдельную test auth/profile под SID1009/non-admin. В прежней конфигурации реальный
MCP chain принят; конечный runtime в отдельной guest Windows-сессии ещё не принят.
Схема выше перечисляет исходные owner/Site routes и не является доказательством работающего G2.

Простая session-based схема предпочитается как Candidate. Граница защищает owner данные/GUI/control,
сохраняя собственные guest GUI/clipboard, процессы, browser state и нужную сеть.
Точная политика и критерии — [в плане](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md), причина выбора — [в session decision](G3_SESSION_BOUNDARY_OUTCOME_DECISION_2026-10-15.md).

Отдельная Windows-сессия не является TCP loopback авторизацией и не ограничивает другие ChatGPT tools.
Запрет Windows SID1009 не ограничивает независимый Repo RW mount.
Наличие owner HOST/Repo в том же чате требует отдельной оценки whole-chat guarantee;
оно не меняет доказанный scope самого guest Windows-процесса.

#### Native Fortis Repo

**Актуально после WF-036–048 (25.10.2026):** два независимо идентифицированных Windows Repo Tunnel (`repo-mode` и `repo-mode-plus2`) идут через `docker exec` сразу в **Direct Linux Desktop Commander** `/opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js` внутри `fortis-repo-test`. В read-only `/proc` последнего аудита — **2 Direct, 0 активных legacy Bridge**. Второй профиль браузера **не** означает второй контейнер или изоляцию UID/файлов. Docker bind mounts дают доступ к тем же Windows-файлам; `/workspace/repo` — отдельный writable Docker volume, **не** синоним `/workspace/repos`. Актуальная схема, доказательства и остаточные риски — [TUNNEL_SECURITY_ISOLATION](agent-workflow/TUNNEL_SECURITY_ISOLATION.md).

**Исторически (до двух Direct)** профиль `repo-mode` запускал `docker exec -i fortis-repo-test node /workspace/repo/.fortis/mcp-bridge.mjs`. Этот **legacy** Bridge всё ещё лежит в writable-parent каталоге и может быть подменён, поэтому **НЕ использовать эту команду как fallback/runbook**. Датированная [source-копия](../runtime/repo-mode/fortis-mcp-bridge.mjs) меняла `initialize`/`tools/list` presentation; это не гарантия политики `tools/call`, и Git source ≠ установленный runtime. Удаление только после независимого Direct recovery, под контролем владельца.

Для Repo реальные нижние границы доступа задаются Docker mounts, user/permissions и сетью. Ограничение `allowedDirectories` отдельных MCP file tools не ограничивает автоматически shell-процессы. Подробности — [ACCESS](ACCESS.md).

#### Hosted HOST Site и Repo Site

Site — отдельный размещённый MCP proxy с диагностической веб-страницей; интерактивная MCP App-карточка — иной механизм. Hosted Worker не имеет прямого Windows FS/stdio и должен иметь поддерживаемый защищённый upstream-маршрут. Изменения Site публикуются независимо от native.

По [SITES](SITES.md) HOST Site использует отдельный upstream и проксирует MCP-сеанс. Repo Site имеет собственный gate; на проверке **12.10.2026** диагностический `repo_connection_status` вернул `configured=false`, `accessEnabled=false`, `connected=false`. Это не значит, что native Repo недоступен.

## Что происходит при MCP-вызове

1. ChatGPT получает описание инструментов через `initialize` и `tools/list` (в зависимости от маршрута и жизненного цикла клиента).
2. ChatGPT вызывает инструмент через `tools/call` и аргументы передаются соответствующему пути.
3. Native HOST исполняет вызов на Windows; **текущий native Repo — в Linux Docker через Direct DC (без Bridge)**, прежний Bridge — исторический маршрут; Site передаёт вызов своему upstream **только при настроенном пути**.
4. Успех/ошибка возвращается по тому же MCP-маршруту. При timeout результат мутации может быть неизвестен: **сначала проверить результат, не повторять слепо**.

`tools/list` показывает объявленный контракт, но не подтверждает доступность upstream, реальные OS-права или отсутствие альтернативного пути исполнения. Сама диагностическая страница /ui не является точкой авторизации.

## Границы безопасности и наблюдения

| Контур | Где должны обеспечиваться ограничения | Чего это не покрывает |
|---|---|---|
| HOST | Windows ACL / учётная запись процесса + обязательная проверка вызовов (если будет внедрена) | Docker-изоляция Repo не распространяется на HOST |
| Repo | Docker mounts/identity/network + ограничения доступного shell + обязательная проверка вызовов (если будет внедрена) | Файловый MCP allowlist сам по себе не ограничивает терминал |
| Hosted Site | Авторизация Site, upstream-auth, gate для **своего** маршрута | Нельзя заблокировать native-путь одним Site gate |
| Observatory P1/activity | Read-only диагностика, история метрик и инцидентов | Не блокирует вызовы и не гарантирует полный аудит |
| [Observatory V1](../observatory/v1/README.md) | Owner Bearer API, Host/Origin-проверки и scoped Notifier grant; Docker-архив отдельно | Не обязательный MCP gate; Repo/G2 не получают owner-полномочия от одного чтения архива |
| Broker / Bridge | Отдельная политика выбора/экспорта snapshot | Не ограничивает прямой доступ Repo к mounts |

**Принудительный audit/policy enforcement на всех native и Site путях пока не подтверждён как реализованный.** Проектируемые гарантии, модель событий и тесты — в [AUDIT](AUDIT.md). Не выдавать планы за работающие защиты.

## Кто владеет изменениями

- Фактические два Direct Repo, legacy Bridge и Windows launcher: [текущая security карта](agent-workflow/TUNNEL_SECURITY_ISOLATION.md), [INSTRUCTIONS](INSTRUCTIONS.md), [runtime](../runtime/README.md).
- Hosted Site source, version, tool schemas и deployment: [SITES](SITES.md), [WORKFLOW](WORKFLOW.md).
- Живые полномочия, ключи и сеть: [ACCESS](ACCESS.md).
- Дата/доказательства текущего состояния: [CURRENT_STATE](CURRENT_STATE.md).
- Snapshot — самостоятельный контур с ручным Broker: [SNAPSHOT](SNAPSHOT.md).
- Observatory V1 source/API, установленные версии и доказательства: [README V1](../observatory/v1/README.md).

Не менять лишние уровни вместе; одна ошибка Site или MCP-сессии не доказывает неисправность обоих native-туннелей.
