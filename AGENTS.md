# Работа с этим репозиторием

Для Fortis Repo-чата сначала короткий вход главного реестра из
`/workspace/repo/README.md` и полностью UC-CONT-002/003; затем только применимые
[локальные Tunnel UC](docs/use-cases/README.md). Primary `Repos/tunnel` держать
на чистом `main`; edit/test/stage/commit — в зарегистрированном task worktree.

Начать с [навигации по задачам](docs/README.md) и [архитектуры](docs/ARCHITECTURE.md); для журналирования и запретов — [AUDIT](docs/AUDIT.md). Эти страницы не заменяют live-проверку.

Сначала README.md и применимый локальный UC. `docs/CURRENT_STATE.md` —
исторический срез; читать его для соответствующей истории, не как текущую
конфигурацию. Source/Guard owner — `runtime/windows-repo/README.md`;
незавершённая работа ведётся только в `docs/BACKLOG-IMPROVEMENTS.md`.

- Выполнять задачу пользователя. Не трактовать подключение MCP-плагина как запрос создать сайт.
- Различать native HOST, native Repo Docker и два Site MCP endpoint. Диагностика одного не доказывает состояние другого.
- HOST: только разрешённые файловые/терминальные действия. Автоматизация основного Windows GUI, screenshots и ввод не разрешены.
- Repo Docker: `/workspace/repos` и `/workspace/files` — aliases внутренних `Repos`/`Workfiles` в persistent workspace. Windows clones — отдельные Git-каталоги; не выводить host bind из похожего пути.
- Не публиковать ключи, профили с секретами, логи с payload, snapshots ZIP или приватные upstream URL. Не расширять аудиторию Site или экспорт Bridge попутно.
- После timeout мутации сначала проверить состояние. Не повторять вслепую.
- Не удалять/чинить metadata Windows linked worktrees из Linux только из-за недоступных Windows-путей.
- При изменении runtime, инструкций или tool presentation обновить docs/INSTRUCTIONS.md и соответствующие текущие документы. Записать, что реально перезапущено/опубликовано и проверено.
- runtime/ — исходники-копии. Для применения нужен явный перенос в действующую установку и проверка. Site исходники принадлежат отдельному Sites Git, не этому репозиторию.
