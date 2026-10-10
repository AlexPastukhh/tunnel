# Snapshot Bridge

Это альтернативный путь для больших проектов: подготовить проверенный snapshot → работать в ChatGPT scratch → вернуть patch → проверить и применить на HOST. Не является обязательным каналом Docker MCP.

Действующий Bridge: C:\Users\alexa\chatgpt-bridge\Bridge.ps1.
Registry: C:\Users\alexa\chatgpt-bridge\repos.json.
Owning transport repo: [AlexPastukhh/chatgpt-snapshot-transfer](https://github.com/AlexPastukhh/chatgpt-snapshot-transfer), checkout C:\Users\alexa\chatgpt-bridge\transport\private.

Основной живой протокол: [docs/CHATGPT_BRIDGE_WORKFLOW.md](https://github.com/AlexPastukhh/chatgpt-snapshot-transfer/blob/main/docs/CHATGPT_BRIDGE_WORKFLOW.md), [CHATGPT_START_HERE.md](https://github.com/AlexPastukhh/chatgpt-snapshot-transfer/blob/main/CHATGPT_START_HERE.md). Копии на момент переноса лежат в history/snapshot-transfer; исходники остаются в своём Git repo.

Короткий порядок:
1. guide / list / preview; проверить точный project/path, исключения и экспорт.
2. Новый проект экспортируется только после отдельного разрешения: transport коммитит ZIP в сохраняемую Git-историю приватного repo.
3. snapshot; получить artifact_id/snapshot_id, при ожидании status.
4. Скачать ровно этот GitHub Actions artifact через GitHub connector; сверить SHA-256 файлов по _bridge/manifest.json.
5. Работа со scratch snapshot, вернуть patch; HOST apply сначала CheckOnly, затем apply в согласованной задаче. Учитывать already_applied.

После переноса registry содержит 19 разных repo / 20 aliases (test и test-private — одна папка). Экспорт включён только для прежних obs-planning-docs, test-private, test; новые регистрации выключены. Добавление папки в Repos или создание tunnel repo само по себе **не включает** snapshot export.

Проверено 2026-10-09: полный private obs-planning-docs snapshot и test-private apply/already_applied. Это история конкретной проверки, не обещание актуальности старого ZIP.

HOST GUI не использовать. Для больших чтений выбирать snapshot workflow по действующей политике; runtime verify/write/apply выполнять на нужном контуре, не спутывать scratch с Windows working tree. Стандартные команды подробно не копируются: смотреть живой основной протокол.
