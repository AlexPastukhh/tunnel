# Навигация по инфраструктуре

> **Актуальная граница:** для текущей карты Fortis Repo volumes/mounts, Fortis Approvals, AI integrations, machine authorization, GitHub credential stores и общего Git recovery см. соседний проект `fortis-container` (`/workspace/repos/fortis-container/docs/`). Этот индекс и часть датированных документов ниже описывают Tunnel/G2 состояние на 2026-10-16; они не являются источником текущего mount layout.

**Точка входа:** [главный README](../README.md). Этот индекс отвечает на вопрос «где читать / где менять», а не дублирует конфигурацию. Перед действием сверять [датированный срез](CURRENT_STATE.md) с live-системой.

## Локальные повторяемые сценарии

[Реестр Tunnel](use-cases/README.md) ведёт к Guard/reconnect owners;
общий Docker/GitHub/CI workflow — в главном реестре Fortis.

## От вопроса к документу

| Вопрос или задача | Читать сначала | Затем, если нужно |
|---|---|---|
| Итог G2/Repo и воспроизведение | [ISOLATION_GUIDE](ISOLATION_GUIDE.md) | [E44 metadata/docs](G3_DOCS_CONSOLIDATION_AND_REPO_BOUNDARY_2026-10-16.md) |
| Как ChatGPT связан с Windows и Docker? | [ARCHITECTURE](ARCHITECTURE.md) | [CURRENT_STATE](CURRENT_STATE.md) |
| Site обязателен? Чем Site отличается от native? | [ARCHITECTURE](ARCHITECTURE.md) | [SITES](SITES.md) |
| Какие плагины и версии Site существуют? | [SITES](SITES.md) | [INSTRUCTIONS](INSTRUCTIONS.md) |
| Что фактически готово сейчас? | [CURRENT_STATE](CURRENT_STATE.md) | [OPERATIONS](OPERATIONS.md) |
| Продолжить Fortis G2 и оценить необходимость каждого шага | [Актуальный G2 plan](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) | [Session decision](G3_SESSION_BOUNDARY_OUTCOME_DECISION_2026-10-15.md), evidence E01–E44 в плане |
| Начальный G2 scope, daily entry/stop/recovery и вывод прежнего HOST | [E42 scope/runbook](G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md) | Принят(scope), old HOST остановлен: [E43](G3_G2_SCOPE_ACCEPTANCE_AND_HOST_RETIREMENT_2026-10-16.md) |
| Как запустить, остановить или восстановить туннель? | [OPERATIONS](OPERATIONS.md) | [ACCESS](ACCESS.md) |
| Какие файлы, процессы и сети доступны чату? | [ACCESS](ACCESS.md) | [ARCHITECTURE](ARCHITECTURE.md) |
| Где история вызовов, как блокировать нежелательные операции? | [AUDIT](AUDIT.md) | [ACCESS](ACCESS.md) |
| Есть ли монитор и GUI? | [OBSERVABILITY](OBSERVABILITY.md) | [AUDIT](AUDIT.md) |
| Как создать новый hosted MCP-плагин? | [WORKFLOW](WORKFLOW.md) | [SITES](SITES.md) |
| Где править и как доставить изменение? | [INSTRUCTIONS](INSTRUCTIONS.md) | [PROVENANCE](PROVENANCE.md) |
| Как получить snapshot проекта? | [SNAPSHOT](SNAPSHOT.md) | [Broker runbook](../runtime/broker/README.md) |
| Где лежат исходники и что было перенесено? | [PROVENANCE](PROVENANCE.md) | [MIGRATION](MIGRATION.md) |

## Единственный смысл каждого документа

- **[ARCHITECTURE](ARCHITECTURE.md)** — компоненты, маршруты вызова, границы доверия и независимость native/Site. Не каталог текущих PID и портов.
- **[CURRENT_STATE](CURRENT_STATE.md)** — только проверенное состояние с датой; не источник живых разрешений.
- **[ACCESS](ACCESS.md)** — источники полномочий, ограничения Windows/Docker, ключи, интернет и порядок изменения доступа.
- **[AUDIT](AUDIT.md)** — фактические ограничения истории вызовов и *проектируемые*, пока не реализованные журнал/Policy Gate.
- **[OBSERVABILITY](OBSERVABILITY.md)** — существующий read-only монитор и его границы; не система разрешений.
- **[OPERATIONS](OPERATIONS.md)** — эксплуатационные команды, запуск/остановка/восстановление.
- **[SITES](SITES.md)** — идентификаторы, реализация и состояние **hosted** Sites, отдельно от native.
- **[WORKFLOW](WORKFLOW.md)** — создание нового Site/MCP-плагина по актуальным skills.
- **[INSTRUCTIONS](INSTRUCTIONS.md)** — какой исходник править и как доставлять изменения в существующие компоненты.
- **[SNAPSHOT](SNAPSHOT.md)** — пользовательский сценарий Snapshot Bridge, границы допуска и ссылка на живую проверку.
- **[BROKER V2](BROKER_V2_PLAN.md)** / **[V1](BROKER_V1_PLAN.md)** — решения, реализация, evidence и история, не повседневный runbook.
- **[PROVENANCE](PROVENANCE.md)** / **[MIGRATION](MIGRATION.md)** — происхождение исходников, перенос, сохранённые исключения.

## Источники вне docs

- [AGENTS.md](../AGENTS.md) — обязательные правила работы ассистента; не копия эксплуатационных инструкций.
- [runtime/README.md](../runtime/README.md) — датированные копии runtime, которые сами ничего не развёртывают.
- [runtime/broker/README.md](../runtime/broker/README.md) — команды Broker, диагностика и восстановление.
- [history/README.md](../history/README.md) — архив документов с потенциально устаревшими путями и статусами.

## Проверка репозитория

[Git worktree / publication review (16.10.2026)](GIT_WORKTREE_REVIEW_2026-10-16.md) фиксирует включённые материалы, исключённые локальные артефакты и границы проверки перед публикацией.

## Просмотр активности инструментов

[Activity audit source MVP](../observatory/README_DUAL_TUNNEL.md)
читает ограниченную историю Desktop Commander отдельно в G2 и Repo;
полный interception/audit остаётся [проектом](AUDIT.md).

## Правило DRY и актуальности

Каждый изменяемый факт поддерживать у владельца информации; здесь оставлять ссылку. **Дата проверки ≠ live-статус**. Подтверждённое поведение, исторический срез и предложенный механизм различать явными словами. Не заменять повторением ссылку, если рядом с опасным действием необходимо краткое предупреждение о безопасности.

После изменений проверить [INSTRUCTIONS](INSTRUCTIONS.md): какой runtime действительно развернули, какую версию Site опубликовали и какие файлы только документировали. Git push документов **не** публикует runtime/Site автоматически.

## Fortis G2 — порядок чтения после E43/E44

1. [Итог и 10 шагов](ISOLATION_GUIDE.md): accepted, verified, limitations.
2. [План/E01–E44](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md): 58 критериев.
3. [E42 runbook](G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md): exact daily/stop/recovery.
4. [E43](G3_G2_SCOPE_ACCEPTANCE_AND_HOST_RETIREMENT_2026-10-16.md): решение и old HOST Stop.
5. [CURRENT_STATE](CURRENT_STATE.md): сводка и сохранённая хронология.
6. [E44](G3_DOCS_CONSOLIDATION_AND_REPO_BOUNDARY_2026-10-16.md): bounded Repo metadata/docs.

Old NEXT/BLOCKED/PENDING в history/proposals — не текущие обязательства.
[Старая навигация](G2_G3_SUPERSEDED_GUIDANCE_2026-10-15.md#docs_index) сохранена.
