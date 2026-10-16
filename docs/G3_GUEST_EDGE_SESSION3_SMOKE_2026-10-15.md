# G3 — Guest Session 3 Edge startup smoke test, 2026-10-15

**ACTUAL GUEST SESSION 3 EDGE STARTUP/CDP FILE PASS / PRIVATE STATION AND G2 STILL BLOCKED.** Windows C# compiled and ran in the user's local ordinary guest PowerShell; synthetic `about:blank` / own temporary-profile CDP smoke succeeded. G3 remains BLOCKED.

Source: `runtime/host-g2/window-isolation/Test-G3GuestSessionEdge.ps1`
SHA256: `2A9B2FF45E234E69F7461F8C00421DED0C34BA19C420C17739641CC42B933527`.

Actual prior test: guest SID1009 in separate Windows Session 3, ordinary token, created unique `Local\\FortisG3GuestCheck` mutex successfully. This new test is **not** a full Edge DOM/CDP/storage test, nor private-station or runtime acceptance.

## User-reported actual Windows guest run — PASS

The user ran the **pinned** test under local SID1009 Session 3. Console output included Edge `DevTools listening on ws://127.0.0.1:<ephemeral>/devtools/browser/<uuid>` and synthetic JSON:

```json
{"Sid":"S-1-5-21-303538662-3368424508-2654684973-1009","Session":3,"Admin":false,"EdgeStartup":true,"JobStopped":true,"ProfileRemoved":true,"Result":"PASS","NativeResult":"CDP=True;Stopped=True;EarlyExit=False;ExitCode=259;Assigned=True;Pid=19016","ErrorType":null,"ErrorMessage":null,"Scope":"Guest Session 3 own about:blank CDP file only; no owner objects or clipboard/screen"}
```

**Accepted narrowly:** guest SID1009, non-admin, in its own client Session 3 can launch the installed Edge headless with standard sandbox and fresh private temp profile; the own `DevToolsActivePort` appeared. The synthetic Edge process was attached to the kill-on-close job; `JobStopped=true` and `ProfileRemoved=true` reported after cleanup. `ExitCode=259` here is the stored STILL_ACTIVE code before job closure, **not** evidence a browser process is still running; report confirms job stop afterward. Actual CDP protocol interaction, DOM/storage, private noninteractive guest Window Station/desktop and owner-guest IPC have NOT been tested in this run. There is no persistent runtime acceptance.

The `ws://127.0.0.1:<ephemeral>` link in console is a disposable local debugging endpoint while Edge runs. Test closed its job, so that particular endpoint is not intended to remain available. Never publish it as a remote reachable URL or treat it as an authentication secret.

**Next gate (staged, not yet run):** first a guest Session 3 local private **noninteractive** Window Station/default desktop create/restore/close check, documented at `G3_GUEST_PRIVATE_STATION_SMOKE_2026-10-15.md` (does **not** launch a child). After passing, separately add a synthetic child job to verify inherited station and cleanup, and only then Edge fresh profile + CDP in that station. Reuse design evidence from the earlier SID1009-owned **unnamed** private station success, but do not use the owner Session 2 launcher: its station and token/session guards target the wrong session. No owner WinSta0/default ACL writes, no SYSTEM service, no bypass of browser sandbox or Kaspersky.

## Guest-only behavior

- Fail closed unless token SID1009, SessionId=3, non-admin; refuse previous loaded C# type.
- Choose installed Microsoft Edge at a fixed system Program Files path, reject executable reparse point.
- Create a GUID-random own profile under the guest's TEMP folder. Never touch owner profile, cookies, screen, clipboard, named objects or owner window station.
- Create unnamed Win32 job with `KILL_ON_JOB_CLOSE`; start only guest Edge **suspended**, attach to job, resume, wait at most 20s for `DevToolsActivePort` file in its own profile. Uses `--headless=new`, `about:blank`, `--remote-debugging-address=127.0.0.1`, ephemeral port=0, no first run/extensions/sync/background networking. **No `--no-sandbox`**. Does not read CDP port, issue DevTools commands, start HTTP server or read page content.
- Close job (kills attached processes), wait up to 10s for browser process exit, then remove only the own random temp root. On failure, report `Result=FAIL` and cleanup state; do not change ACL, config, OS policies, tasks, services or other browser processes.
- Kaspersky may flag process creation/Win32 Add-Type even if this is legitimate testing: **stop immediately on any detection and do not add exceptions**, recover quarantined code or disable protection.

## Guest-readable transfer, performed manually under owner (no elevated permissions)

The repo is in owner's user profile; do **not** assume guest can read it. With owner ordinary PowerShell, check the source hash and manually copy only this synthetic test script to the existing Public Documents folder using a non-overwriting destination:

```powershell
$src='C:\Users\alexa\Repos\tunnel\runtime\host-g2\window-isolation\Test-G3GuestSessionEdge.ps1'
$dst='C:\Users\Public\Documents\FortisG3Edge-2A9B2FF4.ps1'
$expected='2A9B2FF45E234E69F7461F8C00421DED0C34BA19C420C17739641CC42B933527'
if((Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash -ne $expected){throw 'Source hash changed'}
if(Test-Path -LiteralPath $dst){throw 'Existing transfer file: review; do not overwrite'}
Copy-Item -LiteralPath $src -Destination $dst -ErrorAction Stop
if((Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash -ne $expected){throw 'Copied hash mismatch'}
'G3 guest test file staged (not executed)'
```
## Local guest run (no elevation and no credential prompt)

Use Windows **Switch user** to the existing FortisHostG1 Session 3; open normal PowerShell and run the complete block as one action:

```powershell
$p='C:\Users\Public\Documents\FortisG3Edge-2A9B2FF4.ps1'
$expected='2A9B2FF45E234E69F7461F8C00421DED0C34BA19C420C17739641CC42B933527'
$b=[IO.File]::ReadAllBytes($p)
$sha=[Security.Cryptography.SHA256]::Create()
$actual=([BitConverter]::ToString($sha.ComputeHash($b))).Replace('-','')
$sha.Dispose()
if($actual -ne $expected){throw 'Guest test hash changed'}
& ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($b)))
```

Expected JSON: SID1009, Session3, Admin=false, `EdgeStartup=true` if an own `DevToolsActivePort` file was seen, `JobStopped=true`, `ProfileRemoved=true`, `Result=PASS`. Report FAIL/errors as-is; do not modify policy to compensate.

After the test, switch back to the owner **without signing out either user**, send only this synthetic JSON. Removing the copy in Public Documents should happen after the result is reviewed; owner may then delete *only that one copied file*.

Another staged script `Test-G3GuestEdgeSession3.ps1` exists in this shared repo and uses a different smoke method (`--dump-dom`, `taskkill` cleanup). Do NOT run both tests, blend their pins or treat them as mutually validated. For this step only `Test-G3GuestSessionEdge.ps1` at the pinned hash above is recommended for stronger child-process cleanup; it validates CDP port-file startup, not DOM. **Not validated on Windows in this phase.** Repo Python structural source audit PASS; complete C# compilation/PowerShell AST and native guest Edge smoke PENDING. No Windows remote tool used, no Git commit/push.
