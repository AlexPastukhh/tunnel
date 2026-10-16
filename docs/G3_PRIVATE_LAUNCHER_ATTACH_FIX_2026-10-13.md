# G3 — Attach privilege correction, 2026-10-13

Срез 2026-10-13T16:00:16.8605164Z / 23:00 Asia/Bangkok. **SCOPED_PRIVILEGE_FIX_STAGED / CREDENTIALED_RETRY_PENDING. G3 OPEN, G4 NOT_ACCEPTED.** [JSON evidence](G3_PRIVATE_LAUNCHER_ATTACH_FIX_2026-10-13.json); [предыдущая staging точка и полный план](G3_PRIVATE_LAUNCHER_STAGING_2026-10-13.md).

## Наблюдение и исправление

Пользовательский local Launch прошёл ValidateAccount, но StartUser вернул Win32 5. Сохранённый inner stack указывает на Attach после CreateProcessWithLogonW. Старый Check был inlined и не сохранял название native API; stack не различает OpenProcessToken от job operations. В source действительно отсутствовал обязательный scoped SeDebugPrivilege для owner cross-account token inspection, хотя такой scope уже использовался в privileged inventory.

G2WindowSupervisor теперь временно включает **существующий SeDebugPrivilege только у caller owner** при cross-account VerifyIdentity. AdjustTokenPrivileges захватывает PreviousState; scope восстанавливает его до создания/назначения Job и ResumeThread. TOKEN_ADJUST_PRIVILEGES относится к собственному owner token; token G2 не изменяется. Отсутствующая привилегия приводит к fail-closed Win32 1300. Check SID/non-admin/session, suspended creation, job kill-on-close, отсутствие inherited owner handles и masked credential/key flow сохранены. Ошибки CreateProcessWithLogonW/OpenProcessToken/enable/restore/job/resume теперь имеют явные stage labels и Win32 code.

Microsoft primary docs: [OpenProcessToken](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-openprocesstoken) требует enabled SeDebugPrivilege для другой учётной записи; [AdjustTokenPrivileges](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-adjusttokenprivileges) описывает PreviousState/restore и ERROR_NOT_ALL_ASSIGNED. Это подтверждает пропуск в source, но исправленный credentialed переход ещё должен пройти локальный selftest.

## Проверено

- CAS exact old source SHA до изменения двух Git-backed source files; new byte readback SHA PASS. Start-G2PrivateWindow.ps1 pin обновлён только для нового Supervisor.
- Windows combined C# compile, source/component pins, PowerShell AST parse и captured-byte Preview PASS.
- Non-admin owner scope test: DebugBefore=ABSENT, enable returned explicit Attach/EnableSeDebugPrivilege / Win32 1300, DebugAfter=ABSENT. Отсутствующая привилегия не добавлена; no credentials prompted. Actual enabled admin branch и credentialed StartUser остаются PENDING local.
- Owner WinSta0/default original hashes 65FE8DB…/A571929… совпали; WRITE_DAC after forecast ALLOW/ALLOW; Preview ACL writes=0.
- HOST 5580 / Repo 23904 сохранили CreationDate, healthz/readyz 200/200. Нет owner runtime restart, ACL Apply, ключевого файла, service/task/Docker/Site изменений, commit/push.
- Старые synthetic CAS/pipe/CLI/Edge проверки остаются историческим evidence для неизменённых частей; не объявляют исправленный production runtime accepted.

## Локальный повтор

Предыдущее owner PowerShell уже загрузило старый C# type, поэтому нужен **fresh elevated owner PowerShell под alexa**. Не закрывать HOST/Repo. Старый G2 уже был остановлен для первой попытки; duplicate guard всё равно проверит отсутствие SID1009/UNKNOWN before writes.

```powershell
$script = 'C:\Users\alexa\Repos\tunnel\runtime\host-g2\window-isolation\Start-G2PrivateWindow.ps1'
$bytes = [IO.File]::ReadAllBytes($script)
$sha = [Security.Cryptography.SHA256]::Create()
try { $hash = ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '') }
finally { $sha.Dispose() }
if ($hash -ne '3A30DF3BCBA12E6B08611A2316ACD13F8F2AC5986E3CB8B584F2F85F311FEC26') {
    throw 'Скрипт изменился — запуск остановлен'
}
& ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($bytes))) -Mode Launch
```

Пароль FortisHostG1 и separate G2 key вводить только в local masked prompts; не присылать их. Credentialed private CLI/Edge selftest и повторный zero-G2 inventory предшествуют key prompt, owner-only backup и owner window ACL Apply. Если отказ повторится, вернуть stage/Win32 error из новой версии. Keep owner supervisor console open after startup.

## Pins и оставшиеся gates

| Source | SHA256 |
|---|---|
| G2WindowSupervisor.cs | 1A7D66AFC9B7933DA2AFF8EAB7915D008DA4752EF76702020E33974BB680038B |
| Start-G2PrivateWindow.ps1 | 3A30DF3BCBA12E6B08611A2316ACD13F8F2AC5986E3CB8B584F2F85F311FEC26 |

Прежние E56E0A40… operator / 0A097A40… supervisor pins — исторические, не использовать для нового Launch. Rollback procedure и backup scope из staging document сохранены; явный откат вызывается через **новый pinned operator** с Mode Rollback и exact printed Backup path.

После credentialed успеха: actual native MCP/private-station chain/owner-object open DENY/retained-handle boundary/Windows CLI/Edge/Workspace/runtime/UI/API/owner preservation acceptance. Owner local APIs, whole-chat routes, service/SMB residuals, per-logon-session persistence и retirement interactive entry path остаются незакрытыми; G4 не принят.
