# G3 — Guest Session 3 CWF_CREATE_ONLY existing Window Station, 2026-10-15

**ACTUAL NATIVE RESULT: BLOCKED at creation / root behavior identified / no ACL modification.** This does not undo previous guest Session3 unique Local mutex and headless Edge/CDP startup PASS.

## Confirmed result

The user ran SHA256-pinned `Test-G3GuestPrivateStation.ps1` revision `9F82E0E35D47CE32411AB52139DCDF4C41AFBB42F549562539955C916DC843F6` locally under ordinary guest SID1009 in Session 3. Hash check PASS and native C# compiled. The only observed exception:

```text
Create private window station failed (Win32 183)
```

This is `ERROR_ALREADY_EXISTS`. The code called `CreateWindowStation(null, CWF_CREATE_ONLY=1, 0xf037f, ...)` after SID1009/Session3/nonadmin validation. Microsoft documents: when station name is null, its name is derived from the calling **logon session**; when CWF_CREATE_ONLY is set and that name already exists, the API fails. This is **not** STATUS_ACCESS_DENIED, not a named-mutex regression, and not evidence that the existing station is suitable for isolation. No station was created, no switch to another station, no private desktop was created, no owner station DACL changed. The guard prevented accidental reuse.

Do **not** change CWF_CREATE_ONLY to zero and treat a returned handle as an isolated private station: Windows may return an already-existing station; no new per-G2 security boundary is established. Do not run the old explicitly named non-admin test either (admin-only naming), make guest an administrator, grant Everyone access, create privileged services/tasks, change owner WinSta0 ACL, or disable Kaspersky.
## Next bounded observation — guest-only metadata, not owner objects

Staged script: `runtime/host-g2/window-isolation/Inspect-G3GuestStations.ps1`
SHA256: `941FED61BEB08A9370AEDFF8D4E05511AC4A896B9BCAD293312F2C7792BEB4E4`.

- Validates exact SID1009, Session 3, non-admin **before** any native call.
- Uses **only** `GetProcessWindowStation` plus `GetUserObjectInformationW(UOI_NAME,UOI_FLAGS)` on the calling process's existing handle and `EnumWindowStationsW` (name-only enumeration of accessible stations within **Session 3**). It neither opens nor creates stations/desktops, switches objects, reads windows/clipboard/desktop content, reads/writes DACLs nor touches owner Session 2.
- Enumeration may fail due to the non-admin token; JSON will report `EnumerationAllowed=false` and `EnumerationWin32`; no bypass. Enumerating names **does not prove** an object's ACL, session-logon origin, owner, or suitability for private G2.
- Repo source static check PASS. Native PowerShell/C# compilation and actual guest run **PENDING**. Stop on Kaspersky detection; do not add exclusions.

## Owner-mediated one-file transfer (ordinary owner PowerShell)

Do not grant SID1009 read permission to the owner's repository; copy only this pinned read-only probe to a new Public Documents filename, without overwriting existing content:

```powershell
$src='C:\Users\alexa\Repos\tunnel\runtime\host-g2\window-isolation\Inspect-G3GuestStations.ps1'
$dst='C:\Users\Public\Documents\FortisG3StationInspect-941FED61.ps1'
$expected='941FED61BEB08A9370AEDFF8D4E05511AC4A896B9BCAD293312F2C7792BEB4E4'
if((Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash -ne $expected){throw 'Source hash mismatch'}
if(Test-Path -LiteralPath $dst){throw 'Existing destination refused'}
Copy-Item -LiteralPath $src -Destination $dst -ErrorAction Stop
if((Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash -ne $expected){throw 'Copy hash mismatch'}
'G3 guest read-only station metadata probe staged'
```
## Guest Session 3 run (fresh ordinary guest PowerShell)

```powershell
$p='C:\Users\Public\Documents\FortisG3StationInspect-941FED61.ps1'
$expected='941FED61BEB08A9370AEDFF8D4E05511AC4A896B9BCAD293312F2C7792BEB4E4'
if((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -ne $expected){throw 'Guest probe hash mismatch'}
& ([scriptblock]::Create([Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes($p))))
```

Return only synthetic JSON fields `CurrentStationName`, `CurrentStationVisible`, `EnumerationAllowed`, `EnumerationWin32`, `AccessibleStationNames` and SID/session/admin. No passwords, secrets, desktop images, clipboard or owner account artifacts.

## Completed guest metadata inspection — actual native PASS

User ran pinned SHA256 `941FED61BEB08A9370AEDFF8D4E05511AC4A896B9BCAD293312F2C7792BEB4E4` under non-admin SID1009 / Session 3. `GetProcessWindowStation` name `WinSta0`, Visible=true; `EnumWindowStationsW` succeeded Win32 0 and returned names `WinSta0`, `Service-0x0-218d7932$`. Creates=0, ACLWrites=0, DesktopReads=0, OwnerSessionTouched=false. The service-like station is only an enumerated name; its ownership/ACL/suitability was not established and **must not** be used for G2. Windows session 3 has its own `WinSta0` separate from owner's session 2 `WinSta0`. Full evidence and alternative G3 designs: `G3_SESSION3_STATIONS_READONLY_2026-10-15.md`. Previous 'actual run PENDING' below is a historical staging instruction, now superseded by this result.

## Architecture consequence

A regular logged-in SID1009 in Terminal Services Session 3 already has an automatically named logon-window-station object in this context. A genuinely **new private** Window Station for the controlled G2 process will require a separately reviewed process/logon/session architecture, not simply swapping the CreateWindowStation flag. Earlier successful unnamed SID1009 prototype used a **different execution/logon context** and does not establish that a new station can be created from the already-connected interactive guest token. The owner launcher still creates its station in owner Session2 and cannot be redirected just by changing a desktop string.

Next architecture design should explain and separately verify (1) new guest noninteractive logon context, (2) its `BaseNamedObjects` creation rights within Session3, (3) owner↔guest supervisor lifecycle/job/IPC and isolation, (4) browser default sandbox and fresh-profile CDP/DOM and cleanup, and (5) logoff/reboot. No cross-session privileged broker or owner ACL mutation is approved yet.

Sources: [Microsoft CreateWindowStationW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-createwindowstationw), [EnumWindowStationsW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-enumwindowstationsw), [GetUserObjectInformationW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getuserobjectinformationw).

**No Windows remote shell, service, task, session, AV setting, ACL, runtime, Git commit or push was changed by the assistant.**
