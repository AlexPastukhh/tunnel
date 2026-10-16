# G3 — private object compatibility, 2026-10-14 01:11 Asia/Bangkok

**STAGED / WINDOWS_CHECKS_PASS / ACTUAL_G2_EDGE_PENDING. G3 OPEN / G4 NOT_ACCEPTED.**

User report at 2026-10-13T17:52:10.9063423Z confirms the earlier CLI/runtime/private-station results and isolates installed Edge exit21 to ProcessSingleton creation. Native delete-on-close profile file succeeds (0). Own token integrity is Medium (S-1-16-8192); labels contain no explicit High ACE. Captured stderr contains only ProcessSingleton failure. This does not determine the exact internal Edge Win32 failure.

## Narrow correction

The successful earlier G2-owned private prototype gave full access to its own private objects. The staged owner-created objects instead gave SID1009 only 0x2037f / 0x201ff, omitting DELETE, WRITE_DAC and WRITE_OWNER. Chromium's [sandbox desktop source](https://chromium.googlesource.com/chromium/src/+/refs/tags/128.0.6613.50/sandbox/win/src/window.cc) clones current desktop ACL and requests DESKTOP_CREATEWINDOW | DESKTOP_READOBJECTS | READ_CONTROL | WRITE_DAC | WRITE_OWNER (0xe0003), applying its own Restricted-code deny separately.

Restore SID1009 full access **only on the new named noninteractive private station and its default desktop**: 0xf037f / 0xf01ff. Owner/SYSTEM full grants remain. Guest may now modify the ACLs of these private objects; owner retains pre-opened supervisor handles and the kill-on-close job. These grants do not grant access to owner WinSta0/default, services or filesystem. Main SID1009 deny masks, approved owner hashes, backup/CAS/rollback and all Apply guards are unchanged. Edge sandbox is unchanged.

This fixes a demonstrated compatibility omission; it is **not yet proof** of the installed Edge ProcessSingleton cause. Actual guest preflight remains mandatory before main ACL writes/key stage.

## Exact current pins

| File | SHA256 |
| --- | --- |
| Start-G2PrivateWindow.ps1 | 05B63616B857699DF6E19D957DDDAB7BA1196E977A6CE3D4B21706F7C8F42434 |
| G2WindowSupervisor.cs | E63C215501DE2F5D5AA19FF569C107014E77E04BDAF287906B362B21A0CFEFE0 |
| private-station-node-probe.js | BE064FBE5F7FBF12CDEE4DF6E04FA766FDD2DE1DAD6D2F6FC42B03CEBB9E016E |

Prior D5ED… operator, F619… supervisor and 4A58… Node pins are historical. Intermediate 8E93… operator was verified but is superseded by the final diagnostics pin above.

## Verification

Windows pinned combined C# compilation, PowerShell AST, Node syntax and read-only Preview PASS at 2026-10-13T18:11:28.0855814Z. Current owner standard-token in-memory descriptors with the same guest grant shape: old desktop Chromium request DENY -> new ALLOW; old full station DENY -> new ALLOW; main station and desktop explicit deny still DENY. This is not an actual SID1009 live access test.

Main WinSta0/default original DACL hashes still match; WRITE_DAC forecast ALLOW/ALLOW; Preview ACL writes=0, credential prompts=false. Five protected-process UNKNOWN entries remain in the non-elevated Preview; local elevated launch still requires complete inventory.

Added bounded native diagnostics to Node's own metadata grandchild: startupMutexOpenWin32 (read/open only, never acquire or modify existing startup mutex); ownMutexCreateWin32 (new unique test mutex, closed); messageWindowWin32 (own message-only window, destroyed, allowed only in FortisG2-* station). No owner screen/clipboard/windows enumeration occurs. Owner test sees startup mutex absent (2), own random mutex create=0, main-station message-window guard=-1. Installed Edge binary's public string confirms Local\\ChromeProcessSingletonStartup!, consistent with [upstream ProcessSingleton source](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/chrome/browser/process_singleton_win.cc).

## Local launch

Leave owner HOST and Fortis Repo running. Use a **fresh elevated owner PowerShell** because previous C# types remain loaded. Read, verify and run the same operator bytes:

```powershell
$script = 'C:\Users\alexa\Repos\tunnel\runtime\host-g2\window-isolation\Start-G2PrivateWindow.ps1'
$bytes = [IO.File]::ReadAllBytes($script)
$sha = [Security.Cryptography.SHA256]::Create()
try { $hash = ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '') }
finally { $sha.Dispose() }
if ($hash -ne '05B63616B857699DF6E19D957DDDAB7BA1196E977A6CE3D4B21706F7C8F42434') {
    throw 'Скрипт изменился — запуск остановлен'
}
& ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($bytes))) -Mode Launch
```

Enter Windows password locally/masked. If full actual CLI/Edge preflight passes, the existing authorized flow asks for the separate G2 runtime key locally/masked and continues to backup/main deny/private runtime. If it fails, return the synthetic JSON (including the new mutex/window Win32 fields); main ACL/key stage must still remain untouched.

Live acceptance must then verify private runtime station, fresh opens denied on owner objects, CLI/headless Edge compatibility, workspace/runtime protections, UI suppression and preserved owner HOST/Repo health. Owner APIs, whole-chat tool routes, services/SMB, per-logon persistence and retirement of interactive G2 entry remain open.

No common runtime/service/task or owner tunnel restart, Site publication, Git commit or push occurred. [Machine-readable evidence](G3_PRIVATE_OBJECT_COMPATIBILITY_2026-10-14.json) includes the full user report and tested scope.
