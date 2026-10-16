# G3 — guest-owned private Window Station smoke, 2026-10-15

**TWO ACTUAL NON-ADMIN STATION CREATE ATTEMPTS FAILED; SECOND CWF_CREATE_ONLY RETURNED WIN32 183.** G3 remains BLOCKED. Windows non-admin SID1009 reached `CreateWindowStation` but the explicit `FortisG3-{GUID}` name was rejected; PowerShell displayed `Create private window station` without numeric Win32 code. Microsoft's `CreateWindowStationW` documentation explicitly restricts specifying names to Administrators. This was a test-source mistake; it does not disprove separate-session object compatibility. Do not repeat the former SHA.

## Evidence and exact scope

- User locally proved SID1009 non-admin Session 3 creates a unique `Local\\` mutex.
- The user then returned actual `Result=PASS` for `Test-G3GuestSessionEdge.ps1`, SHA256 `2A9B2FF45E234E69F7461F8C00421DED0C34BA19C420C17739641CC42B933527`; guest installed Edge launched headless `about:blank`, own `DevToolsActivePort` appeared, kill-on-close job stopped, temp profile removed.
- That Edge test did **not** put the browser in a guest-owned noninteractive station. Existing owner-created station in owner Session 2 had Edge ProcessSingleton failure due to inaccessible named objects.
- The next test isolates the next missing gate: can guest SID1009 **inside its own Session 3** create an *unnamed-by-caller* noninteractive private window station and `default` desktop, then restore its original station and close both handles? **No Edge/Node/G2 child is launched in this test.**

Source: `runtime/host-g2/window-isolation/Test-G3GuestPrivateStation.ps1`. The earlier failed named-station source had SHA256 `717D0F1105B80795859204656CD4BC6D6C6B8945B1175EFE5B97ADB1B24162E6` and must not be run again.
SHA256: `9F82E0E35D47CE32411AB52139DCDF4C41AFBB42F549562539955C916DC843F6`.

It requires *exact SID1009, Session=3, non-admin* before compiling C#. It creates new objects with explicit `SY`+SID1009 full-access DACLs **only on those new objects**. Uses `CreateWindowStation(null, CWF_CREATE_ONLY=1, ...)`: Windows assigns the logon-derived name, and `CREATE_ONLY` refuses to return a handle for an already existing station. Flags do not make a station interactive; it checks the returned name is not `WinSta0` and `Visible=false`, temporarily selects the new station, creates its desktop named `default`, then restores the original station and closes private handles. Native Win32 errors now include an exact numeric code. The system-derived name is not expected to begin `FortisG3-`. This conservative create-only behavior can fail if such a station already exists; never bypass on failure. Does not change ACLs of owner WinSta0/default, services, system objects or existing guest WinSta0/default; no screen/clipboard/profile content reads. The corrected C# **compiled and ran locally** under SID1009 Session 3, but `CreateWindowStation(null, CWF_CREATE_ONLY=1,...)` returned `Win32 183 / ERROR_ALREADY_EXISTS`. The create-only guard prevented reuse of the preexisting system-derived station; no station/desktop was created by this attempt. Details and a new **read-only** guest station-metadata probe: `G3_GUEST_STATION_EXISTING_OBJECT_2026-10-15.md`. Do NOT remove create-only to force success; no AV exceptions.
## One-file transfer under owner (ordinary PowerShell, not elevated)

The owner source path may not be readable by guest. Copy only this pinned test file to Public Documents; do not grant the guest owner-repository access:

```powershell
$src='C:\Users\alexa\Repos\tunnel\runtime\host-g2\window-isolation\Test-G3GuestPrivateStation.ps1'
$dst='C:\Users\Public\Documents\FortisG3Station-9F82E0E3.ps1'
$expected='9F82E0E35D47CE32411AB52139DCDF4C41AFBB42F549562539955C916DC843F6'
if((Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash -ne $expected){throw 'G3 source hash mismatch'}
if(Test-Path -LiteralPath $dst){throw 'Existing destination; no overwrite'}
Copy-Item -LiteralPath $src -Destination $dst -ErrorAction Stop
if((Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash -ne $expected){throw 'G3 transfer hash mismatch'}
'Private station probe staged only'
```
## Guest manual run (fresh non-elevated PowerShell, Session 3)

Use Windows **Switch user**, not Sign out. In the existing FortisHostG1 Session 3, open a fresh *ordinary* PowerShell and paste **one block**:

```powershell
$p='C:\Users\Public\Documents\FortisG3Station-9F82E0E3.ps1'
$expected='9F82E0E35D47CE32411AB52139DCDF4C41AFBB42F549562539955C916DC843F6'
if((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -ne $expected){throw 'Guest file hash mismatch'}
& ([scriptblock]::Create([Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes($p))))
```

Expected JSON: SID1009, Session3, Admin=false, a system-assigned private Station name (not `WinSta0`; no `FortisG3-` prefix), `Desktop=default`, `Visible=false`, `GuestProcessStationRestored=true`, `PrivateDesktopClosed=true`, `PrivateStationClosed=true`, `Result=PASS`.

On a failure or Kaspersky alert, stop and report the error as-is; do not bypass restrictions, restart owner/guest sessions or re-run blindly. If the probe reports that original station was not restored, **close that disposable guest PowerShell console** before any other actions; do not run further GUI tests in it. Never run owner `Start-G2PrivateWindow.ps1 -Mode Launch` for Session 3.

## After passing

**Do not claim G3 accepted**. A subsequent separate guest-owned controller test must launch a *synthetic* child inside this station with job cleanup, validate inherited station and its name-object rights; then run Edge/CLI/Node under its private desktop and finally design owner↔guest IPC and logout/reboot recovery. Guest's separate Windows login session is currently user-created and may not survive logoff/reboot. The browser sandbox must stay enabled.

Only repository source/docs were staged; no Windows remote fixtures, services/tasks, Kaspersky policy, ACL for existing objects, owner runtime, or Git commit/push.
