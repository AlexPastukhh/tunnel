# G3 — guest Session 3 Edge smoke test, 2026-10-15

**STAGED ONLY; native guest execution pending.** This is a narrow local manual test, not a G2 runtime change, and it does not prove CDP/storage, network access or private station isolation.

## Basis and hypothesis

- Actual owner client session 2, guest SID1009 client session 3 established by user's Fast User Switching.
- In Session 2 guest NtOpenDirectoryObject of the owner's BaseNamedObjects returned 0xC0000022 for create and READ_CONTROL.
- Guest Session 3, non-admin SID1009, independently created its own unique Local-named mutex successfully.
- Earlier owner-created private-station Edge failed ProcessSingleton, exit 21; guest-session Edge has **not** been run yet.

## Staged narrow manual test

Source file: runtime/host-g2/window-isolation/Test-G3GuestEdgeSession3.ps1

SHA256: 1DD2FAD0175C9AB23A85577ED80B2954F736C0700306BD76F75BCD73C4B15136

The file resides inside the owner repository C:\Users\alexa\Repos\tunnel and **may not be readable by SID1009**. Do not grant guest access to owner repo to run it. The user should paste the entire reviewed PowerShell block from ChatGPT into an ordinary, non-elevated PowerShell under the existing guest Session 3. Paste the entire & { ... } block at once, not isolated finally statements.
Preflight checks expected SID1009, Windows Session 3, and non-admin token before launching any process. Installed Edge is read only. The script creates a GUID-named temporary folder under guest %LOCALAPPDATA%\FortisHostG2\Workspace\scratch, rejects reparse points on scratch root, runs Edge headless with default sandbox, fresh --user-data-dir and --dump-dom against a synthetic data:text/html URI. Background networking/extensions/sync are disabled. No owner profile/cookies/clipboard/screen/system data or network URLs are used.

The script waits at most 25 seconds for Edge; if timeout/error occurs it targets the exact spawned Edge PID and descendants via taskkill /T /F. The temporary folder is removed in a finally block with bounded retries. JSON includes EdgeExitCode, DomMarkerFound, TimedOut, ProfileRemoved and Status. PASS requires exit 0, DOM marker and successful cleanup. If cleanup fails, Status=FAIL; do not run follow-up until leftover guest scratch can be inspected.

Windows native PowerShell AST / guest execution is not yet verified (Fortis Repo Docker lacks pwsh); best-effort Windows process-tree kill does not formally prove no residual processes. If Kaspersky generates an alert, stop; no exclusions, no repeated launch until reviewed.

A passing result would prove **only** that installed Edge can launch and render a synthetic DOM in guest's interactive Session 3, not private noninteractive guest station/desktop isolation, CDP/storage, owner UI denial, guest-controller IPC/job lifecycle or persistent G2. Existing owner Session 2 launcher must not be used with Launch mode.

**Only Repo sources/docs were staged. No Windows remote fixture, ACL, service/task, antivirus setting, runtime, live launcher, OS policy, commit or push was modified.**
