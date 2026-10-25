# Где находится текущее состояние

Это указатель на владельцев фактов, не второй журнал релизов. Обновлён 26.10.2026 при упорядочивании документов; эта дата не является датой новой runtime-проверки.

| Контур | Текущий статус и план | Доказательства / эксплуатация |
| --- | --- | --- |
| Fortis Repo / Tunnel | [Security-реестр](agent-workflow/TUNNEL_SECURITY_ISOLATION.md), [STATE задач](agent-workflow/STATE.md) | [JOURNAL](agent-workflow/JOURNAL.md), [OPERATIONS](OPERATIONS.md) |
| Project Checker | [PLAN](userscript-updater/PLAN.md) | [Implementation log](userscript-updater/IMPLEMENTATION_LOG.md), [Windows boundary](userscript-updater/WINDOWS_TRUST_BOUNDARY.md), [source README](../runtime/userscript-updater/README.md) |
| Observatory / Notifier / Viewer | [README V1](../observatory/v1/README.md) | Там отдельно ведутся source, installed версии, проверки и открытые вопросы |
| Fortis G2 | [План и evidence E01–E44](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) | [E42 runbook](G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md), [E43 решение/retirement](G3_G2_SCOPE_ACCEPTANCE_AND_HOST_RETIREMENT_2026-10-16.md) |
| Hosted Sites | [SITES](SITES.md) | [WORKFLOW](WORKFLOW.md), [INSTRUCTIONS](INSTRUCTIONS.md) |
| Snapshot / Broker | [SNAPSHOT](SNAPSHOT.md) | [Broker runbook](../runtime/broker/README.md) |

## Как читать статус

Источник, тесты, установленная версия и реальное восстановление имеют разные evidence. Последний документированный результат не гарантирует текущую доступность процесса. Native Repo, G2 и Sites — независимые маршруты; успешная проверка одного не подтверждает другой.

Номера тестов, PID, SHA и milestone поддерживать у владельца компонента, здесь оставлять ссылку. Результаты обычной разработки Checker не требуется копировать в эту страницу.

## История

[Полный прежний текст CURRENT_STATE](CURRENT_STATE_HISTORY_20261026.md) сохранён с датированными результатами и прежними утверждениями. Он не источник текущего NEXT или команд восстановления. Новую хронологию вести в журнале соответствующей работы по [единому протоколу](agent-workflow/README.md).
