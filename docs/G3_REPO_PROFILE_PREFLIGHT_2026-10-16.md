# E37 — предварительная проверка профиля Repo, 16 октября 2026

> Продолжение: [E38](G3_REPO_RUNTIME_CUTOVER_2026-10-16.md) выполнил согласованный Repo-only Apply/restart и actual narrow MCP/control/guest surface acceptance. Ниже сохранён preflight E37 до переключения; current monitor gap — в E38/плане.

**Проверка формы профиля завершена в ограниченном scope. Переход не выполнен.**
[План](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) · [JSON](G3_REPO_PROFILE_PREFLIGHT_2026-10-16.json) · [E36](G3_REPO_GUARDED_MIGRATION_2026-10-16.md) · [Восстановление](G3_REPO_RUNTIME_ONLY_RECOVERY_2026-10-16.md).

## Зачем потребовался шаг

E35 проверил исходники обычного stdio runtime, E36 — применение и восстановление двух файлов.
Они не показывали, содержит ли реальный профиль несовместимые настройки полного клиента или
дополнительные HTTP bindings. Эта адресная проверка снижает риск неудачного запуска и применения
выводов E35 к другой конфигурации. Ключи, старое окружение процесса и содержимое owner GUI для неё не нужны.

## Что выполнено

Чтение на Windows под owner SID1001/Session1: 2026-10-15 23:29:40.772 UTC
(16 октября 06:29:40 Asia/Bangkok). Профиль выбран по source-derived resolver:
WINDOWS_USER_CONFIG, named profile repo-mode. Файл разобран локально существующим js-yaml/JSON_SCHEMA.
В чат/JSON выведены только сводные признаки и SHA256, без значений профиля и окружения.
Ссылки на credentials не разрешались; файлов ключей открыто 0, сетевых запросов 0.

| Проверяемое свойство | Наблюдение |
|---|---|
| Профиль соответствует Repo tunnel ID | Да; config_version=1 |
| MCP HTTP bindings / Harpoon targets | 0 / 0 |
| MCP commands | 1; команда отличается от фиксированной команды Candidate |
| Control plane origin / prefix | Production origin / default prefix |
| Представление ключа | FILE_REFERENCE; путь и значение не выведены |
| Health listener | Loopback TCP |
| Проверенные full-only conflicts / review items | Пустые списки |
| Неизвестные поля верхнего уровня | 0; полная nested schema не проверялась |
| Выбранные env overrides / OTEL resource/service | Отсутствуют в текущем observer process |
| Дополнительные full-only/cloudflared/raw-log/tunnel-ID env | Отсутствуют, отдельная сводка 23:31:25 UTC |

Несовпадение команды не требует правки профиля. Candidate явно задаёт
`--mcp.command command=docker exec -i fortis-repo-test node /workspace/repo/.fortis/mcp-bridge.mjs`.
В закреплённых исходниках `resolveMCPEntries` при Changed flag возвращает CLI array,
не добавляя команды из profile/env. При этом профиль сначала разбирается и его ссылки могут
разрешаться штатным загрузчиком; работоспособность этой стадии ещё не проверена native runtime.
Пустой additional Harpoon override переиспользует уже проверенное E08.

В 23:31:11 UTC Repo PID22488/Session1 сохранил expected owner, creation и public executable pin.
Оба live launcher/control файла сохранили BEFORE hashes E36. FilesChanged=0, restart=false.

## Подготовленные исходники и проверки

В `runtime/host-g2/runtime-api-migration/`:

- `repo-profile-shape-preflight.mjs`: 7534 bytes, SHA256
  `A89FE795D4C0DF8BF060A463272AAA768C501271E6F89054E9DC2EA42DD70024`.
- `test-repo-profile-shape-preflight.mjs`: 1738 bytes, SHA256
  `968F4F4A2D1ED473A2377E6D75B3A5FD0F4F273E429FE2DC8DC01294BF75A298`.

Repo: syntax check пройден при подготовке; шесть synthetic classifier/privacy cases PASS,
включая конфликтующие параметры, приватные synthetic значения и ошибки parser без вывода данных.
Owner data в тестах не использовались. Windows reader выполнен только после проверки SHA256.
Это не новый launcher, gate или установка runtime.

Первичные исходники: [openai/tunnel-client, commit a390c168…](https://github.com/openai/tunnel-client/tree/a390c168ff1b2d14e73a95991c186c6aba3ff5a0):
`profile.go` (resolver), `file_config.go` (profile compatibility),
`config.go` (CLI precedence и runtime env restrictions), все в `pkg/runtimeconfig/`.
Полные commit/blob IDs находятся в JSON. Совместимость установленного artifact с source
принимается в прежнем pinned-artifact scope E08, новая сборка не выполнялась.

## Ограничения и исправленная подготовительная проверка

Это bounded shape preflight, **не** полный effective-config dump, native Go validation,
исчерпывающая проверка nested schema или доказательство native MCP compatibility.
Окружение уже работающего Repo не читалось. Окружение будущего произвольного PowerShell
может отличаться от observer; при запуске нужен тот же проверенный контекст либо адресная сверка.
Прежний exists-only запрос ошибочно проверял подкаталог `profiles`. Он не читал профиль
и не доказывает его отсутствие. Resolver исправлен по исходникам до реального чтения.

Профиль, live launchers, credentials, ACL, сеть, контейнер, HOST и G2 не менялись.
Live Apply/Rollback, production backup и runtime restart не выполнялись.
G3 BLOCKED; G4–G6 не приняты. Результат не закрывает owner API или final G2 takeover.

## Следующее действие и его граница

Подготовка E36/E37 позволяет вынести конкретное решение: изменить ровно
`C:\\Users\\alexa\\chatgpt-repo-mode\\run-tunnel.ps1` и `control.ps1`,
затем прервать и запустить **только Repo** на pinned runtime.
Польза — удалить admin graph сохраняющегося owner Repo endpoint; цена —
временное прерывание общего Repo и замена OpenPanel /ui на /health.
Доступ к файлам и powershell/CLI через G2 сохраняется.

После отдельного согласия: guarded Apply → сохранить BackupPath/SHA256 → остановить
выбранный Repo без StopContainer → запустить → проверить actual narrow process,
MCP вызов, bridge/container, monitor/control и допустимую диагностику.
При проблеме — локальное восстановление E36; слепой повтор и overwrite DRIFT не допускаются.
Старый HOST и G2 этим шагом не менять и не останавливать. Повторять E08 fixtures,
GUI/clipboard, synthetic Git или весь прежний аудит для этого решения не требуется.
