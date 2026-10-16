# G2 — обычная остановка и ручное восстановление, 2026-10-16

**PASS(scope): прежние три процесса и listener завершились, новая guest chain/MCP работают.**
[Structured evidence E28](G3_G2_NORMAL_STOP_RECOVERY_2026-10-16.json).
Общий G3 BLOCKED; G4–G6 не приняты.

## Фактические результаты

Пользователь сообщил «сделал» после инструкции остановить только G2 и повторить pinned guest
LaunchTest. Само нажатие Ctrl+C/ввод ключа не наблюдались; desktop automation не использовалась.

| Компонент | Прежний PID | Результат | Новый PID |
|---|---|---|---|
| runtime | 23896 | ORIGINAL_GONE | 25920 |
| Python gate | 32480 | ORIGINAL_GONE | 18956 |
| MCP Node | 32496 | ORIGINAL_GONE | 32272 |

В 04:02:43 actual G2 MCP выполнил pinned Verify SHA99482C33…: baseline JSON hash совпал;
creation fingerprints защищают от PID reuse; NewRuntime=true, OldSnapshotProcessesGone=true,
Passed=true. Новая chain принадлежит SID1009/non-admin/Session2; hashes фактических EXE совпали
с runtime A922D372…, Python31FE10B4…, Node2FFE3ACC….
Это одновременно полезная MCP/CLI/file-read операция после ручного восстановления.

В 04:03:29 старый port59393 не слушает. Среди новой selected chain слушает только runtime на
127.0.0.1:54647; Python/Node TCP listeners отсутствуют. HTTP-запросов не было.

Отдельный owner metadata after-check в 04:19:39 подтвердил owner HOST PID13520 и Repo PID22488:
SID1001/Session1 и exact creation fingerprints совпали с E25. Active console Session1.
Отдельный read-only Repo MCP вызов также завершился успешно.
Это point-in-time сохранность соседей, не непрерывный uptime и не повторная owner HTTP health-проверка.

## Статусы и оставшаяся работа

- 6.4 — PASS(scope) ordinary entry/normal stop/manual restart с тремя baseline processes.
- 8.1 — PASS(scope) текущего scoped stop; owner neighbors сохранены.
- 8.3 — PASS(scope) ручного цикла и полезного guest MCP после возврата. Длительность не измерялась;
  числового time gate пользователь не задавал, новая stopwatch-проверка не назначается.
- 8.4 — PARTIAL: normal cleanup подтверждён; forced-failure case не испытан.
- 8.5 — PASS(scope) фактического reboot/manual startup из E20 и последующего восстановления E28.
  Это не общая G6 acceptance.
- 8.7 — инструкция entry/stop/recovery дополнена доказательством этой версии; общий handover ещё частичный.

Не повторять этот normal stop/restart или reboot без drift/конкретного нового вопроса.
E26 ACL regression, E20 browser и E22 guest clipboard scoped PASS сохраняются.

Остаются применимые owner boundary, brokers/API/IPC/services/protected assets, один обоснованный
failure case и итоговый переход на G2. Прежний owner HOST пока работает как переходный канал;
его отдельная runtime-only migration не нужна. Фактический вывод прежнего HOST ещё не выполнен.

## Что не выполнялось

Ассистент не останавливал процессы и не вводил credentials. Launcher/source pins не менялись.
Не менялись ACL, сеть, AV, mounts, службы, scheduled tasks или owner profiles.
Commit/push и публикации не выполнялись. Все утверждения о новом recovery ограничены этим
ручным циклом; future descendants, crash и logoff cleanup не приняты автоматически.
