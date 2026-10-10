# START HERE — ChatGPT ↔ Windows Bridge

**Текущий, проверенный протокол:** [docs/CHATGPT_BRIDGE_WORKFLOW.md](docs/CHATGPT_BRIDGE_WORKFLOW.md).

Любой новый чат сначала читает полный протокол через подключённый GitHub-плагин, затем спрашивает у Windows Bridge, какие команды и репозитории доступны. Не используй snapshot IDs, Artifact IDs и файлы из других чатов как актуальные.

## Для нового чата — готовая инструкция

> Работаем с локальными Git-репозиториями Windows через Secure MCP Tunnel / Desktop Commander и **приватный** GitHub-посредник `AlexPastukhh/chatgpt-snapshot-transfer`. Прочитай `docs/CHATGPT_BRIDGE_WORKFLOW.md` из этого приватного репозитория. Через Tunnel вызови `Bridge.ps1 guide`, `discover`, `list`; если проект не зарегистрирован, сделай `register -Remote owner/repo`; перед экспортом — `preview`, затем `enable` для согласованного проекта. Сделай `snapshot`, дождись `status=ready`, скачай **текущий** `artifact_id` через GitHub-плагин в файловую систему ChatGPT, распакуй и сверь все SHA-256 с manifest. Работай с файлами в ChatGPT, а не пофайловыми Tunnel-вызовами. Изменения возвращай патчем через `apply -CheckOnly` и `apply`, без автоматического коммита пользовательских изменений. Не считай этап выполненным без проверки. Число Tunnel-вызовов не фиксировано.

## Начало на Windows через Tunnel

```powershell
$bridge = 'C:\Users\alexa\chatgpt-bridge\Bridge.ps1'
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge guide
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge discover
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge list

# Уже зарегистрирован и разрешён для приватного экспорта:
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge preview -Repo obs-planning-docs
powershell -NoProfile -ExecutionPolicy Bypass -File $bridge snapshot -Repo obs-planning-docs
```

Далее из JSON возьми `artifact_id` и `snapshot_id`. При сбое/ожидании:
`Bridge.ps1 status -SnapshotId <id>`. Скачивание выполняет GitHub-плагин `download_workflow_artifact` из `AlexPastukhh/chatgpt-snapshot-transfer`. GitHub Artifact — один ZIP-слой с `repo/` и `_bridge/manifest.json`.

## Проверенный статус

- **`obs-planning-docs`: реальный приватный snapshot получен и проверен в ChatGPT** (2026-10-09; 1169 файлов / 12 941 899 исходных байт; SHA-256 каждого файла совпал).
- **`test-private`: приватный `apply` проверен:** `checked` → `applied` → `already_applied`.
- `discover` обнаружил 19 локальных Git working trees. **Все 19 уже зарегистрированы** в Bridge (20 алиасов, так как у тестового репозитория два имени). Из 17 новых регистраций экспорт у всех отключён; включены только прежние `obs-planning-docs`, `test-private`, `test`.
- Приватный транспорт коммитит ZIP в Git-историю. В отличие от Actions Artifact, история Git не имеет автоматического семидневного удаления. Не расширяй доступы к репозиторию без проверки.
- `all` значит все подходящие Git-видимые файлы, не игнорируемые untracked + tracked, кроме обязательных защитных исключений; **не буквально весь диск**.

**Если workflow или команды изменились, обновить основной протокол, этот старт и локальную инструкцию.**

## Готовые промпты (обновлены 2026-10-09)

- [Полная политика HOST + SNAPSHOT-FIRST](prompts/HOST_POLICY_SNAPSHOT_FIRST.md) — подробно про запреты GUI основного desktop, маршрутизацию HOST/ChatGPT и рабочие проверки.
- [Краткий SNAPSHOT-FIRST + TUNNEL VERIFY](prompts/SNAPSHOT_FIRST_TUNNEL_VERIFY.md) — компактная инструкция для новых задач.

Оба промпта используют существующий Bridge и GitHub-плагин для **автоматической доставки** snapshot в ChatGPT. Старое правило «сразу попросить пользователя прислать архив» осталось только резервным вариантом для случаев, когда автоматический путь не работает. Новому проекту требуется отдельное согласование публикации в сохраняемую Git-историю приватного транспорта.
