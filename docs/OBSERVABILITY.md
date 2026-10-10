# Наблюдаемость и планы GUI

Локальные источники dashboard остаются:
- C:\Users\alexa\Documents\prot\observability-ui-prototype-0 — ранний fixture UI.
- C:\Users\alexa\Documents\prot\observability-ui-prototype-1 — read-only shadow dashboard P1.

P1 читает local health/metrics и обезличенные WARN/ERROR, sampler 5 секунд, rolling history 60 минут. Incidents собирают окно 2 минуты до/после, collecting→complete, сохраняются и экспортируются redacted ZIP. Запросы/промпты/транскрипты/ключи не должны попадать в диагностический экспорт.

Это отдельный out-of-band dashboard, не обязательный путь MCP и не инструмент изменения файлов/разрешений. После переноса репозиториев прежние prototype servers остановлены; не считать dashboard запущенным по наличию исходников.

P2 (автоматические сравнения/deltas) и request-level attribution/canary остаются планами. Подробная история реализации/расследований: history/prot/docs/observability и TUNNEL-OBSERVABILITY*.md.

Sandbox GUI/Windows Sandbox/VM описаны в старых isolation/sandbox-plugin планах. Они не развёрнуты как доступная GUI среда. Текущий Docker repo контур уже реализован, поэтому старое «изоляции ещё нет» относится к прошлой фазе или отдельному GUI плану, не к текущему Repo Docker.

Основной Windows GUI запрещён. Нельзя выдавать broad HOST MCP или диагностическую Site-страницу за GUI sandbox.
