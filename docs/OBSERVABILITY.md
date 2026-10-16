# Наблюдаемость и планы GUI

## Текущее после E43

Old owner HOST намеренно offline; не считать это сбоем G2/Repo. E39 исправил
source discovery, но не обновил installed dashboard. Repo narrow сохраняет health/metrics,
не legacy full /ui и /api/logs. Это не permissions gate.
[Итог](ISOLATION_GUIDE.md), [E39](G3_REPO_MONITOR_DISCOVERY_2026-10-16.md).

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
