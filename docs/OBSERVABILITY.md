# Наблюдаемость и планы GUI

## Текущее после E43

Old owner HOST намеренно offline; не считать это сбоем G2/Repo. E39 исправил
source discovery, но не обновил installed dashboard. Repo narrow сохраняет health/metrics,
не legacy full /ui и /api/logs. Это не permissions gate.
[Итог](ISOLATION_GUIDE.md), [E39](G3_REPO_MONITOR_DISCOVERY_2026-10-16.md).

## Обновление source-dashboard после обнаруженного ложного TELEMETRY DOWN (16.10.2026)

Старый owner HOST остановлен в E43; обращение Observatory к устаревшему адресу 127.0.0.1:8080 порождало таймауты и ложный статус общей телеметрии. Новый исходник по умолчанию не опрашивает legacy HOST и показывает RETIRED; только явный OBS_LEGACY_HOST_ENABLED=1 возвращает исторический опрос. Repo UP доказывает лишь локальный health/identity, не доступность инструмента в каждом чате. G2 остаётся отдельной линией без отдельного постоянно работающего health-коллектора. После правки требуется перезапуск **только Observatory** для применения; runtime и ACL не менялись.

## Activity stream source-only, 2026-10-16

В Git добавлен [read-only activity_audit.py](../observatory/activity_audit.py)
и opt-in /api/activity для metadata по вызовам инструментов G2/Repo.
GUI не получает аргументы, полный командный текст, ответы или секреты.
Если источник недоступен, UI показывает unconfigured/unavailable, а не
ложный ноль операций. Метаданные G2 не становятся доступны owner
обходом ACL. Offline tests не заменяют native Windows acceptance.
Руководство по настройке: [Observatory](../observatory/README_DUAL_TUNNEL.md).
Установленный Windows P1, G2 gate и Repo MCP Bridge не изменялись.

## Датированная история (сохранена без удаления)

> E39, 16 октября: [автопоиск Repo исправлен](G3_REPO_MONITOR_DISCOVERY_2026-10-16.md). Причина — discovery timeout3s; теперь bounded15s и executable-name filter. Windows source collector автоматически UP/initialized без OBS_REPO_URL, Repo11 tests PASS. Известный старый P1 не содержит repo_monitor.py и не обновлялся. Его installation/GUI не приняты. Sampler wait5s — номинальная пауза между rounds; collection time увеличивает фактический интервал. Ниже E38 UNKNOWN — исходный baseline.

> Проверка E38, 16 октября: Repo переведён на runtime. Пinned source collector repo_monitor.py исполнен на Windows: explicit listener UP/initialized, automatic discovery UNKNOWN. Installed dashboard/GUI не проверены и source collector не менялся. [Evidence и ограничение](G3_REPO_RUNTIME_CUTOVER_2026-10-16.md). Метрики доступны; full /api/logs у Repo отсутствует. Это не подтверждение единого работающего dashboard всех туннелей.

**Рабочая реализация dual-tunnel GUI (12.10.2026):** исходники P1 без истории и логов скопированы в [observatory](../observatory/README_DUAL_TUNNEL.md). Добавлены Repo status/history API, независимая карточка и проверка идентичности listener. Шесть модульных/API-тестов прошли. На Windows выполнен read-only smoke: подтверждены HOST UP, Repo UP с проверенной identity и MCP initialized, HTTP 200 для пяти маршрутов (корень, snapshot, history, repo-status, repo-history). Визуальное отображение в браузере и установка ещё не проверены. Исходный P1 на Windows не заменялся. Аудит и кнопки управления не реализованы.

Observatory — read-only монитор, **не** обязательный MCP enforcement и не полный audit log. Для спецификации учёта/запрета вызовов — [AUDIT](AUDIT.md); для путей доступа — [ARCHITECTURE](ARCHITECTURE.md).

Локальные источники dashboard остаются:
- C:\Users\alexa\Documents\prot\observability-ui-prototype-0 — ранний fixture UI.
- C:\Users\alexa\Documents\prot\observability-ui-prototype-1 — read-only shadow dashboard P1.

P1 читает local health/metrics и обезличенные WARN/ERROR, sampler 5 секунд, rolling history 60 минут. Incidents собирают окно 2 минуты до/после, collecting→complete, сохраняются и экспортируются redacted ZIP. Запросы/промпты/транскрипты/ключи не должны попадать в диагностический экспорт.

Это отдельный out-of-band dashboard, не обязательный путь MCP и не инструмент изменения файлов/разрешений. После переноса репозиториев прежние prototype servers остановлены; не считать dashboard запущенным по наличию исходников.

P2 (автоматические сравнения/deltas) и request-level attribution/canary остаются планами. Подробная история реализации/расследований: history/prot/docs/observability и TUNNEL-OBSERVABILITY*.md.

Sandbox GUI/Windows Sandbox/VM описаны в старых isolation/sandbox-plugin планах. Они не развёрнуты как доступная GUI среда. Текущий Docker repo контур уже реализован, поэтому старое «изоляции ещё нет» относится к прошлой фазе или отдельному GUI плану, не к текущему Repo Docker.

Основной Windows GUI запрещён. Нельзя выдавать broad HOST MCP или диагностическую Site-страницу за GUI sandbox.

## Native G2 + Repo counters (source preview, 2026-10-16)

The read-only native metrics collector at observatory/dual_metrics.py
discovers Windows G2 by its exact guest SID, profile name and loopback
process-owned listener. It reads health + allowlisted Prometheus numbers
only, not keys, guest YAML, tool history or payloads. On inability to
verify G2 identity it reports UNKNOWN. Repo stays independently verified
by Repo tunnel identity; old owner HOST remains RETIRED.

API /api/tunnels and /api/g2-history + native route cards/60m command chart
were added. Historical HOST P1 widgets are folded away. Live guest-side
read-only health checks observed G2 and Repo both live/ready with
MCP initialized; no owner Windows installed-dashboard acceptance yet.
Do not treat local UP or polled command counts as chat-level delivery.
Preview instructions and limitations: observatory/README_DUAL_TUNNEL.md.

## User-downloadable safe telemetry history (source, 2026-10-16)

Observatory adds a local owner-only SQLite archive covering a rolling
90-day horizon, with max 1 native G2/Repo aggregate sample per route per
minute, plus metadata-only tool events from separately configured,
ACL-readable Desktop Commander histories. New UI exports all available or
date-filtered history as CSV/JSON inside ZIP, with a manifest.json for
coverage and omissions. Old records outside the previous 60m JSONL / rolling
DC files cannot be reconstructed. Full raw commands/chats/process descendants,
tamper-proof forensic logging, guest-only file access, and legacy E43
incident archives are intentionally excluded. New work does not adjust native
tunnel configurations, ACLs, keys, Docker mounts or G2 launchers. Apply by
restarting only the separate Windows Observatory preview after Git pull.
See observatory/README_DUAL_TUNNEL.md for details.

## E45 security finding: owner HTTP reachable from G2 (2026-10-16)

A read-only Windows G2 SID1009 request to owner Observatory 127.0.0.1:8093
returned HTTP 200. Loopback is shared by machine users, not SID-private.
The owner service can therefore respond to G2 even without guest access to
owner files. Host/Sec-Fetch-Site headers do not authenticate a Windows SID.

Before correction, SimpleHTTPRequestHandler.translate_path accepted parent
path segments and unrestricted static file names; synthetic path inspection
proved filesystem targets could resolve outside the Observatory root. Since
the server runs as owner alexa, this could expose owner-readable files to
a guest HTTP client. No such private files or secrets were read in this
investigation. Source-only correction now whitelists exactly index.html,
styles.css, and app.js for GET/HEAD and adds synthetic HTTP regressions.

IMPORTANT: static asset fix does NOT protect other unauthenticated HTTP API
routes (including downloads and owner-writable incident marks), and does NOT
update the running Windows server process. STOP the Windows 8093 Observatory
preview with Ctrl+C until owner-authenticated APIs / per-user IPC are reviewed
and approved. Do not change G2/Repo tunnels, ACL, keys or Docker.

Earlier G2 E19 scoped TCP/GET and E35/E38 selected native admin endpoint
checks never covered this later owner Observatory app; G3 owner IPC/API 5.8
remained PARTIAL. They do not prove generic localhost user isolation.
