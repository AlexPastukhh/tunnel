# Архитектура: ChatGPT, native Tunnel, MCP, Sites и Broker

> **HISTORICAL BASELINE — 2026-10-16.** Этот документ сохраняет прежнюю архитектуру G2/Repo и её границы. Описания `/workspace/repos` и `/workspace/files` как Windows RW mounts устарели для текущего Fortis Repo: mountinfo от 2026-11-03 показывает подкаталоги общего ext4 `fortis-repo-workspace` volume. Текущая карта — `/workspace/repos/fortis-container/docs/ARCHITECTURE.md` и `CONTAINERS-AND-VOLUMES.md`.

**Назначение:** единая карта компонентов и границ доверия. Даты, версии и фактическое состояние — в [CURRENT_STATE](CURRENT_STATE.md); запуск — в [OPERATIONS](OPERATIONS.md); идентификаторы hosted Sites — в [SITES](SITES.md).

## Действующие независимые контуры после E43

G2 native: отдельный Windows guest SID/login, narrow runtime → Python gate → Node MCP.
Own GUI/clipboard/browser/Workspace разрешены в bounded scope; owner GUI/private защищаются
в доказанных пределах. Old owner HOST остановлен E43, connector/key сохранены для recovery.

Repo native: Windows launcher от alexa → narrow API E38 → Docker UID1000.
Текущая Docker topology: named volume `fortis-repo-workspace` подключён RW к `/workspace/repo`, `/workspace/repos` и `/workspace/files`; последние два пути — subpaths `Repos` и `Workfiles`. Отдельный named volume `fortis-r7-client` подключён RO к `/run/fortis-client`. Это не Windows bind mounts и не guest Windows SID. См. актуальную карту в рабочем checkout: `/workspace/repos/fortis-container/docs/CONTAINERS-AND-VOLUMES.md`.
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

Профиль `repo-mode` запускает `docker exec -i fortis-repo-test node /workspace/repo/.fortis/mcp-bridge.mjs`. Установленный MCP Bridge запускает Linux Desktop Commander; файловые операции с bind mounts изменяют соответствующие Windows-файлы. `/workspace/repo` — отдельный volume, **не** синоним `/workspace/repos`.

В датированной копии [fortis-mcp-bridge.mjs](../runtime/repo-mode/fortis-mcp-bridge.mjs) Bridge изменяет `initialize`/`tools/list` presentation, убирает legacy UI-ресурсы и передаёт остальные запросы upstream. Это **не подтверждает** наличие полноценной политики разрешений или аудита на каждый `tools/call`. Копия в Git не равна установленной версии: перед изменениями сравнить с live и применить по [INSTRUCTIONS](INSTRUCTIONS.md).

Для Repo реальные нижние границы доступа задаются Docker mounts, user/permissions и сетью. Ограничение `allowedDirectories` отдельных MCP file tools не ограничивает автоматически shell-процессы. Подробности — [ACCESS](ACCESS.md).

#### Hosted HOST Site и Repo Site

Site — отдельный размещённый MCP proxy с диагностической веб-страницей; интерактивная MCP App-карточка — иной механизм. Hosted Worker не имеет прямого Windows FS/stdio и должен иметь поддерживаемый защищённый upstream-маршрут. Изменения Site публикуются независимо от native.

По [SITES](SITES.md) HOST Site использует отдельный upstream и проксирует MCP-сеанс. Repo Site имеет собственный gate; на проверке **12.10.2026** диагностический `repo_connection_status` вернул `configured=false`, `accessEnabled=false`, `connected=false`. Это не значит, что native Repo недоступен.

## Что происходит при MCP-вызове

1. ChatGPT получает описание инструментов через `initialize` и `tools/list` (в зависимости от маршрута и жизненного цикла клиента).
2. ChatGPT вызывает инструмент через `tools/call` и аргументы передаются соответствующему пути.
3. Native HOST исполняет вызов на Windows; native Repo — в Docker через Bridge; Site передаёт вызов своему upstream **только при настроенном пути**.
4. Успех/ошибка возвращается по тому же MCP-маршруту. При timeout результат мутации может быть неизвестен: **сначала проверить результат, не повторять слепо**.

`tools/list` показывает объявленный контракт, но не подтверждает доступность upstream, реальные OS-права или отсутствие альтернативного пути исполнения. Сама диагностическая страница /ui не является точкой авторизации.

## Границы безопасности и наблюдения

| Контур | Где должны обеспечиваться ограничения | Чего это не покрывает |
|---|---|---|
| HOST | Windows ACL / учётная запись процесса + обязательная проверка вызовов (если будет внедрена) | Docker-изоляция Repo не распространяется на HOST |
| Repo | Docker mounts/identity/network + ограничения доступного shell + обязательная проверка вызовов (если будет внедрена) | Файловый MCP allowlist сам по себе не ограничивает терминал |
| Hosted Site | Авторизация Site, upstream-auth, gate для **своего** маршрута | Нельзя заблокировать native-путь одним Site gate |
| Observatory | Read-only диагностика, история метрик и инцидентов | Не блокирует вызовы и не гарантирует полный аудит |
| Broker / Bridge | Отдельная политика выбора/экспорта snapshot | Не ограничивает прямой доступ Repo к mounts |

**Принудительный audit/policy enforcement на всех native и Site путях пока не подтверждён как реализованный.** Проектируемые гарантии, модель событий и тесты — в [AUDIT](AUDIT.md). Не выдавать планы за работающие защиты.

## Кто владеет изменениями

- Фактические профили, контейнер, Bridge и Windows launcher: [INSTRUCTIONS](INSTRUCTIONS.md), [runtime](../runtime/README.md).
- Hosted Site source, version, tool schemas и deployment: [SITES](SITES.md), [WORKFLOW](WORKFLOW.md).
- Живые полномочия, ключи и сеть: [ACCESS](ACCESS.md).
- Дата/доказательства текущего состояния: [CURRENT_STATE](CURRENT_STATE.md).
- Snapshot — самостоятельный контур с ручным Broker: [SNAPSHOT](SNAPSHOT.md).

Не менять лишние уровни вместе; одна ошибка Site или MCP-сессии не доказывает неисправность обоих native-туннелей.
