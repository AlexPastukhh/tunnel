# G3 — query-only token verification, 2026-10-13

Срез 2026-10-13T16:19:40.8422267Z / 23:19 Asia/Bangkok. **QUERY_ONLY_VALIDATOR_TESTED / CREDENTIALED_RETRY_PENDING. G3 OPEN, G4 NOT_ACCEPTED.** [JSON evidence](G3_PRIVATE_LAUNCHER_QUERY_ONLY_2026-10-13.json). Это следующий source fix после [Attach privilege correction](G3_PRIVATE_LAUNCHER_ATTACH_FIX_2026-10-13.md); общий [staging plan/rollback](G3_PRIVATE_LAUNCHER_STAGING_2026-10-13.md) сохраняется.

## Наблюдение

Local retry с operator SHA 3A30… прошёл создание процесса и scoped SeDebugPrivilege, затем отказал именно Attach/OpenProcessToken (Win32 5). Requested access был 10 = TOKEN_QUERY | TOKEN_DUPLICATE. Main window ACL Apply и runtime key prompt не достигнуты. Включения caller privilege недостаточно для прежнего запроса; не считать 23:00 patch actual acceptance.

## Новый validator

Attach запрашивает **только TOKEN_QUERY=8**. WindowsPrincipal/WindowsIdentity construction на target token заменена direct GetTokenInformation для SID, groups и elevation: дублирование или impersonation target token не нужны. Для G2 target отклоняются elevated token и любое Administrators membership, включая deny-only; filtered admin account не принимается за обычную учётную запись. TokenType=Primary и TokenSessionId=owner session проверяются прямо на том же process token до Job assignment / Resume. Exact SID и mask scope сохранены.

Caller-only SeDebugPrivilege scope остаётся с захватом/восстановлением PreviousState before Resume. Job kill-on-close, suspended creation, explicit private lpDesktop, no inherited owner handles, local masked password/key, protected bootstrap/PID-bound pipe и preflight-before-ACL порядок не менялись.

[Microsoft GetTokenInformation](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-gettokeninformation) требует TOKEN_QUERY для используемых классов. [Token rights](https://learn.microsoft.com/en-us/windows/win32/secauthz/access-rights-for-access-token-objects) различают query и duplicate и проверяют requested mask против token DACL. Это обосновывает removal ненужного права, но **actual query-only open токена G2 ещё PENDING local**; не заявлять причинную приёмку по одному source patch.

## Проверено до локального повтора

- CAS старых source bytes и SHA readback для Supervisor/operator PASS; component pin обновлён.
- Windows C# combined compile, source/component pins, PowerShell AST parse и captured-byte Preview PASS.
- Настоящий current Windows process token открыт как TOKEN_QUERY only. Native SID verification PASS; попытка DuplicateToken на этом же handle DENY Win32 5. Wrong expected SID rejected.
- Non-elevated owner token (account alexa with filtered admin membership) отклонён requireStandard validator по Administrators group, даже при CallerAdmin=false. Primary=1, Session=1 через direct DWORD metadata PASS.
- Первый внутренний read-only test выявил Win32 24 для sizing probe fixed DWORD class TokenElevation; TokenUInt исправлен на direct 4-byte buffer, повторный полный test PASS. Это не был user Launch, credentials/ACL не затрагивались.
- Owner original WinSta0/default hashes unchanged; WRITE_DAC forecast ALLOW/ALLOW, ACL writes=0. HOST 5580 / Repo 23904 CreationDate unchanged, healthz/readyz 200/200.
- Actual target SID1009 credentialed token open/private runtime не принят; parent enabled/admin branch проверяется local preflight до main ACL writes.

## Следующий local шаг

Нужен **новый elevated PowerShell owner alexa**: текущий загрузил старую C# assembly. HOST/Repo не закрывать. G2 duplicate/unknown guard сохранён, key/owner ACL apply следуют только после private CLI/Edge selftest PASS.

```powershell
$script = 'C:\Users\alexa\Repos\tunnel\runtime\host-g2\window-isolation\Start-G2PrivateWindow.ps1'
$bytes = [IO.File]::ReadAllBytes($script)
$sha = [Security.Cryptography.SHA256]::Create()
try { $hash = ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '') }
finally { $sha.Dispose() }
if ($hash -ne '6DD2A5DB2FE7EA9C79DEB6BB5CB68FC985CC9ADDA4A678B659394D7F4CB299FA') {
    throw 'Скрипт изменился — запуск остановлен'
}
& ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($bytes))) -Mode Launch
```

Password FortisHostG1 и separate G2 key только в local masked prompts. Вернуть startup metadata либо exact named stage/Win32 error; никаких секретов в чат. После успеха оставлять owner supervisor window открытым.

| Source | SHA256 |
|---|---|
| G2WindowSupervisor.cs | F61983384AFF51CCC007586DA614C710306FDCC52981C5C0A3B77AD98202045D |
| Start-G2PrivateWindow.ps1 | 6DD2A5DB2FE7EA9C79DEB6BB5CB68FC985CC9ADDA4A678B659394D7F4CB299FA |

Все E56E… / 3A30… / промежуточный 78E3… operator pins исторические; для нового Launch/Rollback использовать 6DD2… operator и F619… supervisor. Existing owner-only backup/CAS rollback procedure не изменена.

Live station/desktop ACL ещё не применены, runtime/services/tasks/Docker/Sites не переключались, ключевые файлы не создавались, Git commit/push отсутствуют. Следующие gates: actual private runtime/owner-object fresh-open deny/retained handles/MCP/Windows CLI/Edge/workspace/runtime/UI/API/owner preservation; owner APIs/whole-chat routes/service/SMB, session persistence и retirement старого interactive G2 path остаются OPEN.
