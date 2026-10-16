# G3 — запуск G2 и наследование handles, 2026-10-16

> **Статус после E43 (16.10.2026):** old owner HOST остановлен. Сведения ниже о работающем HOST и будущем переключении — исторические наблюдения до приёмки. Действующий результат: [E43](G3_G2_SCOPE_ACCEPTANCE_AND_HOST_RETIREMENT_2026-10-16.md) и [план](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md).

> Уточнение цели 2026-10-16 03:35: G2 заменяет прежний owner HOST. Его runtime-only migration и helper больше не являются следующей работой (NOT REQUIRED NOW). Датированные факты и JSON ниже сохранены; действующий порядок — [актуальный план](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md). Live HOST пока не остановлен.

**Анализ исходников и адресная Windows-проверка завершены. 2.6 PARTIAL; G3 BLOCKED; G4–G6 не приняты.**
[Structured evidence E24](G3_G2_LAUNCH_INHERITANCE_2026-10-16.json).
Этот этап не менял launcher, runtime, профили, ACL, сеть, антивирус или работающие туннели.

## Результат и границы

Обычное наследование handles при создании процесса между разными Windows-сессиями не поддерживается
контрактом CreateProcess. Это документированное свойство Windows, а не новая локальная проверка.
Действующие launcher PowerShell PID32088 → runtime23896 → Python32480 → Node32496 принадлежат
SID1009 и Session2. В E21 owner GUI был независимо установлен как SID1001/Session1.
Из этих фактов следует, что обычное наследование от родителя из owner Session1 не является путём
текущего гостевого запуска. Это не исключает explicit duplication, привилегированного посредника
или API, выполняющего действия в owner session.

| Участок | Доказательство | Что это ограничивает |
|---|---|---|
| Guest launcher → runtime | Public/source SHA0638D14A… совпал; source проверяет SID/non-admin/WTS owner/WinSta0/Default, запускает ProcessStartInfo с UseShellExecute=false | Ошибочный запуск через Run as в чужой session; не означает полного отключения наследования любых guest handles |
| Runtime → Python gate | Reviewed commit a390c168…: exec.Command, StdinPipe, StdoutPipe, stderr; custom SysProcAttr/AdditionalInheritedHandles здесь не задаются. Go1.27.0 использует явный HANDLE_LIST | Наследование по этому пути ограничено выбранными standard handles, при соответствии binary просмотренному source |
| Python gate → Node | Gate SHA146E60B0… совпал с Repo. Installed Python3.13.16: close_fds=True, shell=False. Gate передаёт stdin/stdout/stderr без custom startupinfo/handle_list | Не передаёт произвольные дополнительные inherited handles через этот вызов |
| Node → команды пользователя | E18–E23 подтверждают отдельные реальные guest commands, GUI/browser и inventory | Это не review каждого будущего произвольного descendant или всех его IPC |

Версия runtime с commit a390c168… и Go1.27.0 сохранена в E08; текущий EXE hash совпал с тем
артефактом. Это provenance и source review, не новое доказательство воспроизводимой сборки.
SHA256 Python EXE и timestamps записаны в JSON без argv/env values или содержимого профилей.

## Findings

F1 — обычное межсессионное наследование ограничено Windows и способом текущего запуска.
Нет основания повторять переключение профилей или создавать ещё одну private station ради этого пути.

F2 — E23 не становится полным inventory от анализа кода: 184 записи без type name и относительные
desktop names остаются ограничениями наблюдения. Они сами по себе не доказывают owner capability.
Полный разбор всех записей не назначается обязательным следующим тестом без конкретного пути обхода.

F3 — остаётся более прямой известный путь: owner HTTP API, ранее доступный гостю в scope E13.
E15 описывает отсутствие Windows identity guard и опасные/чувствительные маршруты в исходнике.
Наследование handles и guest-only runtime migration этот путь не закрывают.
Реальные owner write/RCE здесь не проверялись и не утверждаются.

F4 — selected owner DUP_HANDLE DENY из E22 относится к guest-initiated pull из трёх процессов.
Он не исключает owner-initiated transfer или отдельный broker. Clipboard bridge metadata E22
также не равно полному исключению bridges или effective disabled policy.

## Следующая работа и необходимость

Продолжить пункт 4 актуального плана: isolated совместимость owner runtime-only и условия
поочерёдного переключения owner routes. Польза — подготовить устранение известной owner API
поверхности, а не расширять полный аудит ради списка handles.
Сначала переиспользовать E14/E15 и выяснить остающиеся full-only зависимости без чтения секретов.
Live owner restart/cutover пока не выполняется; его согласование относится к конкретному
подготовленному route с backup/rollback. Достаточные guest clipboard/browser positives не повторять.

## Источники

- [CreateProcessW: bInheritHandles и session restriction](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessw).
- [Process connection to a window station](https://learn.microsoft.com/en-us/windows/win32/winstation/process-connection-to-a-window-station).
- [Thread connection to a desktop](https://learn.microsoft.com/en-us/windows/win32/winstation/thread-connection-to-a-desktop).
- [DuplicateHandle: PROCESS_DUP_HANDLE и направления передачи](https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-duplicatehandle).
- [Python3.13 subprocess: close_fds/handle_list/std handles](https://docs.python.org/3.13/library/subprocess.html).
- [Tunnel transport, exact commit](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/mcpclient/stdio_command.go).
- [Go1.27.0 Windows process creation](https://github.com/golang/go/blob/go1.27.0/src/syscall/exec_windows.go).
