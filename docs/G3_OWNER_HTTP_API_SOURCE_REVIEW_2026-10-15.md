# G3 — source-only review локального owner HTTP API, 2026-10-15

**Статус: анализ исходников завершён; исправление не применено; G3 BLOCKED.**
Результат этого этапа — точная карта маршрутов и обоснованный выбор следующей проверки.
Это не Windows acceptance и не разрешение менять действующие owner HOST/Repo.

## Основание и границы

Прочитаны handoff, инструкции checkout и релевантные G3 evidence. Fortis Repo доступен как Linux UID/GID1000.
Прямое чтение mountinfo подтвердило RW bind /Users/alexa/Repos → /workspace/repos,
RW bind /Users/alexa/Workfiles → /workspace/files и отдельный ext4 Docker volume → /workspace/repo.
Строка C:\\134 в get_config — источник 9p; сама по себе она не задаёт корневой Windows каталог mount.
Checkout: /workspace/repos/tunnel, HEAD 5627ce9. Прежние tracked/untracked изменения сохранены.

Публичные исходники openai/tunnel-client получены через read-only GitHub connector по точному commit
`a390c168ff1b2d14e73a95991c186c6aba3ff5a0` (версия из прежнего evidence: v0.0.15).
Ни текущая версия двух owner EXE, ни их соответствие этим исходникам заново не проверены.
Поэтому вывод о структуре кода нельзя выдавать за новое наблюдение live Windows.
Предыдущий guest GET200 — самостоятельное реальное evidence из
[G3_LIVE_OWNER_LISTENERS](G3_LIVE_OWNER_LISTENERS_2026-10-15.md), без чтения тела ответа.

## Findings

### F1 — local guard не устанавливает Windows identity

`GuardedMux` применяет `LocalOnly`; `IsLoopbackRequest` проверяет RemoteAddr/IP либо Unix transport.
Проверки SID, Windows SessionId, локального bearer key или клиентского сертификата здесь нет.
`SameOriginUnsafe` защищает от части browser CSRF, но пропускает native-клиент без Origin/Referer
и без Sec-Fetch-Site: cross-site. Это согласуется с уже наблюдавшимся guest GET200.
Не доказаны live PUT, изменение настроек, выполнение owner-команд или полный захват HOST.

### F2 — требуется закрыть и управляющие, и чувствительные read-маршруты

Full app регистрирует adminui на общем health/admin mux. В нём 20 шаблонов маршрутов.
Некоторые диагностические handlers вообще не ограничивают HTTP method; GET ниже означает
основное назначение, а не гарантированный запрет остальных методов.

| Путь | Method в handler / назначение | Значение для G3 |
|---|---|---|
| /, /ui, /ui/ | UI index через шаблон /; отдельной method-проверки нет | UI не является авторизацией; закрыть для guest вместе с admin поверхностью |
| /assets/, /favicon.ico | UI assets / 204; отдельные правила asset server | Не самостоятельное доказательство защиты API |
| /api/status | Нет method-проверки; GET status | В коде есть private upstream URL, tunnel metadata и channel сведения; не разрешать guest по названию status |
| /api/system | Нет method-проверки; GET snapshot | TLS/proxy identity/health/probe сведения; не public health |
| /api/oauth | Нет method-проверки; GET snapshot | OAuth discovery сведения; чувствительность требует отдельной оценки |
| /api/logs, /api/logs/stream | Нет method-проверки; JSON / SSE | Owner logs; redaction не доказывает отсутствие всех приватных данных |
| /api/logs/export | Нет method-проверки; archive generation | Собирает logs, runtime/config metadata, metrics, admin snapshots; не вызывать на live даже для status-only smoke |
| /api/log-level | GET, PUT; иначе 405 и Allow: GET, PUT | GET exposure подтверждён ранее; PUT меняет controller в исходнике, но на live не проверялся |
| /api/harpoon/status, /api/harpoon/targets, /api/harpoon/calls | Нет method-проверки; GET snapshots | Метаданные targets и calls; закрыть guest до доказательства безопасного состава |
| /api/codex/status, /api/codex/events, /api/codex/events/stream | Только GET | Bridge status/events; не безопасная общая диагностика |
| /api/codex/login/device, /api/codex/login/cancel | Только POST + SameOriginUnsafe | Запуск/отмена login через bridge; никаких live проб |
| /api/codex/thread/start, /api/codex/turn/start | Только POST + SameOriginUnsafe | Передают параметры thread/turn в bridge; никаких live проб |

`PUT /api/log-level` зарегистрирован через обычный loopback guarded handler без
дополнительного `adminSameOriginUnsafe`. Даже добавление такого CSRF wrapper не ограничило бы
native SID1009: оно не проверяет Windows identity.

Codex handlers принимают CWD, approval/sandbox параметры и prompt; это существенная
управляющая поверхность по исходникам. Наличие работоспособного Codex bridge, его credentials,
допустимых режимов и реальный эффект на owner Windows этим review НЕ установлены.

### F3 — OPENAI_ADMIN_KEY не защищает local adminui

`pkg/config/admin.go` загружает ключ для CLI управления удалённым control plane.
Local `adminui.registerRoutes` не использует этот AdminConfig. Нельзя предлагать
`--admin-key` как исправление локального межпользовательского доступа.

### F4 — готового full-client переключателя «только admin off» здесь нет

В проверенных RegisterFlags, AdminUIConfig и wiring нет отдельного CLI/env параметра
для отключения или аутентификации только local adminui при сохранении health TCP listener.
`allow-remote-ui=false` сохраняет доступ всех локальных пользователей.
`open-web-ui=false` управляет открытием браузера, а не регистрацией API.
Малый log buffer, выключенный payload capture или случайный порт не являются границей SID.

`app.RuntimeOptions.DisableHealthAdmin` существует для embedders: он исключает весь health/admin
listener и adminui. Обычная команда run вызывает `app.New` с обычными RuntimeOptions;
этот embedder option не является доступным флагом работающего full EXE и не даёт hot disable.
Штатного hot reload policy для этих routes в просмотренном wiring не обнаружено.

### F5 — runtime-only оставляет диагностическую поверхность

Runtime graph не включает adminui/Codex/full-client UI. Это поддерживает прежний synthetic
результат отсутствия выбранных admin routes, но не доказывает совместимость owner profiles.

| Поверхность runtimehealth | Что следует из кода | Решение до отдельной проверки |
|---|---|---|
| /healthz | Статическое тело live | Кандидат для доступной guest liveness |
| /readyz | Может возвращать dependency reason и строку ошибки | Status-only диагностика допустима как кандидат; безопасность тела отдельно не доказана |
| /health, /health/… | Loopback-only component snapshots; details query может переопределить default | Не считать public-safe из-за health.show-details=false |
| /metrics | Prometheus exporter | Метки и metadata требуют отдельной оценки; отсутствие admin routes их не скрывает |
| /harpoon/mcp | Optional HTTP streamable transport в обоих graphs | Требуется явно отключить, если он не нужен; это отдельная поверхность |

В `readinessStatus` sanitizer ошибки только обрезает пробелы. Нельзя утверждать, что
readyz body автоматически удаляет private URL или все чувствительные сведения.
`health.show-details=false` — default представления, а не запрет `?details=true`.
Дополнительный Harpoon transport регистрируется ровно как `/harpoon/mcp`;
проверка только /harpoon или /mcp его не покрывает.
Пустой `--harpoon.additional-transport=` имеет приоритет над inherited env в parser;
его прежний synthetic Windows тест уже есть — повторять без изменения гипотезы не нужно.

## Proposals — Candidate, не committed rollout

| Вариант | Польза / ограничения / стоимость | Статус |
|---|---|---|
| Сохранить live owner HOST/Repo на время анализа | Сохраняет чаты; обнаруженный admin GET доступ остаётся открытым | Текущий разрешённый режим; не remediation |
| Официальный runtime-only по одному owner route | Удаляет adminui из graph и сохраняет MCP/health; binary уже staged и synthetic tests есть. Нужны profile compatibility, независимый backup/rollback и согласованный restart каждого route | Предпочтительный Candidate для isolated compatibility review; production не одобрено |
| Точный auth/policy gate внутри full-client listener | Сохраняет full UI для owner и может оставить выбранные health routes. Нужны отдельный build, credentials boundary, тесты и дальнейшая поддержка | Альтернатива, если full-only функции действительно необходимы |
| Proxy перед прежним full TCP listener | Сам по себе не закрывает исходный прямой localhost порт | Не считать исправлением |
| Full client через Unix socket | Есть конфигурационный параметр; Windows совместимость, защита socket и совместимость monitor/launchers здесь не проверены; меняется доступ ко всему listener | Не выбран; нельзя объявлять более простым доказанным решением |

Не менять firewall, mounts, owner/session ACL, общий Tunnel или все три launcher files.
Нельзя считать guest-only переход G2 на runtime защитой owner full listener.
Минимальный rollout определяется числом опасных owner listeners: каждый доступный full listener
должен получить собственную доказанную защиту. Один исправленный route не закрывает другой.
Сначала isolated compatibility review; live profile/PID mapping потребуется только перед consequential change.
Отсутствие full-only возможностей в текущем owner сценарии пока неизвестно.

## Candidate Verification Plan — согласован с текущей целью

Текущая очередь и необходимость тестов — подпункты 4 [плана](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md).
1. Использовать карту реальных routes и pinned graph; 404 несуществующего endpoint не доказывает закрытие других.
2. Для неизменного narrow artifact с исключённым admin-модулем использовать уже пройденные fixtures,
   manifest/hash и source graph. Не перебирать все paths × methods заново без конкретного Evidence Gap.
   Новый auth/policy gate требует своих isolated controls до handler; реальные owner profiles/keys не используются.
3. Защищать dangerous owner functions и sensitive data. Safe diagnostic GET может быть ALLOW
   при доказанном составе и соответствии live версии. В reviewed source GET /api/log-level возвращает
   current/supported logging levels; PUT меняет owner state и оценивается отдельно.
   405/400/500 либо connection failure не являются доказательством authorization DENY.
4. Перед отдельно одобренным owner change подтвердить PID/SID/CreationDate/EXE hash/version/profile mapping,
   без secret argv/env/keys. Применять только single-route Preview/backup/rollback.
5. После изменения — owner MCP/health и guest safe status-only negative на нужных protected GET routes.
   Не читать owner admin bodies, не вызывать live export/streams/PUT/POST.
   Отсутствие mutating surface обосновывать reviewed artifact и isolated evidence.
6. Оба exposed owner listeners должны иметь нужную защиту; другой route не менять попутно.
   Уже пройденные Harpoon override, generic MCP и runtime ACL tests не повторять без изменённой базы.

Guest own GUI/clipboard разрешены; owner negative capability тесты остаются.
Ручной guest login принят; unattended cold boot не является обязательным gate.
G4–G6 этим source review не приняты. [Прежняя verification редакция](G2_G3_SUPERSEDED_GUIDANCE_2026-10-15.md#api_review_verification)
сохранена как историческая; source Findings и первичные blob IDs ниже/выше не менялись.

## Review Limitations и доставка исходного source review

Проверены исходники точного commit и согласованность отчёта с registrations.
Нет нового native Windows evidence, полной проверки зависимостей, проверки установленного full EXE,
нового HTTP traffic к owner, запуска/остановки Windows процессов, ACL/network/task/service изменений.
Не читались secrets, profiles, logs, owner clipboard/screen или live admin bodies.
Не выполнены commit/push/deployment и production migration.

При исходном source review изменены только этот отчёт и короткие ссылки на него в CURRENT_STATE/INSTRUCTIONS.
При последующем согласовании документации уточнён Candidate Verification Plan; текущая доставка описана в CURRENT_STATE.
Отчёт не является исполняемым enforcement. G3 остаётся BLOCKED.

## Первичные исходники

Все ссылки ниже закреплены на одном commit; blob ID — Git SHA-1, не SHA256 EXE.

| Файл | Blob ID |
|---|---|
| [pkg/app/app.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/app/app.go) | 7fead300f78cf29bff14db134d67fd4cca61eb53 |
| [pkg/adminui/fxmodule.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/adminui/fxmodule.go) | c52e93e09eaf624cd4c579e442925ac13e9fd9d7 |
| [pkg/httpguard/guard.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/httpguard/guard.go) | 349b878d86c9134070375c4c5ed3db5f193b49e4 |
| [pkg/adminui/log_level.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/adminui/log_level.go) | 4826209d3f0714ee15b6b720b5eecf06eebe3bfb |
| [pkg/adminui/codex.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/adminui/codex.go) | 21ce06433f8d169a507d49a4a6731b6aeaf4ca2b |
| [pkg/adminui/ui.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/adminui/ui.go) | 7b73c84dc44348d29a14b5f4bbf63684b458e66e |
| [pkg/adminui/system.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/adminui/system.go) | a2c774dbb614a4220709b6e07c2121d98e3d8306 |
| [pkg/adminui/log_export.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/adminui/log_export.go) | 8c55021fabc539ef113c64a7896d2978c8f1d1fc |
| [pkg/adminui/harpoon.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/adminui/harpoon.go) | a1f294dc72f58edabf71f83c845be15aea845ddf |
| [pkg/config/config.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/config/config.go) | 06cfb2a444bc977e98f6dfaf9bae0d38ba386944 |
| [pkg/config/admin.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/config/admin.go) | fd60738caa91273c382af265e13afcfb1bce8cf7 |
| [cmd/client/run_command.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/cmd/client/run_command.go) | b6798c8ab2e5ffe6b01d31bad426a066ce768ff8 |
| [pkg/runtimeapp/app.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/runtimeapp/app.go) | 8dbaba54c0339da3ca2af54cf921164c835d9c48 |
| [pkg/runtimeconfig/config.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/runtimeconfig/config.go) | a724464b28ed9684da6c8f6573474afd82c0e559 |
| [pkg/runtimehealth/health.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/runtimehealth/health.go) | dac598f1c816adf81261255c295d2a3ee30f89bc |
| [pkg/runtimehealth/components.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/runtimehealth/components.go) | d05674e821cf1c7e71a5874908a38a42693d8333 |
| [pkg/runtimeharpoon/shared_wiring.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/runtimeharpoon/shared_wiring.go) | 5c6496d7fa476c345859414492ffdd2cec8ba0c7 |
