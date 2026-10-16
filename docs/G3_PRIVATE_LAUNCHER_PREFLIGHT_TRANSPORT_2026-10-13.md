# G3 — early preflight transport, 2026-10-13

Срез 2026-10-13T16:43:12.8129907Z / 23:43 Asia/Bangkok. **PROCESS_ONLY_POLICY_AND_EARLY_TRANSPORT_TESTED / GUEST_RETRY_PENDING. G3 OPEN, G4 NOT_ACCEPTED.** [JSON evidence](G3_PRIVATE_LAUNCHER_PREFLIGHT_TRANSPORT_2026-10-13.json); [query-only fix](G3_PRIVATE_LAUNCHER_QUERY_ONLY_2026-10-13.md); общий [staging plan/rollback](G3_PRIVATE_LAUNCHER_STAGING_2026-10-13.md).

## Что показал local retry

Operator 6DD2… больше не отказал в Attach: StartUser вернулся после suspended token identity/admin/type/session check, Job assignment и Resume. Затем родитель дождался Private preflight pipe timeout. Старый harness подключался только после Add-Type и всего Node/Edge теста; ранняя ошибка или заблокированная загрузка .ps1 оставалась невидимой. Actual guest station/CLI/Edge result ещё не получен; token/job успех не закрывает window gate.

Metadata policy read: у owner MCP Process=Bypass, CurrentUser=RemoteSigned; machine policy Undefined и LocalMachine Undefined. Exact G2 HKU policy key не был loaded/defined при read; это **не доказательство exact effective G2 policy во время проваленной попытки**. Явный -File bootstrap раньше не получал process execution policy из sanitized environment. [Microsoft execution policies](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-5.1) описывает Restricted script block и Windows Shell zone checks; причина старого guest timeout остаётся inferential, а не установленной записью child stderr.

## Изменение

- Только тестовый powershell.exe получает **-ExecutionPolicy Bypass**; CurrentUser/LocalMachine/GroupPolicy/registry не меняются. Child по-прежнему SID1009/non-admin; установка process policy не выдаёт OS права.
- Harness подключается к existing ACL-protected named pipe до Add-Type/Node и передаёт Progress: Connected → WindowMetadata → NodeCliEdge, затем Result или bounded Error (stage/type/message). Password/key в harness/environment не передаются.
- Parent сохраняет native exact created-PID binding и validates stage/frame/length; node read укладывается в общий 90-sec deadline вместо прежнего 15-sec read after connection.
- Во время ожидания connection/result проверяется native child exit; ранний exit выводится как hex code без ожидания 90 sec. Connect failure до framed channel exits94. Async/read resources closed; Job cleanup retained.
- Query-only Supervisor F619… и component pins не изменились. Protected bootstrap, no owner-file result reads/admin recursive deletion, zero-G2 guard, native non-admin checks, owner backup/CAS и preflight-before-key/ACL порядок сохранены. Guest pipe ACL дополнительно исправлена GW → GRGW только для transient synthetic channel; filesystem/window scope не расширен. Канал не несёт password/runtime key.

## Проверено

Fresh Windows compile/AST/captured pinned Preview PASS. Actual same-account transport fixtures исполняли **тот же parent loop и harness**, заменив только Node/Edge invocation на controlled JSON/failure; это не actual guest CLI/Edge acceptance.

| Fixture | Результат |
|---|---|
| Explicit Restricted -File | Load blocked, exit1; raw stderr не выведен |
| Bypass success | Early progress/result + native PID binding PASS, exit0 |
| Controlled Node stage exception | Named structured NodeCliEdge error PASS, exit3 |
| Early child exit before connection | Hex code93 detected promptly; no 90-second wait |

Fixture PS1 удалён, собственные child processes/pipe handles закрыты. ACL writes=0, credentials prompted=false. Owner station/default original hashes 65FE8DB…/A571929… unchanged, owner WRITE_DAC forecast ALLOW/ALLOW. HOST 5580 и Repo 23904 сохранили CreationDate, healthz/readyz 200/200. Source CAS/readback PASS.

## Дополнительная проверка прав канала, 23:57 Asia/Bangkok

Same-account клиент с реальными ограничениями GW не смог подключиться (controlled exit94). После GRGW на том же temporary pipe progress/result с PID binding PASS; main owner objects не менялись. Fixture parent использовал retained WRITE_DAC handle только для своей synthetic pipe DACL; production IPC grant относится лишь к этому random diagnostic channel. Финальный operator 0CF2… syntax/compile/pins/Preview PASS; main ACL writes=0. Срез final Preview 2026-10-13T16:56:58.1552314Z. Это обоснованный transport fix, actual guest run ещё PENDING.

## Локальный повтор

Открыть **fresh elevated owner PowerShell под alexa**, старую console с уже загруженным type не переиспользовать. HOST/Repo оставлять. Пароль FortisHostG1 и separate G2 key вводить только local/masked; key/ACL Apply следуют после actual private CLI/Edge PASS.

```powershell
$script = 'C:\Users\alexa\Repos\tunnel\runtime\host-g2\window-isolation\Start-G2PrivateWindow.ps1'
$bytes = [IO.File]::ReadAllBytes($script)
$sha = [Security.Cryptography.SHA256]::Create()
try { $hash = ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '') }
finally { $sha.Dispose() }
if ($hash -ne '0CF2D6228A6D5DF52C26DBD73EB758C5958B039F9F6A48EE44B9A04525FA4D4F') {
    throw 'Скрипт изменился — запуск остановлен'
}
& ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($bytes))) -Mode Launch
```

Вернуть Preflight stages и startup metadata/error, без секретов. Early exit 0xC0000142, если появится, указывает на native startup initialization до harness, а не разрешение в PowerShell коде; не расширять private ACL наугад. После normal startup сохранять supervisor console open и отдельно принять actual MCP/private station/owner-object open DENY/compatibility/owner preservation.

| Source | SHA256 |
|---|---|
| Start-G2PrivateWindow.ps1 | 0CF2D6228A6D5DF52C26DBD73EB758C5958B039F9F6A48EE44B9A04525FA4D4F |
| G2WindowSupervisor.cs (unchanged) | F61983384AFF51CCC007586DA614C710306FDCC52981C5C0A3B77AD98202045D |

Прежние operator pins исторические; новый Launch/Rollback использует 0CF2… operator. Existing owner-only backup/CAS rollback procedure сохранена. **Main station/desktop ACL ещё не applied; private runtime ещё не accepted**. Runtime/services/tasks/Docker/Sites не переключались, ключевые файлы не создавались, Git commit/push нет. Owner APIs/whole-chat routes/service/SMB и per-session persistence/retirement interactive path остаются OPEN; G4 не принят.
