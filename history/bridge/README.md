# ChatGPT Bridge — Windows (current)

Дата: 2026-10-09. **Точка входа нового чата:** приватный репозиторий [AlexPastukhh/chatgpt-snapshot-transfer](https://github.com/AlexPastukhh/chatgpt-snapshot-transfer):
- [CHATGPT_START_HERE.md](https://github.com/AlexPastukhh/chatgpt-snapshot-transfer/blob/main/CHATGPT_START_HERE.md)
- [docs/CHATGPT_BRIDGE_WORKFLOW.md](https://github.com/AlexPastukhh/chatgpt-snapshot-transfer/blob/main/docs/CHATGPT_BRIDGE_WORKFLOW.md)

Локальный исполняемый файл: `C:\Users\alexa\chatgpt-bridge\Bridge.ps1`.

## Вызовы через Secure MCP Tunnel / Desktop Commander

```powershell
$bridge='C:\Users\alexa\chatgpt-bridge\Bridge.ps1'
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge guide
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge discover
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge list
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge preview -Repo obs-planning-docs
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge snapshot -Repo obs-planning-docs
```

Если нового проекта нет в `list`: `register -Remote owner/repo`, `preview`, `enable -Repo alias -Mode all -ConfirmExport`. `register` и `enable` **не публикуют** файл; `snapshot` публикует ZIP в приватный GitHub-посредник. Для остановки новых выгрузок — `disable -Repo alias`.

Получить `artifact_id` из JSON `snapshot` / `status`, скачать через **GitHub-плагин** `download_workflow_artifact` в текущую файловую среду ChatGPT и сверить SHA-256 всех файлов с `_bridge/manifest.json`. Работать по локальной копии ChatGPT, изменения возвращать единым патчем: `apply -CheckOnly`, затем `apply`. При потере ответа Tunnel использовать `status -SnapshotId ...`.

**Проверено 2026-10-09:** `obs-planning-docs`: 1169 файлов перенесены через приватный GitHub Artifact в ChatGPT и проверены побайтово по SHA-256; `test-private`: `apply` / `already_applied` проверены. Число Tunnel-вызовов не фиксировано, главное — отказаться от пофайлового доступа по Tunnel.

Приватный GitHub — не эфемерное хранилище: ZIP-коммиты сохраняются в истории Git. Сканирование типовых ключей не гарантирует отсутствие всех секретов. Никогда не публиковать репозиторий-посредник без ревизии содержимого.
