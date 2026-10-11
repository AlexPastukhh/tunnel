# Windows Broker V2 — эксплуатационный runbook

**Сначала:** [общий сценарий и границы безопасности](../../docs/SNAPSHOT.md). **Текущий срез и список исключений:** [CURRENT_STATE.md](../../docs/CURRENT_STATE.md). Этот документ — технические действия, не вторая копия статуса. Исторические тесты и архитектурные решения: [план V2](../../docs/BROKER_V2_PLAN.md), [V1](../../docs/BROKER_V1_PLAN.md).

## Компоненты и режим доступа

- **Рабочий Windows worker:** `C:\Users\alexa\chatgpt-repo-mode\broker\worker.py`; приватные `permits.json`, `issued-snapshots.json`, `requests/` остаются **вне Docker RW mounts**.
- **Bridge и реестр допусков:** `C:\Users\alexa\chatgpt-bridge\Bridge.ps1`, `repos.json`. `broker_snapshot_enabled=true` разрешает повторный snapshot **только данного alias**, при включённом Broker. Отсутствует/false → default deny либо V1 one-shot.
- **Fortis Repo-клиент:** `/workspace/repo/.fortis/bridge-broker-client.py`, приватное Docker volume.
- **Очередь:** `/workspace/files/.fortis-bridge-broker-v1/in` и `out` (Windows `C:\Users\alexa\Workfiles\.fortis-bridge-broker-v1\`). У очереди нет аутентификации отправителя; риск принят. Ответы очереди — advisory, проверяется скачанный Artifact.
- **Источник в Git:** `runtime/broker/worker.py` и тесты в `tunnel` — **не сам Windows runtime**; правка Git-файла ничего не развёртывает. Старый `runtime/broker/bridge-v2-windows.patch` исторический и **не соответствует live Bridge: не применять повторно**.

## Ручной жизненный цикл

На Windows (Task оставлена Enabled, но не имеет logon trigger/RestartOnFailure):

```powershell
Start-ScheduledTask -TaskName 'FortisRepoBridgeBrokerV1'
Get-ScheduledTask -TaskName 'FortisRepoBridgeBrokerV1' | Select-Object TaskName, State
Stop-ScheduledTask -TaskName 'FortisRepoBridgeBrokerV1'
```

Через Fortis Repo, **после** запуска Task:

```bash
python3 /workspace/repo/.fortis/bridge-broker-client.py list
python3 /workspace/repo/.fortis/bridge-broker-client.py preview 'test-private'  # заменить alias
python3 /workspace/repo/.fortis/bridge-broker-client.py snapshot 'test-private' --timeout 75  # после проверки scope
# При ожидании/потере ответа заменить ID текущего запроса:
python3 /workspace/repo/.fortis/bridge-broker-client.py status 'current-snapshot-id' --timeout 35
python3 /workspace/repo/.fortis/bridge-broker-client.py recover 'original-request-uuid' --timeout 35
```

`list` показывает **живые разрешения**, не использовать числа из старых E2E; `preview` даёт краткий sample и current selection SHA. Полный read-only список на Windows: `& 'C:\Users\alexa\chatgpt-bridge\Bridge.ps1' -Action preview -Repo <alias> -FullFiles -Fingerprint`. Для новых alias существующее `export_enabled` никогда не означает standing consent.

## Получение и проверка ZIP

1. Из `status` получить **текущие** `snapshot_id`, приватный GitHub repo, workflow run и `artifact_id`. `ready` только подтверждает готовность Actions.
2. Через **GitHub connector** `download_workflow_artifact` реально получить Artifact в файловую среду ChatGPT. Сам скачанный Actions Artifact — внешний ZIP со внутренним snapshot ZIP.
3. Проверить имена, отсутствие path traversal/symlink/дубликатов, `_bridge/manifest.json`, каждый файл и его SHA-256, `selection_sha256` против одобренного preview. Готовый офлайн-верификатор — `runtime/broker/verify_artifact.py`; для **распакованного внутреннего ZIP**:

   ```bash
   python3 /workspace/repos/tunnel/runtime/broker/verify_artifact.py downloaded-inner.zip verified-snapshot --snapshot-id '<snapshot_id>' --selection-sha256 '<approved_selection_sha256>'
   ```

   Не считать `status=ready`, размер внешнего Actions ZIP или JSON очереди заменой независимой проверки.

## Ошибки, восстановление, отзыв

- **Timeout/потерян ответ:** `recover <исходный request UUID>` → `status <snapshot_id>`. Не создавать новый запрос `snapshot` с новым UUID.
- **Bridge создал ZIP/commit, но GitHub push упал:** проверить `Bridge.ps1 -Action status -SnapshotId <id>`, локальный Git HEAD, чистоту transport checkout, точный приватный `origin` и удалённый `main`. Если коммит **не опубликован**, допустима точная повторная отправка **того же коммита** после восстановления сети; не создавать ZIP заново. При неизвестном remote-state остановиться и проверить через GitHub. Такой ручной recovery был нужен при втором V2 E2E; автоматический retry не обещан.
- **Не готов Artifact:** повторять `status`, а не `snapshot`. **Непредвиденный scope/секрет/ошибка сигнатуры:** не обходить mandatory scan/limits; проверить источник данных и настройки. **Остановлен Broker:** новый запрос не исполняется; `requests/permits/journal` не удалять.
- **Отзыв:** Windows-only `repos.json` → `broker_snapshot_enabled=false`; пересчитать права через живой `list`. Отзыв не удаляет уже опубликованный ZIP из приватной Git-истории.

## V1 one-shot fallback и обновление

Для alias **без standing-допуска**, при отдельном разрешении на проверенную область, на Windows:

```powershell
& 'C:\Users\alexa\AppData\Local\Programs\Python\Python312\python.exe' 'C:\Users\alexa\chatgpt-repo-mode\broker\worker.py' --grant-repo <alias> --expected-selection-sha256 <sha256-from-full-preview> --minutes 10
```

Permit однократный (срок 1–30 минут), привязан к текущим байтам; не передавать в Docker. Остальной процесс snapshot → Artifact → verify тот же.

**Обновление live worker:** сначала `python3 runtime/broker/test_worker.py` на mock Bridge (не GitHub); сделать backup Windows worker/Task, остановить только `FortisRepoBridgeBrokerV1`, установить проверенный исходник в private Windows path, сверить SHA256/syntax, затем только вручную запустить и проверить `list/preview/deny/recover`. Не перезапускать HOST/Repo Tunnel без причины; не переносить GitHub credentials, `permits.json` или `issued-snapshots.json` в Git, не сбрасывать журнал. Не выполнять произвольный Windows shell, `register/enable/apply` через Broker и не публиковать публичный synthetic `test`.
