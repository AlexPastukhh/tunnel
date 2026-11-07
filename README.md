# Личные туннели и MCP-плагины

> **Граница документации:** этот репозиторий владеет Tunnel, Repo1/Repo2 workers и Windows Guards. Текущая топология общего Fortis Repo workspace, volumes, Fortis Approvals, GitHub credentials и Qwen integration теперь описывается в соседнем проекте `fortis-container` (`/workspace/repos/fortis-container/README.md`). Датированные документы Tunnel от 2026-10-16 сохраняются как история и не должны переопределять mount evidence от 2026-11-03.

Документация существующей инфраструктуры ChatGPT ↔ Windows HOST, Fortis Repo (Docker), независимых hosted Sites и Snapshot Bridge/Broker. **Этот репозиторий не является автоматически применяемой конфигурацией**: runtime и Sites обновляются отдельно.

**Начать здесь:** [Навигация по задачам](docs/README.md) · [Как устроена система](docs/ARCHITECTURE.md) · [Проверенное состояние](docs/CURRENT_STATE.md). Для AI-ассистента обязательны [AGENTS.md](AGENTS.md).

## Локальные Use Cases

[Реестр Tunnel](docs/use-cases/README.md) — Guards и reconnect. Общий workflow —
в [главном реестре Fortis](https://github.com/AlexPastukhh/fortis-container/blob/main/docs/use-cases/README.md).
Каждый новый чат читает полностью UC-CONT-002/003; весь каталог читать не нужно.

## По задаче

| Нужно | Документ |
|---|---|
| Проверенное, принятое, ограничения, повторная настройка | [ISOLATION_GUIDE](docs/ISOLATION_GUIDE.md) |
| Понять native Tunnel, MCP Bridge и роль Sites | [Архитектура](docs/ARCHITECTURE.md), [Sites](docs/SITES.md) |
| Проверить текущее состояние, не принять старый срез за live | [Текущее состояние](docs/CURRENT_STATE.md) |
| Продолжить Fortis G2: разрешения, доказательства и оставшаяся работа | [Актуальный план G2](docs/G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md), [решение о Windows-сессии](docs/G3_SESSION_BOUNDARY_OUTCOME_DECISION_2026-10-15.md) |
| Запустить, остановить, восстановить подключение | [Операции](docs/OPERATIONS.md) |
| Обновить Guard и Windows launchers после изменения Docker | [Git → Windows: безопасный reconnect](docs/FORTIS_GIT_WINDOWS_LAUNCHER_WORKFLOW.md) |
| Fortis Repo 1/2 из Script Center: Windows worker chain, runtime-зависимости и paired Git release | [Windows source mirror](runtime/windows-repo/README.md), [Defender / installed inventory](runtime/windows-repo/DEFENDER-AND-INSTALLED-INVENTORY.md) |
| Определить права, mounts, ключи и сетевые границы | [Доступ](docs/ACCESS.md) |
| Узнать, что логируется и как проектируется запрет операций | [Аудит и политика](docs/AUDIT.md) |
| Посмотреть диагностику и планы GUI | [Наблюдаемость](docs/OBSERVABILITY.md) |
| Создать плагин / обновить существующие компоненты | [Создание](docs/WORKFLOW.md) / [Обновление](docs/INSTRUCTIONS.md) |
| Пользоваться Snapshot Bridge / Broker | [Snapshot](docs/SNAPSHOT.md), [Broker runbook](runtime/broker/README.md) |
| Найти происхождение файлов / историю переноса | [Provenance](docs/PROVENANCE.md), [Migration](docs/MIGRATION.md) |
| Планируемые улучшения и технический долг | [Backlog](docs/BACKLOG-IMPROVEMENTS.md) |

## Зеркальная директория Fortis Repo (Git, не bind mount)

Папка проекта в Docker — `/workspace/repo/Repos/<repo>` (то же место, что `/workspace/repos/<repo>`). Соответствующий Windows Git-клон — `%USERPROFILE%\Repos\<repo>`. Для Fortis Repo 1/2 Script Center и Tunnel — **два соседних клона** `%USERPROFILE%\Repos\script-control-center` и `%USERPROFILE%\Repos\tunnel`: первый содержит UI и тонкие адаптеры, второй — единственный Windows worker/launcher source mirror. **Это отдельные файловые системы, не общая папка:** обмен происходит только через `git commit/push` из Docker и упорядоченный `git pull --ff-only` на Windows (`tunnel`, затем `script-control-center`). Незакоммиченные изменения не зеркалируются. Windows-клоны и ярлык не обновляются автоматически. Никогда не монтировать Windows `Repos` как обход схемы Git-продвижения. Подробности — [Fortis Windows Git launcher workflow](docs/FORTIS_GIT_WINDOWS_LAUNCHER_WORKFLOW.md) и [Windows source mirror](runtime/windows-repo/README.md).

## Где истина

- Реальные права определяются **действующим** Windows/Docker runtime, ACL, mounts, конфигурацией и доступностью маршрута; Markdown — документированный срез, не enforcement.
- Hosted Site имеет собственный исходный код и deployment в Sites Git, отдельно от native Tunnel. Site не обязателен для native-доступа.
- `runtime/` — датированные копии исходников, не автодеплой. [Подробнее](runtime/README.md).
- `history/` — неизменённая история, а не текущая инструкция. [Подробнее](history/README.md).
- Для динамических параметров перед действиями обязательна read-only сверка с live-системой. Не публиковать ключи, приватные URL и payload-логи в Git.
