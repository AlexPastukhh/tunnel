# ChatGPT ↔ Windows Bridge — актуальный workflow

**Версия:** 0.5 · **Проверено:** 2026-10-09
**Главная цель:** получать актуальный snapshot локального Windows Git working tree в файловую систему ChatGPT, выполнять массовую работу автономно и пакетно применять изменения. Нет жёсткого ограничения числа вызовов Tunnel: избегаем ПОФАЙЛОВЫХ запросов.

**Самый актуальный источник команд:** локальный `C:\Users\alexa\chatgpt-bridge\Bridge.ps1 guide`. Этот документ хранится в приватном GitHub-посреднике `AlexPastukhh/chatgpt-snapshot-transfer`. Документы и ZIP снимков хранятся в Git-истории; не менять видимость репозитория на Public.

## 1. Быстрый старт новому чату

Прочитать этот документ через подключённый GitHub-плагин. Работать с Windows через Secure MCP Tunnel / Desktop Commander `start_process`, а со snapshot — в собственной файловой системе ChatGPT.

```powershell
$bridge = 'C:\Users\alexa\chatgpt-bridge\Bridge.ps1'
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge guide
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge discover
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge list
```

`guide` описывает команды, `discover` находит доступные локальные Git-клоны, `list` сообщает зарегистрированные алиасы и разрешение экспорта. Эти вызовы не публикуют файлы.

Если проект ещё не зарегистрирован:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge register -Remote AlexPastukhh/obs-planning-docs
```

Можно задать точный локальный путь: `register -Repo <alias> -LocalPath "C:\Projects\repo"`. Новый приватный проект регистрируется с `export_enabled=false`, и не может быть выгружен до `enable`.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge preview -Repo obs-planning-docs
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge enable -Repo obs-planning-docs -Mode all -ConfirmExport
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge snapshot -Repo obs-planning-docs
```

После `snapshot` взять из JSON **актуальные** `snapshot_id`, `status`, `artifact_id` и `github_repository`. Если GitHub Actions не готов, или ответ Tunnel потерян:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge status -SnapshotId <snapshot_id>
```

Когда `status=ready`, вызвать GitHub-плагин `download_workflow_artifact(repo_full_name="AlexPastukhh/chatgpt-snapshot-transfer", artifact_id=<artifact_id>)`. Это **отдельное действие GitHub-плагина, не вызов Tunnel**. Файл должен реально оказаться в файловой системе текущего чата.

## 2. Получение и работа внутри ChatGPT

Downloaded Artifact — **один ZIP-слой**, содержащий `repo/<relative-path>` и `_bridge/manifest.json`. Проверить корректность ZIP, отсутствие path traversal, симлинков и дублей, `snapshot_id`, количество файлов, размер и SHA-256 **каждого** `repo/` файла по манифесту. Исходный `snapshot_sha256` из Windows относится к ZIP *до* GitHub Actions: хеш повторно упакованного Artifact ZIP не обязан совпасть.

Сохранить неизменный baseline, создать рабочую копию. По ней искать, читать, анализировать, редактировать и выполнять доступные локальные тесты **без тысячи обращений через Tunnel**. Если среда ChatGPT не содержит нужной программы для теста, сообщить ограничение или запустить нужную HOST-проверку через Tunnel.

**Сквозной реальный тест 2026-10-09:** `obs-planning-docs`, snapshot `obs-planning-docs-20261008T194815Z-3f7ac1df`, Git HEAD `6c41aa4aa72139786518268dc9a656572b200eb2`, 1169 файлов, 12 941 899 байт исходных файлов; transport commit `52995906aa431663e863754a9543a3126deff545`, run `37834730614`, Artifact `11575396262`. Artifact скачан **в ChatGPT workspace**, ZIP открыт, все 1169 SHA-256 файлов сверены, ошибок нет. **Эти IDs не использовать как текущие в новых задачах**.

## 3. Пакетное применение изменений на ПК

Сгенерировать Git-compatible текстовый patch относительно неизменного baseline. Проверить список путей/изменений, SHA-256 байтов патча. Для небольших патчей:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge apply -SnapshotId <snapshot_id> -PatchBase64 <base64> -PatchSha256 <sha256> -CheckOnly
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge apply -SnapshotId <snapshot_id> -PatchBase64 <base64> -PatchSha256 <sha256>
```

`apply` перепроверяет исходные SHA только изменяемых файлов, выполняет `git apply --check`, затем применяет и считает postimage SHA. Повторное применение того же патча может вернуть `already_applied`; если изменены postimage — ошибка. **Никакого автоматического commit/push пользовательских изменений.** Синтаксис текущего парсера поддерживает обычные текстовые Git diff по безопасным путям (без rename/copy/binary, специфических quoted paths). Нет полноценного atomic rollback для многофайлового патча. Большие патчи потребуют другого транспорта.

**Сквозной приватный тест 2026-10-09:** snapshot `test-private-20261008T180947Z-e1849716` → патч создан в ChatGPT → `apply -CheckOnly: checked` → `apply: applied` → повторный `apply: already_applied`. Создан тестовый `C:\Users\alexa\test\docs\bridge-private-apply-smoke-20261009.md`; пользовательские рабочие файлы не перезаписаны. Таким образом приватный `apply` уже проверен.

## 4. Выбор файлов

Параметры на ПК в `C:\Users\alexa\chatgpt-bridge\repos.json`:

| `selection_mode` | Что включается |
|---|---|
| `all` | Все Git-видимые файлы **кроме обязательных защитных исключений** |
| `exclude` | Git-видимые файлы за исключением шаблонов из локального `policies/<alias>.snapshotignore`; синтаксис Git ignore (включая `!`) |
| `include` | Только файлы по `allowed_export_globs` |

По умолчанию `respect_gitignore=true`: tracked файлы и untracked неигнорируемые; игнорируемые untracked не включаются. Режим `all` **не означает всю файловую систему**, не переносит `.git` и не отменяет обязательные исключения. `preview` читает список и размер, но не архивирует и не публикует.

`obs-planning-docs` сейчас настроен в `all`, экспорт включён. `enable` требует `-ConfirmExport`, сверяет Git origin, приватную видимость репозитория, лимиты и определённые сигнатуры секретных ключей; `snapshot` повторяет проверку сигнатур при каждой отправке. Это **не полноценный аудит конфиденциальности**. ZIP-публикация в приватную историю Git всё же раскрывает файлы всем имеющим доступ к этому репозиторию.

Чтобы запретить последующие snapshot:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge disable -Repo obs-planning-docs
```

## 5. Обнаружение и регистрация

`discover` не делает глобальный поиск по дискам. Только `discovery_roots` из локального `repos.json` и **их непосредственные дочерние папки**, без рекурсии. На 2026-10-09 проверены `C:\Users\alexa`, `C:\Users\alexa\Downloads`, `C:\Users\alexa\Documents`; найдено **19** локальных Git working trees. Все 19 обнаруженных локальных Git working trees **зарегистрированы по явному поручению пользователя** (20 алиасов, включая `test` и `test-private` для одной рабочей копии). 17 новых регистраций имеют `private_bridge`, `classification=private`, `export_enabled=false`; прежние настройки `obs-planning-docs`, `test` и `test-private` не менялись. Сам `discover` по-прежнему никого не регистрирует; дальнейшие новые проекты подключаются отдельно.

`register -Remote owner/repo` сопоставляет remote с реально найденной локальной копией, проверяет рабочий корень, origin и ветку. При нескольких клонах требует явного `-LocalPath`. `register` никогда не публикует данные. Текущие зарегистрированные алиасы: `test` (публичный **только синтетический**), `test-private` (приватный синтетический) и `obs-planning-docs` (реальный приватный).

## 6. Безопасность, восстановление и ограничения

- **Сохранить repo Private.** Приватный посредник является Git-репозиторием, ZIP-коммиты остаются в истории Git даже после удаления GitHub Actions Artifact (retention 7 дней). Для действительно эфемерного транспорта понадобится другая реализация.
- Не публиковать неизвестные/конфиденциальные файлы без ревизии; существующие эвристики по именам/сигнатурам не ловят все секреты.
- **Разрыв связи не означает неуспех.** Использовать `status -SnapshotId`, а не создавать второй snapshot. `status` проверен на восстановлении `ready` после сетевого сбоя.
- Источник истины — локальный Windows рабочий репозиторий; transport Git-коммиты делаются **в отдельном локальном клоне посредника**, не в исходном проекте.
- Без отдельных указаний не делать `git commit`, `push`, `reset --hard`, `clean -fdx` в пользовательских рабочих репозиториях. Тестовые транспортные коммиты приватному посреднику разрешены в установленном workflow.
- Для повторного исполнения/нового чата сначала прочитать эту инструкцию, вызвать `guide`/`list`, а не повторять старые IDs или предполагать доступность файлов предыдущего чата.

**При изменении команд:** обновить и этот файл, и `CHATGPT_START_HERE.md`, и локальную инструкцию Bridge; повторно прочитать опубликованные документы через GitHub-плагин.
