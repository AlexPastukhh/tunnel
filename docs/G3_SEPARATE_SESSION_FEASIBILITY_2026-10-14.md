# G3 — separate guest Windows session feasibility, 2026-10-14

**Status: SESSION3 AND GUEST MUTEX/HEADLESS EDGE CDP PASS; READ-ONLY GUEST STATION INVENTORY PASS; NEW PRIVATE G2 STATION FAIL/IPC/RUNTIME PENDING.** Guest process station=Session3 `WinSta0`, Visible=true; enumerated `WinSta0`, `Service-0x0-218d7932$` (name only; service-like station is not approved for G2). `CreateWindowStation(null,CWF_CREATE_ONLY=1,...)` returned Win32 183; do not remove create-only. Source/read-only actual result `G3_SESSION3_STATIONS_READONLY_2026-10-15.md` compares session-based OS GUI isolation against originally required distinct noninteractive G2 station; neither accepted for live G2 yet. User manually signed into `FORTIS_M\FortisHostG1` using Windows Fast User Switching, then returned to owner without signing out. Owner `quser` showed `alexa console ID 2 Активно` and `fortishostg1 ID 3 Диск` (disconnected but logged on). Thus separate guest Session 3 now exists. Actual later SID1009/Session3 unique `Local\` mutex PASS and own fresh-profile headless Edge/CDP startup PASS. Guest read-only station inventory PASS with current `WinSta0` Visible=true and second `Service-0x0-218d7932$` name-only; none establishes separate private G2 station, owner-clipboard negative acceptance or owner↔guest IPC. See `G3_SESSION3_STATIONS_READONLY_2026-10-15.md`.
This is not an authorization to create a session, service, task, registry value, firewall rule, new ACL, or runtime.
Owner HOST, Fortis Repo, G2 credentials, existing Windows sessions and Kaspersky protections must be preserved.

## Observed evidence (native reports)

- Owner elevated Preview after reboot: Session 2, original WinSta0/Default untouched, G2/unknown process inventory empty, owner WRITE_DAC ALLOW on both.
- Actual non-admin guest SID1009 in Session 2 and a matching private noninteractive Window Station: independent `NtOpenDirectoryObject` requests against `\\Sessions\\2\\BaseNamedObjects` returned `0xC0000022` for `DIRECTORY_CREATE_OBJECT (0x4)` and `READ_CONTROL (0x20000)`.
- Elevated owner read-only query returned DACL for that directory. Owner and owner logon SID get create access; Everyone has only QUERY/TRAVERSE and SID1009 no direct create grant. This explains the tested create access denial; it does not independently prove every Edge ProcessSingleton call.
- The earlier SID1009-owned unnamed private-station prototype ran installed Edge successfully, but no separate Terminal Services session is evidenced by that run.

## Current launcher and why a one-line fix is impossible

- `G2WindowSupervisor.StartUser` calls `CreateProcessWithLogonW(user,domain,password,LOGON_WITH_PROFILE=1,...)`.
- Its constructor creates the new Window Station and private desktop in the **owner process session**; `Attach` deliberately rejects guest processes whose TokenSessionId differs from the owner's SessionId.
- LOGON_WITH_PROFILE loads the account profile; it is **not** a Terminal Services session allocation API. The fact that actual SID1009 still ran in owner Session 2 confirms this locally.
- Different Window Station names within Session 2 do not create a new `Local\\` kernel-object namespace.
- Moving guest execution to another session requires a separate guest-session launcher/agent and a new cross-session control/cleanup design. Changing the `Attach` comparison or supplying a different `lpDesktop` would not safely achieve it.
## Options, decision and security boundaries

| Option | Feasibility | Security decision |
| --- | --- | --- |
| Existing ordinary separate Windows login/session for SID1009 | Potentially feasible if already present, then guest-local private Window Station and job | **Preferred investigation**, without touching owner BaseNamedObjects. Check session inventory first. |
| Local Fast User Switching: user deliberately signs in to SID1009 | Could establish a normal guest session; may change the foreground console and requires user interaction | **Only after explicit consent**. Do not switch, lock, log out or create a session automatically. |
| RDP-created guest session | OS edition, network and RDP configuration dependent | Do not enable RDP/firewall or network listeners for this experiment. |
| Scheduled task running without an interactive logon | Does not guarantee the desired client session, GUI or Chromium behavior | Not accepted as a workaround without native evidence; do not create task. |
| LocalSystem service + `WTSQueryUserToken` + `CreateProcessAsUser` | Documented high-trust/privilege-sensitive approach | Rejected for this phase: no new privileged service, `SeTcbPrivilege` or token handling. |
| Extend owner Session 2 BaseNamedObjects DACL with SID1009 CREATE | Could permit name creation for all guest names in the owner's session; risks collisions/DoS | Not authorized. No `Everyone` / broad ACL write, no system-wide change. |
| PrivateNamespace / renamed mutex workaround | Ordinary unchanged Node and Edge do not automatically use arbitrary private namespaces | Not sufficient for current opaque application dependencies. |

## Read-only next observation — no credential, no elevation required

From an **ordinary owner PowerShell**, execute only these Windows session inventory commands:

```powershell
'OwnerSession=' + [Diagnostics.Process]::GetCurrentProcess().SessionId
& "$env:SystemRoot\System32\quser.exe" 2>&1
```

This queries currently logged-on client sessions and prints session/user information. If `quser.exe` is not installed or returns an error, report that as-is; do not install software, modify Windows policies, or create a new account/session. Session enumeration alone does not prove guest identity via SID or access to its object directory.
## Guest Session 3 first live test staged

See `G3_GUEST_SESSION_MUTEX_TEST_2026-10-15.md`: exact guest SID1009, non-elevated, Session 3, one new unique owned `Local\\` mutex with immediate handle release. The user, not a remote fixture or assistant, performs the test locally after switching to the guest console; status pending. A passing result means only the guest's basic named-object creation works and does **not** approve Edge or the persistent launcher.

## Acceptance gates before any live separate-session prototype

1. Observe whether `FortisHostG1` has its **own** Windows client SessionId different from owner Session 2; distinguish from LSA logon sessions and private Window Stations.
2. Identify how a non-admin G2-owned *local* controller can start and supervise its own child/job in that guest session **without** an owner SYSTEM service, stored password, inherited owner token, or unconstrained cross-session handles.
3. Validate the guest-session-local `BaseNamedObjects` create access using fresh private mutex names; verify profile/temp/runtime read-only and workspace write permissions. Never enumerate or open owner objects or copy owner session data.
4. Test installed headless Edge fresh own profile, default sandbox, CDP/DOM/storage and cleanup, then CLI/Node/Python/Git; no screen or clipboard reads. Fail closed on Kaspersky alert.
5. Review explicit owner↔guest IPC endpoint, mutual authentication, narrow privileges, listener exposure, job lifetime, restart/logoff and recovery. Re-run owner WinSta0/Default denial tests by **fresh opens** without owner data access. Keep HOST/Repo available.
6. Only after complete acceptance and user approval may a production launcher / persistence architecture be considered; G3 remains BLOCKED now.

## Authority / documentation

- Microsoft, [Kernel object namespaces](https://learn.microsoft.com/en-us/windows/win32/termserv/kernel-object-namespaces): `Local\\` and default namespaces are per client session; different users can log on in different Terminal Services sessions.
- Microsoft, [CreateProcessWithLogonW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createprocesswithlogonw): creates an authenticated process, optional user profile; no guarantee of a new client session.
- Microsoft, [CreateProcessAsUser](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessasuserw): process session follows token; privilege requirements.
- Microsoft, [WTSQueryUserToken](https://learn.microsoft.com/en-us/windows/win32/api/wtsapi32/nf-wtsapi32-wtsqueryusertoken): LocalSystem + SeTcb privilege; meant for highly trusted services.
- Microsoft, [WTSEnumerateSessionsW](https://learn.microsoft.com/en-us/windows/win32/api/wtsapi32/nf-wtsapi32-wtsenumeratesessionsw): enumeration is read-only and permission-scoped.

**Only repo docs changed in this phase.** No Windows shell/transport-fixture, process start/restart, ACL write, service/task creation, token transformation, OS policy change, exception, commit or push.
