# Наши плагины через Site

Это справочник только по **hosted Sites**: IDs, Worker/upstream, published source и gate. Независимые native-маршруты и их связь с Site — в [ARCHITECTURE](ARCHITECTURE.md); точка входа по задаче — [README](README.md).

Site здесь — hosted MCP proxy с небольшой диагностической веб-страницей. Страница не обязательна для вызова инструментов из ChatGPT. MCP App с интерактивной карточкой внутри чата — отдельный механизм, не любой сайт.

| | HOST Site | Repo Site |
|---|---|---|
| Название | Desktop Commander · prot | Fortis · Repo Mode |
| URL | https://desktop-commander-prot.alexandr-pastukh03.chatgpt.site | https://fortis-repo-mode.alexandr-pastukh03.chatgpt.site |
| Project ID | appgprj_6ac37ed606f48191a03e271f62f1c436 | appgprj_6ac9cf4d34648191ae73ce8bdc38e772 |
| Plugin ID | plugin_asdk_app_sites_b31ba47e05d08191b7ab22da8c64732a | plugin_asdk_app_sites_2dc4b5748434819189749b3655c7525b |
| Версия на проверке | 4 | 7 |
| Source HEAD | f9cfaed451c0b46b6570eaf123e5235c3593f0c1 | 22b2a4bf0c4c75a41a40b92e2ead9bd1642dddab |

MCP URL — URL соответствующего Site + /mcp. Источники находятся в отдельном **Sites Git на git.chatgpt-team.site**, не в GitHub/tunnel. Идентификаторы сохранять при обновлениях; не создавать второй Site/plugin для обычного исправления.

## HOST proxy

Worker хранит upstream адрес в secret DESKTOP_MCP_URL. DESKTOP_PROJECT_ROOT задаёт предпочтительный путь; по умолчанию C:\Users\alexa\Documents\prot. Это не разрешённая файловая граница.

Каждый proxy вызов создаёт MCP session, выполняет initialize + notifications/initialized, передаёт точные аргументы, поддерживает JSON/SSE, завершает session best-effort. После неопределённой мутации автоматических повторов нет.

Диагностика: site_connection_status, GET /api/status; ?verify=project дополнительно делает read-only list_directory указанного проекта. Offline tool inventory содержит сохранённые схемы; наличие tools/list не доказывает, что upstream сейчас работает.

## Repo Site: отдельный путь, пока не активированный

Условия выпуска file/terminal tools:
- REPO_MCP_URL: поддерживаемый HTTPS upstream endpoint.
- REPO_MCP_TOKEN: optional secret bearer.
- REPO_ISOLATION_VERIFIED: точное значение true после реальной проверки изоляции.

REPO_PREPARATION_STATE=container_verified — записанная отметка, не живая проверка контейнера.

До настройки endpoint/gate рекламируется только repo_connection_status. После активации используется allowlist из 19 инструментов вместо полного native набора 26. DC configuration/feedback UI tools исключены. Site поддерживает server/discover 2026-07-28 и legacy initialize; upstream в проверенном коде использует 2025-03-26.

Native Secure Tunnel ID **не является** готовым HTTPS upstream URL для Worker. Не вставлять внутренние gateway адреса наугад. Подходящий поддерживаемый маршрут native→Site ещё не подтверждён.

## Расхождение, выявленное при актуализации

Hosted Repo версия 7 всё ещё описывает /workspace/repo без Windows mounts; deployment/ хранит прежние scripts/config с offline network и ручным key. Текущий native Repo уже имеет /workspace/repos, /workspace/files, internet и saved-key reference.

Обновлённые документы здесь описывают native состояние. **Hosted Site в рамках переноса документации не изменён и не перепубликован.** При следующем изменении Site нужно согласовать README, deployment snapshot, initialize.instructions, диагностические тексты и страницу с фактическим состоянием, сохранив Site gate закрытым до настройки его собственного endpoint.

Различать «подготовлен контейнер», «работает native plugin» и «активирован Site proxy» во всех формулировках.

## Источники стандартной процедуры

Не копировать стандартный workflow: открыть установленный **sites:sites** и его reference **site-mcp-server.md**; для правил App/skills/extensions — **plugin-creator:create-plugin**, **plugin-creator:update-plugin** и references sites-mcp.md / account-updates.md.

Основные внешние спецификации: [MCP](https://modelcontextprotocol.io/specification/), [MCP Apps](https://modelcontextprotocol.io/docs/extensions/apps). Версии протокола выбирать по текущему skill и поддержке обеих сторон, не менять работающий upstream только по новизне даты.
