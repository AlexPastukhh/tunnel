# Fortis_M — documentation hub

Статус: базовая структура создана 2026-10-07.

Цель этого каталога — отделить эксплуатационную документацию от длинных рабочих планов и прототипов.

## Разделы

### Tunnel
[docs/tunnel/README.md](tunnel/README.md)

Текущая рабочая схема Secure MCP Tunnel, запуск, остановка, health checks, связь с ChatGPT connector и runbook ротации runtime key.

### Observability GUI
[docs/observability/README.md](observability/README.md)

Состояние GUI, Prototype 0, ссылки на подробный prototype track и правила безопасного подключения к live telemetry.

### Isolation
[docs/isolation/README.md](isolation/README.md)

Модель границ доступа: Repo Mode, HOST Maintenance, временные grants и связь с Sandbox GUI.

### Sandbox plugin
[docs/sandbox-plugin/README.md](sandbox-plugin/README.md)

Место для документации отдельного Sandbox Control plugin/broker.

План реализации: [docs/sandbox-plugin/PLAN.md](sandbox-plugin/PLAN.md)

## Подробные рабочие документы

Пока не переносим их, чтобы не ломать историю и ссылки:
- [../ENVIRONMENT-ROADMAP.md](../ENVIRONMENT-ROADMAP.md)
- [../SECURE-ACCESS-CONTROL-PLAN.md](../SECURE-ACCESS-CONTROL-PLAN.md)
- [../SANDBOX-GUI-PLAN.md](../SANDBOX-GUI-PLAN.md)
- [../TUNNEL-OBSERVABILITY-PLAN.md](../TUNNEL-OBSERVABILITY-PLAN.md)
- [../TUNNEL-OBSERVABILITY-GUI-PROTOTYPES.md](../TUNNEL-OBSERVABILITY-GUI-PROTOTYPES.md)

## Правило документации

`docs/` отвечает на вопрос «как это сейчас устроено и как этим пользоваться».
Длинные *PLAN* документы отвечают на вопрос «что и почему мы ещё собираемся построить».