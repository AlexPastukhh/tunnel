# Snapshot Bridge — как пользоваться

**Назначение.** Через вручную запускаемый Windows Broker получить актуальный ZIP локального Git-проекта в приватном GitHub Actions Artifact, независимо проверить архив в ChatGPT и работать с его копией. Это не даёт Broker права выполнять Windows-команды или применять patch.

**Проверенный срез 2026-10-11:** Broker V2 установлен, Task `FortisRepoBridgeBrokerV1` включена, но **остановлена** (`Ready`); автозапуска и перезапуска после сбоя нет. В реестре 20 alias, из них **17 имеют постоянный допуск** `broker_snapshot_enabled=true` к приватному транспорту. Не включены `obs` (объём/недоступный путь), `theory-conspects-and-banks` (15 совпадений с сигнатурой возможного ключа) и публичный synthetic `test`. Это состояние **на дату проверки**; перед операцией нужен живой `list/preview`.

**Доказанная цепочка:** на `test-private` два разных snapshot прошли Broker → Bridge → private GitHub Actions → скачивание в ChatGPT; оба ZIP проверены по manifest и SHA-256 (по 8 файлов / 13 510 байт). Остальные 16 включённых alias прошли read-only preflight, **но не отдельный GitHub E2E**. ID и разбор второго сетевого сбоя — в [истории V2](BROKER_V2_PLAN.md).

## Обычный сеанс

1. Владелец **вручную запускает** Windows Task `FortisRepoBridgeBrokerV1`. Она не стартует автоматически. Пока Broker включён, любой имеющий запись в общую Workfiles-очередь может отправить разрешённый запрос (риск принят пользователем).
2. В ChatGPT через Fortis Repo проверить **текущий** alias и состав:

   ```bash
   python3 /workspace/repo/.fortis/bridge-broker-client.py list
   python3 /workspace/repo/.fortis/bridge-broker-client.py preview 'test-private'  # заменить alias
   ```

   Для **полного локального** списка и отпечатка, если нужен осмотр всей области, на Windows: `& 'C:\Users\alexa\chatgpt-bridge\Bridge.ps1' -Action preview -Repo <alias> -FullFiles -Fingerprint`. Краткий `selected_sample` — **не весь список**, если файлов больше 12.
3. Если alias разрешён и область подходящая, запросить `python3 /workspace/repo/.fortis/bridge-broker-client.py snapshot 'test-private' --timeout 75` (заменить пример alias фактически выбранным). Для 17 одобренных alias новый one-shot Windows grant не требуется; для прочих действует отказ или отдельная процедура V1.
4. По **текущим** `snapshot_id`, `artifact_id` и GitHub run скачать именно соответствующий Artifact из приватного `AlexPastukhh/chatgpt-snapshot-transfer` в файловую среду ChatGPT. Проверить `_bridge/manifest.json`, все пути, размеры, SHA-256 и совпадение области с preview. **`status=ready` само по себе не означает, что ZIP скачан или проверен.**
5. При ожидании использовать `status <snapshot_id>`. Если потерян ответ на запрос — **`recover <исходный request UUID>`, а не новый snapshot**. При сетевом сбое после локального коммита нельзя повторно создавать ZIP вслепую: см. [runbook восстановления](../runtime/broker/README.md).
6. После сеанса владелец выполняет `Stop-ScheduledTask -TaskName 'FortisRepoBridgeBrokerV1'`.

Команды запуска/остановки Task, V1 one-shot grant, восстановление и проверка ZIP подробно: [Broker runbook](../runtime/broker/README.md). Работа с patch/`apply` возможна **только отдельным согласованным HOST-маршрутом**, не через Broker; [legacy workflow](https://github.com/AlexPastukhh/chatgpt-snapshot-transfer/blob/main/docs/CHATGPT_BRIDGE_WORKFLOW.md).

## Допуски и границы

- **Текущая политика выбора:** у 17 допущенных alias `selection_mode=all` и `respect_gitignore=true`, **без привязанных `.snapshotignore`** — по явному решению пользователя. Это Git-видимые подходящие файлы, **не весь диск**. Старый private policy-файл сохранён, но не применяется. Изменившиеся в будущем Git-видимые файлы тоже могут попасть в ZIP. `.gitignore` — удобство Git, не гарантия удаления секретов.
- **Обязательные защиты сохранены:** проверка Git origin/private transport, запрещённых путей, symlink/junction, размера, известных сигнатур секретов, отпечатка выбранных байтов и ZIP/manifest. Скан известных признаков **не гарантирует**, что в архиве нет чувствительных данных.
- Разрешение задаётся **для конкретного alias** в закрытом Windows `C:\Users\alexa\chatgpt-bridge\repos.json` через `broker_snapshot_enabled=true`; прежний `export_enabled` не равен праву Broker. Для отзыва права выставить `false`. Сам Broker не принимает операции `register/enable/apply`.
- **Транспорт сохраняет ZIP в приватной Git-истории** (срок жизни Actions Artifact не удаляет Git-коммит). Ответ общей очереди не является независимым доказательством содержимого; ZIP обязательно сверять после скачивания. Fortis Repo отдельно имеет RW-доступ к своим смонтированным `Repos/Workfiles`: ограничения snapshot ZIP не запрещают прямое чтение этих папок.
- **Остались закрыты:** `obs` (примерно 59 тыс. кандидатов, уже более 719 МБ до ошибки пути, выше лимитов), `theory-conspects-and-banks` (15 файлов с **возможными**, не подтверждёнными ключами). Публичный synthetic `test` не является приватной целью. Не снимать технические проверки ради их включения.

## Где актуальная информация

- [CURRENT_STATE.md](CURRENT_STATE.md) — **короткий датированный факт состояния**; динамические разрешения перепроверять в live registry/`list`.
- [Broker README](../runtime/broker/README.md) — **команды, V1 fallback, диагностика и восстановление**.
- [BROKER_V2_PLAN.md](BROKER_V2_PLAN.md) — принятые FR/Scenario/SRU, решения, история установки, доказательства E2E и изменения scope.
- [BROKER_V1_PLAN.md](BROKER_V1_PLAN.md) — исторический V1. [Точка входа нового чата](https://github.com/AlexPastukhh/chatgpt-snapshot-transfer/blob/main/CHATGPT_START_HERE.md) — краткая навигация, не второй источник текущего реестра.
