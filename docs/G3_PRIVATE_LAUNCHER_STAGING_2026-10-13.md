# G3 — private launcher staged, 2026-10-13

Срез: 2026-10-13T15:35:25.2034066Z (22:35 Asia/Bangkok). **STAGED_TESTED / LIVE_NOT_APPLIED. G3 OPEN; G4 не принят.** Это текущая точка после [прототипа](G3_WINDOW_ISOLATION_PROTOTYPE_2026-10-13.md), а не подтверждение уже выполненного перехода. [Машинные evidence](G3_PRIVATE_LAUNCHER_STAGING_2026-10-13.json).

## Что готово и что проверено

- Пользовательский elevated Preview в 21:26: owner SID 1001, Session 1, полный inventory, UNKNOWN=0; пять процессов SID 1009. WinSta0/default исходные SHA совпали с последующим readback. Owner WRITE_DAC до/после ALLOW. ACL writes=0, остановок=0, паролей/ключей не запрашивали.
- Подготовлен owner-controlled Start-G2PrivateWindow.ps1: default Preview, локальные Launch/Rollback только от elevated owner; компоненты захватываются в память с SHA256 pins до исполнения. Полный комбинированный C# compile, PowerShell AST parse и captured-script Preview PASS.
- Backup/Apply/Rollback проверены на собственных synthetic window objects: DACL roundtrip Restored, чужое последующее изменение вызвало CAS rejection и было сохранено. Job-managed private child exited 0; synthetic SecureString env slot, собственный USERPROFILE, UI flag и station inheritance PASS.
- Named pipe constructor, writer/reader, timeout/read и GetNamedPipeClientProcessId проверены на собственном same-account synthetic child; фактический PID совпал. Попытку подключения чужого процесса не симулировали. Production код принимает результат только от PID создаваемого credentialed PowerShell.
- Ранее actual G2 SID 1009 в private fixture: PS → Node → обычный PS descendant; Workspace RW, runtime mutation DENY; installed Edge headless с fresh temporary profile, собственными HTTP/CDP/localStorage/DOM PASS. Стандартный browser sandbox сохранён. Это fixture, а не ещё запущенный новый runtime.
- Финальная проверка в 22:35: owner WinSta0/default original hashes неизменны. HOST 5580, Repo 23904, G2 28148 сохранили CreationDate; healthz/readyz 200/200.

**Live window ACL ещё не применены; текущий G2 остаётся на WinSta0.** Credentialed CreateProcessWithLogonW branch / admin-created unique named station требуют локального Windows password и ещё не были запущены. Launcher выполняет именно этот selftest до main ACL writes и до запроса runtime key. Успех синтетических тестов не заменяет эту проверку.

## Как устроен локальный переход

1. Закрыть только старое консольное окно G2 с профилем fortis-host-g2-test (старые SID 1009 PS 21828/conhost 21780/runtime 28148/Python 19376/Node 21812). Не закрывать owner HOST или Fortis Repo. Launch при любом SID 1009 либо UNKNOWN process в Session 1 остановится до изменений; old handles не считаются отозванными изменением DACL.
2. Открыть свежий PowerShell **от имени администратора под alexa**. Запустить captured-byte/SHA command ниже; SourceDirectory остаётся фиксированным Windows repo path.
3. Ввести Windows password FortisHostG1 только в локальный masked prompt. ValidateAccount проверяет точный SID/non-admin. Новый уникальный noninteractive объект создаёт elevated owner, guest SID 1009 не получает WRITE_DAC/WRITE_OWNER/DELETE. Explicit lpDesktop, no inherited owner handles, suspended creation, identity/session check, kill-on-close Job precede resume.
4. Credentialed CLI/Edge selftest выполняется без runtime key. Script/Node source находятся в protected C:\\Tools bootstrap. Результат идёт по ACL-protected named pipe, с native PID binding; admin не читает результат из G2-writable file. Cleanup удаляет только два известных protected файла и пустой directory без recursive admin deletion.
5. Только после selftest PASS и повторного zero-G2 inventory ввести **отдельный существующий G2 runtime key** masked locally. Owner-only ACL backup в C:\\Users\\alexa\\AppData\\Local\\FortisHostG2WindowAclBackup сохраняется до изменений. CAS проверяет текущие descriptors; SID 1009 deny на owner WinSta0/default закрывает reopen и изменение ACL. Owner rights forecast сохранён.
6. Стартует pinned runtime v0.0.15 с тем же G2 test profile в новой отдельной station. Родитель — owner/admin, фактический runtime token — SID 1009/non-admin; parent ambient env/key не копируются. Секрет передаётся как native environment slot из SecureString, новый plaintext key file не создаётся. Консоль supervisor оставлять открытой.
7. После локального запуска отдельно принять actual native MCP identity/chain, private station/descendants, fresh owner-object opens DENY, отсутствие retained owner object handles, Workspace/runtime/UI/API/Edge и неизменность owner HOST/Repo. Только после actual acceptance закрывать соответствующий window gate.

```powershell
$script = 'C:\Users\alexa\Repos\tunnel\runtime\host-g2\window-isolation\Start-G2PrivateWindow.ps1'
$bytes = [IO.File]::ReadAllBytes($script)
$sha = [Security.Cryptography.SHA256]::Create()
try { $hash = ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '') }
finally { $sha.Dispose() }
if ($hash -ne 'E56E0A40AA96D686FBD5C07ECCCC7000B5DF0F14BCA8D8D91368FE05E52ED763') {
    throw 'Скрипт изменился — запуск остановлен'
}
& ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($bytes))) -Mode Launch
```

Пароль/ключ не присылать в чат. Достаточно сообщить «запустилось» или статическую ошибку/несекретные PID, station и Backup metadata. При новом owner logon session исходные window-object ACL могут измениться; launcher fail-closed потребует новый reviewed Preview, не повторять принудительно.

## Откат

При ошибке после своего Apply supervisor завершает только свой Job и пытается CAS rollback после подтверждённого отсутствия G2/UNKNOWN. Если появились чужие изменения ACL или остаётся процесс, защита сохраняется; напечатается backup path. Не переписывать ACL вслепую.

Для явного отката закрыть G2 supervisor/его Job, затем в fresh elevated owner PowerShell выполнить тот же captured pinned script с `-Mode Rollback -BackupPath '<точный Backup из вывода Launch>'`. Backup должен быть direct file в owner-only fixed backup directory, соответствовать schema/SID/session/object names; reparse/untrusted access rejected. При normal runtime exit защита owner window objects сохраняется до такого явного отката.

## Текущий план и совместимость

| Этап | Состояние |
|---|---|
| UI cards off / narrow G2 runtime / protected shared runtime | Applied, accepted в прежних dated evidence |
| Workspace/file baseline + history/Windows compatibility | Applied, accepted в прежнем scope |
| Elevated owner window Preview / staged private launcher / synthetic CAS/job/pipe | PASS на этой точке |
| Local credentialed preflight, window deny и private runtime switch | PENDING local user password/key; ещё не выполнялся |
| Actual private runtime/window gate acceptance | PENDING после запуска |
| Owner local APIs / whole-chat routes / service/SMB residuals | OPEN; не исправлены этой операцией |
| Production G4 и retirement старого interactive G2 entry path | NOT ACCEPTED |

Windows CLI/Node/Python/Git и installed headless Edge с отдельным профилем остаются целевыми возможностями; новых command/network blocks не добавляли. Projects открывать адресно под конкретную Windows-задачу, обычная разработка остаётся Fortis Repo. Основной desktop/clipboard и owner browser sessions не входят в этот baseline. Механизм разрешённой разовой передачи clipboard ещё не реализован.

Source/live distinction: записаны только Git-backed source/docs; ни один runtime/служба/задача/Docker/Site не перезапущен или опубликован, owner launchers/profiles/keys не изменены, commit/push не выполнялись. G2 key — отдельный от owner; stripping Node env не заявлен как граница от чтения памяти другого процесса того же SID.

## Pins

| Source | SHA256 |
|---|---|
| Start-G2PrivateWindow.ps1 | E56E0A40AA96D686FBD5C07ECCCC7000B5DF0F14BCA8D8D91368FE05E52ED763 |
| G2WindowSupervisor.cs | 0A097A40EA867639D7537533FE89171CCA71399B1C18AB31AF4C85FD3AF068EB |
| WindowPolicy.ps1 | 02486600F12D2A3E29FBA4ABFF8440320B2BCA289EB93BCBB120743C0329CA50 |
| G2WindowMeta.cs | BFAFAB4805B7210B11768C591E4FD5B672322514B1E53B5F5EF9382EF1B238AA |
| WindowBoundaryProbe.cs | 29CF0CFA83412084F3573747DEAD73BAFC90E3121B34FE1C9EEF0BB347F838B2 |
| ProcessInventory.cs | 6A59D74F1C6261DAF44E04BA1830D559543879A9F0BCFB4E8C32D5AB36BACDD3 |
| private-station-node-probe.js | C1B1C54977F5478F36C34905AAFDF614D43EBE934968729B0651AF528B58D3B1 |

WindowBoundaryProbe.cs и ProcessInventory.cs — ранее проверенные компоненты. Preview-G2WindowBoundary.ps1 сохраняется как read-only historical preflight; новый переход использует Start-G2PrivateWindow.ps1.
