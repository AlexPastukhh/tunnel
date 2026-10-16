# G3 — подготовленная диагностика GUI/clipboard между Windows-сессиями

## Статус и назначение

Подготовлен исходник [Test-G3SessionGuiBoundary.ps1](../runtime/host-g2/window-isolation/Test-G3SessionGuiBoundary.ps1).
Это следующий контролируемый user-local тест для подпунктов 2.5, 2.8 и части 2.6
[актуального плана](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md).
**G3 BLOCKED; G4–G6 не приняты. OwnerWitness текущего pin выполнен на Windows; GuestProbe BLOCKED на process-query prerequisite; Native/guest GUI acceptance PENDING.**
Сохранение исходника в checkout не устанавливает новый launcher и не изменяет Windows runtime.

SHA-256 единственного исполняемого исходника:
`8F1BC80CA8A2C9625B32340203ABA5AEFEDFBB0BC244AA2C5E1FF7CDBC90B222`.
Встроенный C# входит в эти же байты; внешних исполняемых компонентов нет.

## Пауза метода по запросу пользователя, 2026-10-15

[Review необходимости и Candidate Proposal P01](G3_GUI_BOUNDARY_METHOD_REVIEW_2026-10-15.md) сопоставляет Windows documentation,
локальную evidence и стоимость ручных итераций. Следующие recovery/Native команды пока не требуется
выполнять: сначала выбран достаточный метод и существующий G2 integration route.
Это пауза отладки harness; owner GUI/clipboard guarantee и обязательные незакрытые gates не отменены.
Ни одна security строка не стала PASS. Новый witness ради этого review не нужен.

## Первый Windows запуск предыдущей версии

Пользователь выполнил OwnerWitness с pin `C062023DD7570F1FAA6E05E45B749E668D370A07A3800A37C433D1E096710637`.
SHA-256 проверка и Windows Add-Type compilation прошли. Windows x64 / owner SID / non-elevated guards
до ошибки пройдены; отдельный token/PID witness ещё не выдан. Ошибка:
`Expected own interactive WinSta0/Default canonical paths not established`.
При последующем metadata-only вызове получен точный результат:

```json
{"Session":1,"Objects":{"Station":"WinSta0","Desktop":"Default","StationPath":"\\Sessions\\1\\Windows\\WindowStations\\WinSta0","DesktopPath":"\\Default"}}
```

Исходник ошибочно требовал полный desktop path. Это ошибка проверки, а не DENY и не нарушение изоляции.
Фактическая owner Session1 заменяет старое предположение о Session2 для этого user-local запуска;
guest SessionId здесь не измерялся. Owner GUI/clipboard contents не читались; GuestProbe не запускался.
Исправленная версия выше сохраняет сырое имя и связывает desktop lookup с проверенным station root.
Schema witness повышена до 2; старый witness/source pin не принимается как новый.
Последующий OwnerWitness исправленного pin выполнен; Native root controls / GuestProbe остаются PENDING.

## Исправленный OwnerWitness — Windows результат 2026-10-15 21:51:41 Asia/Bangkok

Источник: JSON пользователя, Mode=OwnerWitness, pin 8F1BC80C…B222.
Windows compilation, owner identity/non-elevated guards и station/desktop name guard пройдены.
Получен schema 2 witness; KeepThisPowerShellOpen=true, GuiContentRead=false.

```json
{
  "Schema": 2,
  "CreatedUtc": "2026-10-15T14:51:41.9198884Z",
  "CreatedUnixSeconds": 1792075901,
  "SourceSHA256": "8F1BC80CA8A2C9625B32340203ABA5AEFEDFBB0BC244AA2C5E1FF7CDBC90B222",
  "Sid": "S-1-5-21-303538662-3368424508-2654684973-1001",
  "Session": 1,
  "Pid": 28260,
  "ProcessCreated": "134365494948380136",
  "StationPath": "\\Sessions\\1\\Windows\\WindowStations\\WinSta0",
  "DesktopName": "Default",
  "DesktopObjectName": "\\Default"
}
```

Это подтверждает owner metadata этап, но не owner DENY и не отдельную guest session.
На этом этапе далее планировался GuestProbe; фактическая остановка и следующий recovery block описаны ниже. Witness пригоден до 22:21:41 Asia/Bangkok
при сохранении owner процесса; новый owner запуск до истечения/изменения не требуется.
Полный цикл и Native self/missing/owner controls, guest window/clipboard ещё не выполнены.

## GuestProbe: остановка и автономная диагностика, 22:05–22:10 Asia/Bangkok

Пользователь прочёл Public PS1 и прошёл pin-check 8F1BC80C…B222. GuestProbe остановился:
`HoldProcess` / `Open target QUERY_LIMITED_INFORMATION`. NativeErrorCode и точный caller stage
не получены. Это не owner GUI/clipboard DENY. Внешний prerequisite прервал независимые GUI тесты;
повторять полный GuestProbe без нового диагностического знания не нужно.
Следующий inline фрагмент ошибочно зависел от прежних `$h` и `$Error[0]`: проверка переменной
дала Unexpected source hash, затем извлечение ошибки завершилось NULL. Это не проверка текущих
байтов файла и не доказательство его подмены. GuestGui result не получен.

Ниже автономный recovery block для **новой ordinary guest PowerShell**, вставлять целиком.
Он не использует прежние переменные/историю ошибок. C# загружается только из заново прочитанных
и сверенных байтов исходного pin. Весь блок останавливается при ошибке prerequisites;
исключение собственного GuestGui возвращается отдельно вместе с уже собранными метаданными.
Полный Native owner тест не запускается. Запрос PID28260 остаётся metadata target из предыдущего
witness; ни успех, ни отказ не доказывают live owner identity или owner GUI protection.
Guest clipboard сохраняется при непустом содержимом. Этот блок и его Windows outcome ещё не проверены
на Windows; текущий C# source не менялся, прежние compile checks не повторялись.

```powershell
& {
    $ErrorActionPreference='Stop'
    $p=Join-Path $env:PUBLIC 'Documents\Fortis-G3-SessionGuiBoundary-8F1BC80C.ps1'
    $bytes=[IO.File]::ReadAllBytes($p)
    $sha=[Security.Cryptography.SHA256]::Create()
    try { $hash=([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','') } finally { $sha.Dispose() }
    if($hash -cne '8F1BC80CA8A2C9625B32340203ABA5AEFEDFBB0BC244AA2C5E1FF7CDBC90B222'){throw 'File SHA256 mismatch'}
    $identity=[Security.Principal.WindowsIdentity]::GetCurrent()
    $session=[Diagnostics.Process]::GetCurrentProcess().SessionId
    if($identity.User.Value -ne 'S-1-5-21-303538662-3368424508-2654684973-1009' -or $session -le 0 -or $session -eq 1 -or @($identity.Groups | Where-Object Value -eq 'S-1-5-32-544').Count){throw 'Expected ordinary guest in separate session'}
    & ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($bytes))) -Mode Validate -CapturedSHA256 $hash | Out-Null
    $objects=[FortisG3SessionBoundary]::OwnObjects()
    $station='\Sessions\'+$session+'\Windows\WindowStations\WinSta0'
    if($objects.StationPath -ine $station -or $objects.Station -ine 'WinSta0' -or $objects.Desktop -ine 'Default' -or $objects.DesktopPath -notin @('\Default',($station+'\Default'))){throw 'Unexpected own station/desktop'}
    $report=[ordered]@{
        SourceSHA256=$hash
        GuestSid=$identity.User.Value
        GuestSession=$session
        OwnObjects=$objects
        OwnProcessQuery=[FortisG3SessionBoundary]::ProcessOpen([uint32]$PID,0x1000)
        WitnessPidQuery=[FortisG3SessionBoundary]::ProcessOpen(28260,0x1000)
        WitnessPidStatus='METADATA_TARGET_ONLY_LIVE_OWNER_IDENTITY_NOT_REVALIDATED'
    }
    try { $report['GuestGui']=[FortisG3SessionBoundary]::GuestGui($false) }
    catch { $report['GuestGuiError']=$_.Exception.GetBaseException().Message }
    [pscustomobject]$report | ConvertTo-Json -Depth 6
}
```

Результат разделить на process access, guest identity/objects и собственные window/clipboard/cleanup.
Не закрывать 2.5/2.6 по этим данным; 2.8 оценивать только по фактическому roundtrip/window/cleanup.

## Что делает тест и зачем

| Проверка | Польза и граница результата |
|---|---|
| OwnerWitness: SID1001, actual SessionId, PID/creation time, полное имя собственной WinSta0 и сырое имя Default | Даёт действительную owner-цель вместо имени `WinSta0`, которое из guest указывает на guest. Читает только метаданные; PowerShell нужно оставить открытой |
| GuestProbe: точный SID1009, отсутствие Administrators membership, другая actual Windows session | Исключает запуск теста из неправильной сессии или с повышенными правами. Номера 2/3 не зашиты |
| QUERY_LIMITED_INFORMATION owner witness process до/после проб | Проверяет session/creation time и удерживает reference к process object. SID проверен при выдаче witness в owner. Недоступная metadata или завершившийся процесс — блокер, не DENY |
| Native open/close own objects с каждым requested mask + заведомо отсутствующее имя | Проверяет работоспособность используемого метода. Self-open требует совпадения имени; для desktop дополнительно проверяется полный station root. Отсутствующее target name должно дать 2/3 после успешного root-open |
| Native open/close owner station/desktop | Проверяет выдачу handles с clipboard/screen/object/hook/switch и ACL takeover rights. Объект не назначается процессу/потоку, полученные права не используются |
| OpenProcess own/owner witness с DUP_HANDLE, CREATE_THREAD, VM_OPERATION/READ/WRITE | Проверяет возможные пути получить handles/код/память через **этот** owner process. Не дублирует handles, не читает/пишет память, не создаёт thread |
| Одно собственное guest window | Подтверждает создание/visibility и проверяет очистку своего объекта. Не проверяет input injection/capture, которые для этого шага не нужны |
| Clipboard roundtrip точного случайного маркера в собственном уникальном custom format | Подтверждает собственный guest clipboard без чтения прежних форматов. По умолчанию непустой clipboard остаётся нетронутым, результат SKIPPED_NONEMPTY |

Состав masks записывается в JSON. Desktop WRITE_DAC/WRITE_OWNER запрашиваются вместе с
READOBJECTS/WRITEOBJECTS, как требует OpenDesktop; DENY относится к комбинации прав.
Нет требования запрещать управление собственными guest процессами, GUI или clipboard.

## Ограничения метода и выводов

- Документированный OpenWindowStation работает в текущей Windows session. Поэтому скрипт
  использует Native API `NtUserOpenWindowStation`/`NtUserOpenDesktop` и имена, полученные
  через `NtQueryObject` от действительных объектов. Для desktop используется имя `Default` относительно
  handle станции, полное имя которой сверено; сырое `\Default` не объявляется полным путём.
  Root запрашивает только WINSTA_ENUMDESKTOPS и закрывается отдельно. Это диагностическая, неподдерживаемая Microsoft ABI;
  её работоспособность и cross-session поведение на этой Windows ещё не проверены.
- `DENIED_OPEN_WITNESS_BACKED` допустим только при успешных self/missing controls и Win32 5
  от owner open. Другие ошибки, отсутствие имени/entry point и сломанный контроль — INCONCLUSIVE.
  Это witness-backed отрицательное открытие, не доказательство невозможности всех GUI APIs.
  `DENIED_STATION_ROOT_DESKTOP_NOT_TESTED` означает запрет открытия station root; отдельное desktop right
  в такой строке не проверено. Ошибка root/missing lookup не превращается в desktop DENY.
- Witness — выбранные оператором метаданные, а не аутентифицированный канал. Его возраст ограничен
  30 минутами. Результат зависит от того, что оставленная PowerShell сохраняет свой station/desktop.
  Источник и SessionId должны совпасть; PID/creation time/session проверяются заново из guest.
  Owner SID принимается из выбранного оператором witness: повторный TOKEN_QUERY owner из guest не нужен
  и не выполняется. Это ограничение доверия явно присутствует в JSON.
- Успешный owner handle помечается `OWNER_HANDLE_OPENED_REVIEW`: нужно оценить его реальную
  применимость между сессиями. Это не означает, что скрипт уже прочитал owner экран/clipboard.
- Процессные пробы относятся к witness PowerShell. Existing handles конечной MCP chain,
  реальные HOST/Repo процессы, clipboard history/sync/RDP и другие bridges ещё не проверены.
- Все owner contents остаются нетронутыми. Нет ACL writes, desktop/station switching,
  screenshot, window enumeration/text reads, SendInput, hooks, token impersonation или privilege enable.
- Общий статус JSON всегда `SCOPED_DIAGNOSTIC_ONLY_G3_PENDING`. 2.5/2.6 закрываются только
  после оценки Windows evidence и применимого остатка на конечной G2 chain.

## Локальный запуск: сначала alexa, затем guest

Обычная **не повышенная** Windows x64 PowerShell. Не закрывать owner HOST/Repo.
Нужен один проверочный файл, а не доступ guest к `alexa\Repos`.
Следующая команда читает исходник, проверяет SHA-256 и исполняет именно captured bytes.
Она также сохраняет эти же байты под фиксированным именем в Public Documents для чтения guest.
Это обычный исходник без credentials; ACL не меняются. Существующий другой файл не перезаписывается.
Owner блок Public copy текущего pin и последующий OwnerWitness прошли без сообщённой ошибки;
отдельный guest read-back ещё не проверен. При отказе остановиться без изменения прав. Предыдущая копия сохраняется под своим именем.

В **новой обычной** PowerShell alexa (предыдущая уже содержит старый C# type):

```powershell
$p='C:\Users\alexa\Repos\tunnel\runtime\host-g2\window-isolation\Test-G3SessionGuiBoundary.ps1'
$b=[IO.File]::ReadAllBytes($p)
$sha=[Security.Cryptography.SHA256]::Create()
try { $h=([BitConverter]::ToString($sha.ComputeHash($b))).Replace('-','') } finally { $sha.Dispose() }
if($h -cne '8F1BC80CA8A2C9625B32340203ABA5AEFEDFBB0BC244AA2C5E1FF7CDBC90B222'){throw 'Source SHA256 mismatch'}
$copy=Join-Path $env:PUBLIC 'Documents\Fortis-G3-SessionGuiBoundary-8F1BC80C.ps1'
if(Test-Path -LiteralPath $copy){if((Get-FileHash -LiteralPath $copy -Algorithm SHA256).Hash -ne $h){throw 'Existing copy differs'}}else{$f=[IO.File]::Open($copy,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None);try{$f.Write($b,0,$b.Length)}finally{$f.Dispose()}}
& ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($b))) -Mode OwnerWitness -CapturedSHA256 $h
```

Оставить эту PowerShell открытой. Передать только полученный JSON в чат либо выбранный
`OwnerWitnessBase64` в guest. Допустим ручной обмен этим фрагментом; bridge для него не нужен.
Переключиться в FortisHostG1 обычным способом, не завершать owner logon.

В новой обычной PowerShell guest:

```powershell
$p=Join-Path $env:PUBLIC 'Documents\Fortis-G3-SessionGuiBoundary-8F1BC80C.ps1'
$b=[IO.File]::ReadAllBytes($p)
$sha=[Security.Cryptography.SHA256]::Create()
try { $h=([BitConverter]::ToString($sha.ComputeHash($b))).Replace('-','') } finally { $sha.Dispose() }
if($h -cne '8F1BC80CA8A2C9625B32340203ABA5AEFEDFBB0BC244AA2C5E1FF7CDBC90B222'){throw 'Source SHA256 mismatch'}
& ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($b))) -Mode GuestProbe -CapturedSHA256 $h -OwnerWitnessBase64 'PASTE_SELECTED_BASE64'
```

По умолчанию guest clipboard тестируется только если он пуст. `SKIPPED_NONEMPTY` — не FAIL
изоляции и не PASS clipboard. Если текущие guest clipboard данные не нужны, можно **до запуска**
добавить `-ReplaceGuestClipboard`: прежние guest данные будут заменены и не восстанавливаются.
После roundtrip скрипт удаляет только свой ещё принадлежащий ему marker; чужое новое содержимое
оставляет нетронутым. Занятый clipboard/ошибка очистки явно отражаются в результате.
Предыдущее содержимое, marker и данные окон в JSON не выводятся.

Передать весь JSON или точную ошибку. При ошибке не повторять запуск вслепую: сначала
проверить стадию и состояние собственного test window/clipboard. Timeout после записи Public copy
не означает, что файл не создан; сначала сверить его SHA-256. Удаление этой конкретной копии —
после теста из alexa, с проверкой того же SHA-256; shared directories не очищать.

## Проверено при подготовке

- В Repo проверены реальный mount, точный checkout, AGENTS и незакоммиченные изменения.
- PowerShell 7.4.6 AST: без ошибок. Встроенный C#: компилируется; Windows API не вызывались.
- C# language version 5: компиляция прошла. Captured-bytes Validate: компиляция прошла,
  SHA-256 совпал, NativeCallsExecuted=false.
- Исправленный source: C#5 compilation, AST и captured-bytes Validate прошли в Repo;
  шесть проверок фактического PowerShell guard приняли наблюдавшееся `\Default` и корректное полное имя,
  отклонили чужую session/station, другое desktop name и чужой полный путь. Windows API не вызывались.
- Windows compilation текущего pin и завершённый owner witness подтверждены JSON пользователя.
- Native API capability controls, guest GUI/clipboard, очистка и final MCP chain: **не проверены на Windows**.
- Windows runtime/ACL/launchers/services/network, Git commit/push и Sites не изменялись.

## Источники методики

- Microsoft: [OpenWindowStationW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-openwindowstationw),
  [SetProcessWindowStation](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setprocesswindowstation),
  [Window Stations](https://learn.microsoft.com/en-us/windows/win32/winstation/window-stations).
- Microsoft: [OBJECT_ATTRIBUTES / relative names](https://learn.microsoft.com/en-us/windows/win32/api/ntdef/ns-ntdef-_object_attributes).
- Microsoft: [station rights](https://learn.microsoft.com/en-us/windows/win32/winstation/window-station-security-and-access-rights),
  [OpenDesktopW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-opendesktopw),
  [clipboard operations](https://learn.microsoft.com/en-us/windows/win32/dataxchg/clipboard-operations).
- Native ABI: [System Informer phnt ntuser.h](https://github.com/winsiderss/phnt/blob/master/ntuser.h),
  прочитан 2026-10-15, SHA-256 `b6d678fa535b08c2102f1b9f51111c05c625a04be1b813dae5357f56208ccb1e`.
  Это сторонний первичный исходник ABI, не обещание Microsoft о cross-session support.
