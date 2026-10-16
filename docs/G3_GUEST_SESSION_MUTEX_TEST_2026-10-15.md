# G3 — separate guest session named-object test, 2026-10-15

**Status: ACTUAL GUEST SESSION NAMED-MUTEX PASS / HANDLE CLEANUP TO CONFIRM.** User-reported actual non-admin SID1009 in Windows Session 3 created a fresh uniquely named `Local\\` mutex successfully; this is not Edge, private desktop, supervisor or persistent G2 acceptance. User separately pasted `finally {}` into PowerShell after the successful JSON, which produced `CommandNotFoundException`: the exception indicates `finally` was treated as an independent statement, **not** that mutex creation failed. Because the successful code might have run without its structured `finally`, user was advised to dispose `$mutex` if their guest console is still open; otherwise closing the PowerShell process will close the handle.

The owner `quser` now reports:
- `alexa` console Session 2 `Активно`.
- `fortishostg1` Session 3 `Диск` (disconnected), after the user manually switched back from a guest Windows sign-in.

This confirms a distinct Windows client session, not that SID1009 can create named objects in it. The earlier `0xC0000022` arose when SID1009 was launched in **owner Session 2**.

## Actual manual guest test result

User returned this JSON from ordinary guest PowerShell (Windows Session 3):

```json
{"Sid":"S-1-5-21-303538662-3368424508-2654684973-1009","Session":3,"Admin":false,"NamedMutexCreated":true,"Status":"PASS","AclWrites":0,"OwnerObjectsTouched":0}
```

**Finding:** guest can create unique own `Local\\` named mutex in its separate client Session 3. The prior Session 2 owner-created guest process returned Win32 5 / NTSTATUS ACCESS_DENIED, consistent with session namespace DACL separation. This rules out a universal SID1009 prohibition on named mutexes; it does not establish headless Edge and G2 launcher acceptance.

The user then entered `finally {...}` as a standalone statement, receiving `finally: CommandNotFoundException`. That is a PowerShell parsing issue only; the guest's `Status=PASS` remains valid. Since the cleanup block may not have been executed, locally dispose the surviving `$mutex` handle using `if ($null -ne $mutex) { $mutex.Dispose(); $mutex = $null }` in **the same guest console** or close that console to release process handles. No claim is made about cleanup until confirmed. The named mutex is a unique randomly named guest-owned object only.

**Next gate staged, not yet run:** bounded guest Session 3 synthetic headless-Edge fresh-profile test (default sandbox, no owner screen/clipboard/cookies, no remote bridge or service), documented at `G3_GUEST_SESSION_EDGE_SMOKE_2026-10-15.md` and source `../runtime/host-g2/window-isolation/Test-G3GuestEdgeSession3.ps1`. On pass, proceed only after review to a separate noninteractive Window Station test in guest's own session and lifecycle/IPC architecture review. Do not run the current owner Session 2 `Start-G2PrivateWindow.ps1 -Mode Launch` or modify its session pin. G3 remains BLOCKED.

## Safe local guest-console-only test

1. Use **Switch user**, not **Sign out**, to return to the existing `FortisHostG1` session.
2. Open ordinary, **non-elevated** Windows PowerShell under guest. Do not change security policy if it fails to open.
3. Paste the block below. It checks exact guest SID, Session 3, and non-admin status **before** creating a single unique owned `Local\\FortisG3GuestCheck-{GUID}` mutex. It closes the handle in `finally` and does not open owner objects or run Edge/Node, fixtures, services, tasks, browsers, persistent runtimes, IPC or ACL writes.
4. Switch back to owner without signing either account out. Send the printed JSON (no passwords).

```powershell
$ErrorActionPreference = 'Stop'
$id = [Security.Principal.WindowsIdentity]::GetCurrent()
$session = [Diagnostics.Process]::GetCurrentProcess().SessionId
$admin = (New-Object Security.Principal.WindowsPrincipal($id)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$expected = 'S-1-5-21-303538662-3368424508-2654684973-1009'
if ($id.User.Value -ne $expected -or $session -ne 3 -or $admin) { throw 'Guest identity/session check failed: do not continue' }
$name = 'Local\FortisG3GuestCheck-' + [guid]::NewGuid().ToString('N')
$created = $false
$mutex = $null
try {
    $mutex = [System.Threading.Mutex]::new($false, $name, [ref]$created)
    if (!$created) { throw 'Unique guest mutex name already exists' }
    [pscustomobject]@{Sid=$id.User.Value;Session=$session;Admin=$admin;NamedMutexCreated=$created;Status='PASS';AclWrites=0;OwnerObjectsTouched=0}|ConvertTo-Json -Compress
} catch {
    [pscustomobject]@{Sid=$id.User.Value;Session=$session;Admin=$admin;NamedMutexCreated=$false;Status='FAIL';ErrorType=$_.Exception.GetType().FullName;HResult=$_.Exception.HResult;AclWrites=0;OwnerObjectsTouched=0}|ConvertTo-Json -Compress
} finally {
    if ($null -ne $mutex) { $mutex.Dispose() }
}
```

**Pass**: exact SID1009 / guest Session 3 / `Admin=false` / `NamedMutexCreated=true`; not yet proof Chromium works. If guest PowerShell cannot open, identity/session check fails, or Kaspersky flags an action, stop without bypassing controls.

Even a passing guest-owned namespace test does not solve owner↔guest job/IPC lifecycle. The present launcher builds its window station in Session 2 and requires the child SessionId to equal owner, so **do not** try `-Mode Launch`, rewrite the check, grant access on Session 2, or run as SYSTEM. Follow design and acceptance gates in `G3_SEPARATE_SESSION_FEASIBILITY_2026-10-14.md`.

**Only repository documentation was staged here.** No native Windows command executed via remote tooling, no Windows object or ACL changed by the assistant, and no commit/push.
