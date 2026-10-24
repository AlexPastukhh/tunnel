# Личные туннели и MCP-плагины

Документация существующей инфраструктуры ChatGPT ↔ Windows HOST, Fortis Repo (Docker), независимых hosted Sites и Snapshot Bridge/Broker. **Этот репозиторий не является автоматически применяемой конфигурацией**: runtime и Sites обновляются отдельно.

**Начать здесь:** [Навигация по задачам](docs/README.md) · [Как устроена система](docs/ARCHITECTURE.md) · [Проверенное состояние](docs/CURRENT_STATE.md). Для AI-ассистента обязательны [AGENTS.md](AGENTS.md).

## По задаче

| Нужно | Документ |
|---|---|
| Общий workflow агентов: требования, текущее состояние, план и журнал | [Точка входа](docs/agent-workflow/README.md), [текущий шаг](docs/agent-workflow/STATE.md) |
| Проверенное, принятое, ограничения, повторная настройка | [ISOLATION_GUIDE](docs/ISOLATION_GUIDE.md) |
| Понять native Tunnel, MCP Bridge и роль Sites | [Архитектура](docs/ARCHITECTURE.md), [Sites](docs/SITES.md) |
| Проверить текущее состояние, не принять старый срез за live | [Текущее состояние](docs/CURRENT_STATE.md) |
| Продолжить Fortis G2: разрешения, доказательства и оставшаяся работа | [Актуальный план G2](docs/G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md), [решение о Windows-сессии](docs/G3_SESSION_BOUNDARY_OUTCOME_DECISION_2026-10-15.md) |
| Запустить, остановить, восстановить подключение | [Операции](docs/OPERATIONS.md) |
| Определить права, mounts, ключи и сетевые границы | [Доступ](docs/ACCESS.md) |
| Узнать, что логируется и как проектируется запрет операций | [Аудит и политика](docs/AUDIT.md) |
| Продолжить защищённое обновление Tampermonkey userscripts | [Требования, план и хендофф](docs/userscript-updater/README.md) |
| Работать с сессиями, архивом и командами Observatory | [Observatory V1](observatory/v1/README.md) |
| Посмотреть диагностику и планы GUI | [Наблюдаемость](docs/OBSERVABILITY.md) |
| Создать плагин / обновить существующие компоненты | [Создание](docs/WORKFLOW.md) / [Обновление](docs/INSTRUCTIONS.md) |
| Пользоваться Snapshot Bridge / Broker | [Snapshot](docs/SNAPSHOT.md), [Broker runbook](runtime/broker/README.md) |
| Найти происхождение файлов / историю переноса | [Provenance](docs/PROVENANCE.md), [Migration](docs/MIGRATION.md) |

## Где истина

- Реальные права определяются **действующим** Windows/Docker runtime, ACL, mounts, конфигурацией и доступностью маршрута; Markdown — документированный срез, не enforcement.
- Hosted Site имеет собственный исходный код и deployment в Sites Git, отдельно от native Tunnel. Site не обязателен для native-доступа.
- `runtime/` — датированные копии исходников, не автодеплой. [Подробнее](runtime/README.md).
- `history/` — неизменённая история, а не текущая инструкция. [Подробнее](history/README.md).
- Для динамических параметров перед действиями обязательна read-only сверка с live-системой. Не публиковать ключи, приватные URL и payload-логи в Git.
