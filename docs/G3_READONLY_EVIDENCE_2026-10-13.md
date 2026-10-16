# G3 — ограниченный HOST: read-only проверки и блокирующий результат, 2026-10-13

Статус: **FAIL / STOP для защищённого общего runtime**. Покрытие G3 частичное; полный аудит обходов не завершён. Подмена кода не выполнялась, запуск от владельца/SYSTEM не демонстрировался.

## Действующий G2

Проверка начата после локального запуска пользователем. Tunnel PID 8452 → Python 5152 → Node 23140 → PowerShell 1708. Все наблюдаемые процессы принадлежат SID S-1-5-21-303538662-3368424508-2654684973-1009 / FORTIS_M\FortisHostG1.
Administrator=false; DESKTOP_COMMANDER_DISABLE_MCP_UI=1; число присутствующих имён CONTROL_PLANE_API_KEY / OPENAI_API_KEY / OPENAI_ADMIN_KEY в дочернем процессе — 0. Значения ключей не читались.
G2 остаётся запущенным; остановлены дальнейшие активные тесты, а не процесс. Старые G2-G факты об остановке относятся к предыдущему запуску.

## Блокирующий результат: общий runtime доступен для изменения

Через реальный G2 токен открывались и сразу закрывались Win32 handles с заданными правами (CreateFile OPEN_EXISTING); WriteFile, DeleteFile, переименование, замена и создание файлов не вызывались.

| Объект | Write/create | Append | Delete |
|---|---|---|---|
| C:\Tools и три runtime-каталога | handle ALLOW | handle ALLOW | handle ALLOW |
| Desktop Commander dist\index.js | handle ALLOW | handle ALLOW | handle ALLOW |
| tunnel-client.exe и node.exe | Win32 32 — sharing violation, не ACL DENY | handle ALLOW | handle ALLOW |

Три runtime-каталога: C:\Tools\tunnel-client, C:\Tools\desktop-commander-runtime, C:\Tools\desktop-commander.
Полный путь JS: C:\Tools\desktop-commander\node_modules\@wonderwhy-er\desktop-commander\dist\index.js.

Независимый owner observer прочитал только ACL/метаданные: на этих объектах имеется наследуемая ACE для Authenticated Users (AU), в том числе 0x1301bf. Затем AccessCheck в процессе самого G2 подтвердил write/append/delete ALLOW для всех семи выбранных ACL, включая оба EXE.
SID 1009 не получил WriteDac/WriteOwner; они запрещены. C:\ root DeleteChild и WriteDac также дали Win32 5.

Действующий старый HOST Node PID 17056 под SID 1001 запускает именно этот index.js и C:\Tools\desktop-commander-runtime\node.exe. Owner HOST PID 5580, native Repo PID 23904 и G2 PID 8452 используют один C:\Tools\tunnel-client\tunnel-client.exe.
Следствие (вывод из наблюдаемых прав и shared paths): G2 может изменять код доверенного runtime; последующая загрузка/перезапуск owner-процесса могла бы исполнить изменённый код с правами владельца. Это не демонстрация фактической эксплуатации или компрометации.
Synthetic ACL PASS из G1/G2-E сохраняет свою узкую область; требования immutable shared binaries / G2-C не подтверждены этим PASS.

## Остальные адресные проверки

- GoodbyeDPI и MySQL80: OpenService с query_config/query_status ALLOW. ChangeConfig, Start, Stop, Pause, Delete, WriteDac, WriteOwner DENY (Win32 5). Никаких service control/config операций не было.
- SERVICE_USER_DEFINED_CONTROL ALLOW у обоих сервисов. Пользовательские коды не отправлялись; поведение обработчиков не исследовано, этот путь остаётся OPEN.
- MySQL mysqld.exe и bin: write/append/delete/WriteDac/WriteOwner DENY; для bin DeleteChild также DENY.
- GoodbyeDPI configured executable/parent вернули PATH_NOT_FOUND (3). Не считать это ACL DENY или доказательством защиты бинарника.
- AMDLinkUpdate, AMDRyzenMasterSDKTask, StartAUEP, FortisRepoBridgeBrokerV1: попытка G2 получить задание/SD через Scheduler COM дала 0x80070005.
- Live scheduler SD четырёх заданий получены authorized owner observer без XML/actions/arguments/паролей; AccessCheck под фактическим G2 токеном дал DENY на read/write/append/execute/delete/WriteDac/WriteOwner. Run/Update/Register/Delete не вызывались. Это адресная проверка ACL, не аудит всех заданий.
- Named pipes docker_engine и dockerDesktopLinuxEngine: generic read/write handles DENY, Win32 5. Docker API-команды не отправлялись.
- Локальные TCP listeners инвентаризированы по адресу/порту/PID/process name; их наличие не означает доступность привилегированных операций.
- Изучен исходник tunnel-client v0.0.15, commit a390c168ff1b2d14e73a95991c186c6aba3ff5a0: admin routes защищаются loopback; SameOriginUnsafe допускает non-browser запросы без Origin/Referer. В log-level handler есть GET/PUT; runtime PUT/POST не проверялись. Не считать localhost межпользовательской границей без отдельной проверки.
- Содержимое logs/export/oauth/codex events, личные файлы, secrets, owner environment и ключи не запрашивались.

## Состояние без production impact

На 2026-10-13T06:58:00.7034171Z (13:58 Asia/Bangkok):
HOST PID 5580 и Repo PID 23904 сохраняют исходные CreationDate; healthz/readyz на 8080 и 58122 — HTTP 200/200.
G2 PID 8452 сохраняет CreationDate 2026-10-13T06:43:30.0963580Z; port 65069 healthz/readyz — HTTP 200/200.
ACL, runtime files, profiles, services, tasks, mounts и ключи не менялись. Созданы только repo-backed evidence и предложенный, НЕ применённый remediation script.

## Предложение и продолжение

[План точечного ACL исправления](G3_RUNTIME_ACL_PROPOSAL_2026-10-13.md).
[Read-only helper source](../runtime/host-g2/g3-readonly-access-check.cs).
[Structured evidence](G3_READONLY_EVIDENCE_2026-10-13.json).

До устранения writable shared runtime G3 не продолжать активными проверками. Далее повторить реальные handle/AccessCheck проверки, затем localhost/API, IPC, synthetic junction/UNC/network и границу альтернативных ChatGPT routes.
Изоляция всей сессии остаётся OPEN: owner HOST и native Repo доступны в том же чате. G4 production migration не выполнена.

Методология: [Service Security](https://learn.microsoft.com/en-us/windows/win32/services/service-security-and-access-rights), [Task security](https://learn.microsoft.com/en-us/windows/win32/taskschd/security-contexts-for-running-tasks), [AccessCheck](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-accesscheck).

## Продолжение после ACL — 2026-10-13

Выше сохранены исходные pre-ACL результаты. Пользователь согласовал и вручную применил исправление; runtime ACL gate теперь PASS, полный post-ACL AccessCheck выполнен. Общий G3 остаётся OPEN на других границах. Актуальные доказательства: [post-ACL verification](G3_POST_ACL_VERIFICATION_2026-10-13.md).
