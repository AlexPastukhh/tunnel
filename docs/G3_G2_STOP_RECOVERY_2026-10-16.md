# G2 — адресная ACL regression и подготовка stop/recovery, 2026-10-16

> Обновление 04:02–04:19: [E28](G3_G2_NORMAL_STOP_RECOVERY_2026-10-16.md) подтверждает completed normal cycle: old three processes/listener gone, новая pinned guest chain/MCP работает, owner neighbors сохранены в scope. Приведённую ниже подготовительную процедуру не повторять ради прежнего результата; PENDING ниже относится к моменту E27. Один controlled peer-failure case позднее принят E29; общий G6 не принят.

**E26: ACL regression PASS(scope). E27: lifecycle capture/negative control PASS; реальная остановка ещё PENDING.**
G3 BLOCKED; G4–G6 не приняты. Прежний owner HOST заменяется G2 в итоге; его отдельная runtime-only
миграция не требуется. На этом этапе owner HOST/Repo не останавливались и не менялись.

## Что проверено

[E26](G3_G2_CURRENT_ACL_REGRESSION_2026-10-16.json): actual guest SID1009/non-admin/Session2,
runtime23896 → Python32480 → Node32496. Для восьми выбранных runtime объектов 48 mutation open-close
запросов получили Win32 ACCESS_DENIED5, 16 read/list/execute/traverse opens разрешены.
Все открытые handles закрыты. 12 own synthetic positives, точный Workspace write/readback и cleanup PASS.
Никаких записей в shared runtime или ACL не было. Полный scan 22758 объектов не повторялся.
Это не acceptance доступа к будущим рабочим проектам или полного owner boundary.

[E27](G3_G2_LIFECYCLE_PREPARATION_2026-10-16.json): подготовлен
[Test-G2Lifecycle.ps1](../runtime/host-g2/runtime-api-migration/Test-G2Lifecycle.ps1),
SHA99482C33C22EEF99149472FB477943FCE568965E585732CC0CD8862B8483A981 (6486 bytes).
Capture сохранил три текущих процесса с SID/session/creation fingerprints и listener59393.
Source/delivery и baseline JSON SHA проверены. Probe не останавливает и не запускает процессы.
До stop выполнен отрицательный контроль Verify: все три ORIGINAL_STILL_ALIVE,
NewRuntime=false, Passed=false — ожидаемый результат контроля, не сбой G2.
Это защищает от ложного lifecycle PASS до фактической остановки.

## Особенность аварийного завершения, E29

[Один controlled synthetic failure case](G3_G2_SYNTHETIC_PEER_FAILURE_2026-10-16.md) проверен: peer вышел37,
а runtime завершился сам с exit0. Поэтому нулевой код runtime не равен успеху MCP-задачи.
При неожиданном завершении проверить ответ самой задачи/доступность G2; для ручного восстановления
использовать прежний pinned launcher. Отдельный restart engine не вводился.
Это не проверка actual Python/DC crash или всех аварийных сценариев.

## Зачем нужен один реальный цикл

Source review Windows signal handling не даёт достаточного доказательства, что остановка runtime
завершит Python/Node. Реальную ошибку остановки пока не наблюдали. Не добавлять supervisor/Job
или менять gate до получения результата. Проверяем обычный ручной цикл, уже принятый пользователем.

1. В существующей гостевой сессии FortisHostG1 открыть консоль, где сейчас работает G2 launcher.
2. Нажать Ctrl+C один раз и дождаться возврата PowerShell prompt. Не делать logout/reboot.
   Если prompt не возвращается или появляется ошибка, остановиться и сообщить; не закрывать
   owner HOST/Repo и не завершать все node.exe/python.exe.
3. В той же обычной guest PowerShell выполнить прежний pinned launcher:

```powershell
& {
    $ErrorActionPreference='Stop'
    $p=Join-Path $env:PUBLIC 'Documents\Fortis-G2-GuestEntry-0638D14A.ps1'
    $b=[IO.File]::ReadAllBytes($p)
    $sha=[Security.Cryptography.SHA256]::Create()
    try{$h=([BitConverter]::ToString($sha.ComputeHash($b))).Replace('-','')}finally{$sha.Dispose()}
    if($h -cne '0638D14A92F78006526281BEC98C391FAD96F6C0F3F70D9C02475DA3A56C481D'){throw 'Launcher SHA256 mismatch'}
    & ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($b))) -Mode LaunchTest -CapturedSHA256 $h
}
```

Отдельный G2 key вводится только локально. Не присылать ключ в чат.
Если launcher сообщает existing tunnel/другую ошибку, не обходить guard.
4. После сообщения LaunchTestStarted оставить консоль открытой, вернуться в alexa и сообщить «готово».
   До проверки не запускать новые workloads, чтобы baseline соответствовал контролируемому циклу.

После этого ассистент через G2 сверит новую chain/runtime pins, выполнит Verify по сохранённому
baseline и отдельно отметит сохранность соседних owner routes по targeted metadata.
Если старые процессы остались, это конкретный cleanup gap, а не повод менять HOST или отключать AV.

## Точные артефакты для Verify

Guest source:
`C:\Users\FortisHostG1\AppData\Local\FortisHostG2\Workspace\g2-lifecycle-99482C33.ps1`.

Baseline:
`C:\Users\FortisHostG1\AppData\Local\FortisHostG2\Workspace\g2-lifecycle-baseline-73ee40685ab7467ea98ecc60590c97e7.json`.

Baseline SHA256:
`BBDC4780BA6CE3615955FC204F73522B2B1098E22F6F488A276D3047075EB96B`.

Verify требует actual новые RuntimePid/PythonPid/NodePid и actual guest SessionId.
Baseline fingerprints защищают от ошибочного вывода по переиспользованному PID.
Probe отслеживает процессы baseline, не все возможные future descendants.
В этом normal-cycle Verify failure case не испытывается; отдельный controlled peer-failure case принят E29. Общая G6 acceptance не объявляется.

## Фактически доставлено

- ACL source: SHA5F5C5BC56D6F385588678AA63BF77FE3ACEE13A7C6EF983FD133615BDCD3FFE8,
  5701 bytes, guest Workspace g2-acl-regression-5F5C5BC5.ps1.
- Lifecycle source: SHA99482C33… в own Workspace; AST Repo, Windows Capture/negative Verify выполнены.
- Публичный launcher SHA0638D14A… не менялся; новый G2 profile или ключ не создавались.
- Не выполнены реальный stop/restart, owner HOST replacement, deployment ACL/runtime, commit или push.
