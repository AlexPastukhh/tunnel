# E38 — Repo переведён на узкий runtime, 16 октября 2026

> Продолжение: [E39](G3_REPO_MONITOR_DISCOVERY_2026-10-16.md) установил и исправил причину source collector auto-discovery UNKNOWN; actual Windows automatic UP/initialized без override. Старые E38 наблюдения ниже сохранены. Installed dashboard по-прежнему не обновлялся.

> После ручного перезапуска пользователя: проверка 2026-10-16 07:19 Asia/Bangkok подтвердила Repo PID31420, creation 2026-10-16T00:06:04.3124340Z, Session1, тот же pinned narrow artifact; listener127.0.0.1:50385, live/ready=true, MCP initialized и actual native Repo CLI UID1000. Проверяющий ничего не перезапускал. Старые PID24720/port65202 ниже — срез первого перехода. Auto-discovery мониторинга повторно не проверялся.

**DEPLOYED / NATIVE MCP PASS(scope). Automatic monitor discovery — отдельный незакрытый вопрос.**
[JSON](G3_REPO_RUNTIME_CUTOVER_2026-10-16.json) · [План](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) · [Recovery](G3_REPO_RUNTIME_ONLY_RECOVERY_2026-10-16.md).
G3 BLOCKED; G4–G6 не приняты. Прежний owner HOST пока работает на полном клиенте.

## Решение и цель

Пользователь в 06:50:25 Asia/Bangkok явно разрешил замену после обсуждения потери полной панели.
Scope: два live Repo файла и временное прерывание только Repo.
Цель — исключить admin UI/API из процесса Repo под alexa, сохранив MCP и диагностику.
Это не отказ от Windows admin token и не запрет гостю читать любые метрики.
G2 и прежний HOST не переводились и не останавливались.

## Фактическое применение и восстановление

В 06:51 owner Preview подтвердил BEFORE файлы и pins.
В 06:51:58 guarded Apply изменил два файла с read-back и создал резервную копию.
Receipt сохранён в Repo до остановки старого процесса.

| Файл в C:\Users\alexa\chatgpt-repo-mode | AFTER SHA256 |
|---|---|
| run-tunnel.ps1 | 52848CDA49FECB4D78589E9979781A28D114A92F694CF75BC66EA6D4412EB93B |
| control.ps1 | 605F9D54A0A35FF3011DC44356A733F975A8993F1225FF53378A6B7880A193C5 |

Recorded recovery identity:

- BackupPath: C:\Users\alexa\AppData\Local\FortisRepoApiMigration\a6d1e489e8b74a6dbbcc17978070641b\backup.json
- BackupSHA256: 7234D724730813F5E50F8A7215054B851B3323C4A4759DD65C5E383F1B14766C
- JournalPath: C:\Users\alexa\AppData\Local\FortisRepoApiMigration\a6d1e489e8b74a6dbbcc17978070641b\journal-57715a6a2b794f6fa9fe92d60fdf7356.jsonl

В 06:53:23 pinned control/selected StopAccess завершил старый Repo PID22488.
Процесс и прежний listener59183 отсутствуют; backup hash сверен перед stop.
Запущен pinned launcher под owner SID1001/Session1, runner PowerShell PID28180.
Для этого MCP-запуска stdout/stderr launcher/runtime подавлены, чтобы не выводить profile/doctor details.
Новая постоянная запись журналов не настроена; история этого запуска не обещается.

## Новый процесс и реальное подключение

| Свойство | Наблюдение |
|---|---|
| Executable | C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe |
| SHA256 | A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A |
| PID / creation UTC | 24720 / 2026-10-15T23:53:49.9302510Z |
| Owner / Session | SID1001 / 1 |
| Listener | 127.0.0.1:65202, датированный динамический адрес |
| Metrics identity / health | Repo подтверждён; live=true, ready=true |

Native Repo MCP реально выполнил Python CLI под UID1000 и прочитал E38 receipt.
Bridge SHA совпал с E35: 8389436658E22F213D9865A78872159E027CA33094999DB64CA96B5A7C79FC21.
Это actual MCP после перехода, а не вывод только по health/exit code.

## Граница из G2 и управление

G2 SID1009/Session2/non-admin, 06:55:53; только GET, bodies не читались:

| Адрес нового Repo listener | Status |
|---|---|
| /healthz | 200 |
| /ui | 404 |
| /api/log-level | 404 |
| /api/logs | 404 |
| /api/codex/status | 404 |
| /harpoon/mcp | 404 |

Mutating methods, exports и streams не вызывались.
Полнота вывода опирается также на pinned artifact/source graph E08/E15,
а не на полный перебор paths × methods. Health/metrics сохраняют прежнюю loopback модель,
без новой проверки SID; это не полная межпользовательская блокировка TCP.

Control Status находит ровно PID24720, выбирает /health и видит правильный running container.
Selected StopAccess реально выполнен на старом процессе; start выполнен pinned launcher.
Кнопки Start/OpenPanel GUI отдельно не нажимались. Повторный restart ради меню не нужен.

## Мониторинг и ограничения

Pinned observatory/repo_monitor.py реально исполнен на Windows owner Python3.12.

- Automatic discovery: UNKNOWN, Native Repo listener discovery unavailable.
- При временном OBS_REPO_URL=http://127.0.0.1:65202 только внутри проверяющего Python:
  UP, verified=true, live=true, ready=true, mcp_state=initialized.
- Source collector и постоянное окружение не менялись.
- Установленный/работающий dashboard и его GUI не проверены.
- В source auto-discovery timeout3s; причина конкретного UNKNOWN не выделена.
  Связь с runtime swap не доказана, baseline полного клиента для этого запроса не снимался.

Первый вызов python.exe оказался WindowsApps alias. Затем использован существующий
owner Python312 по абсолютному пути, без установки/изменения PATH.
ExecutablePath guest Python из owner-запроса был null; его не использовали и права не расширяли.
Это ограничения диагностического запуска, не отказ Repo.

Дальнейшая адресная работа: установить причину auto-discovery и действительную используемую
версию/потребность dashboard. Не закреплять динамический порт65202 как постоянную настройку.
Не повторять runtime switch или полный аудит ради UNKNOWN.
Файловые журналы/rotation — отдельный Proposal, не внедрённая функция.

## Сохранённое состояние и обычный startup probe

Final read-back 06:58:56: AFTER pins совпали; named profile SHA не изменился:
EEB6000A4FC8A84AADA1718306A99A810A55A75BC4666A1DB09BAD954142F39E.
Штатные doctor/runtime используют существующие локальные credential references при запуске;
ключи не экспортировались/не копировались, новый key не provisioned.
Отдельного чтения key contents помощником не было; сами программы штатно читают нужный ключ.

Owner HOST13520 и G2 runtime25920 сохранили прежние creation fingerprints.
Контейнер c6d7be9fe6eb4138a9dc47db3f82c32c377007c2d461c1f03ad37fe9bb3d074a
остался Running с прежним StartedAt 2026-10-15T18:48:24.218118202Z.
Mounts/ACL/network/автозапуск не менялись, StopContainer не вызывался.

Прежний launcher включает probe.mjs: temporary write/unlink controls, обновление
linux-tools.json/verification.json, применение заданных DC/Git настроек внутри Docker volume.
Поэтому весь старт не был read-only; live launcher replacement ограничен двумя файлами.
Report 06:53:49 подтверждает правильный container, UID1000, read-only root, publishedPorts0.

Repo runtime/MCP и выбранная admin boundary приняты в этом scope.
Live rollback не выполнялся; backup identity и E36 Windows fixture recovery evidence сохранены.
Прежний owner HOST ещё предоставляет full-client поверхность. Final G2 takeover, применимые
owner boundary/private-assets вопросы и whole-chat1.4 остаются по плану.
Commit/push не выполнялись.
