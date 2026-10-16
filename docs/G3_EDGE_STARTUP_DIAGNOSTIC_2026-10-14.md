# G3 — Edge startup diagnostic, 2026-10-14 00:46 Asia/Bangkok

Status: **diagnostics verified; actual G2 Edge startup remains pending. G3 OPEN / G4 NOT_ACCEPTED.**

The user-pasted report at 2026-10-13T17:15:19.7357704Z identifies the remaining failed gate. Expected/actual SID1009 and named private station match; admin=false, visible=false. Node and its ordinary PowerShell descendant stay in the private station. Workspace RW, protected runtime read/mutation-deny, own HTTP and temporary cleanup pass in this scope. Edge exits 21 before its own CDP port appears. Its 322 stderr bytes were counted but discarded. This does not establish the installed Edge's specific cause or accept browser compatibility.

## Current changes and pins

| Source | SHA256 |
| --- | --- |
| Start-G2PrivateWindow.ps1 | D5ED0848A6267CC9DBE937964249F6AE120CABD29D02EA4664B1D75A1A401452 |
| private-station-node-probe.js | 4A589A9FC038154787728B49021B1C8EC93C0BBC8E53C1ACEECEDB1CFB6A5BB0 |
| G2WindowSupervisor.cs (unchanged) | F61983384AFF51CCC007586DA614C710306FDCC52981C5C0A3B77AD98202045D |

The Node diagnostic captures at most 4096 bytes from its own fresh-profile Edge stderr, reports total/truncation and detects early exit promptly. A native fresh-profile lock-file probe uses GENERIC_WRITE, FILE_SHARE_READ, CREATE_ALWAYS and FILE_FLAG_DELETE_ON_CLOSE. Own process integrity SID and LABEL_SECURITY_INFORMATION-only station/desktop labels are reported. Label-read failure is diagnostic data, not a permission change.

No Edge sandbox flag, Supervisor, private or main window ACL, runtime guard or final acceptance predicate was weakened. No owner profile, clipboard, screen, credentials or owner logs were read. The isolated child remains the source of Edge stderr.

## Verification

Windows Node syntax and operator AST PASS. Embedded metadata C# compiles; owner synthetic delete-on-close test returns 0 and removes its temporary file. Owner test station=WinSta0, station/desktop label S:, own integrity SID S-1-16-8192. These are owner test results, not the pending G2 measurements.

Pinned component combined compile and captured-byte operator Preview PASS at 2026-10-13T17:46:42.9052352Z. Preview writes no ACLs and prompts no credentials. Main station/default DACL hashes remain 65FE8DB21AB625C1A8877A090002D3B6AF6ABB9261F11EE50BE090F2C42F1DCA / A571929DFA64CA5FC1B593E125A9204D207757FBB50F7AA5221013BB43396F17. Owner WRITE_DAC forecast remains ALLOW / ALLOW. Non-elevated inventory still has five protected-process UNKNOWN entries; only the launch's elevated inventory can close that guard.

## Next local action

Leave owner HOST and Fortis Repo running. Use a **fresh elevated owner PowerShell**; the previous console retains loaded C# types. Read and verify the exact bytes below, then execute those same bytes. Windows password and, only after full preflight PASS, the separate runtime key are entered locally and masked.

```powershell
$script = 'C:\Users\alexa\Repos\tunnel\runtime\host-g2\window-isolation\Start-G2PrivateWindow.ps1'
$bytes = [IO.File]::ReadAllBytes($script)
$sha = [Security.Cryptography.SHA256]::Create()
try { $hash = ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '') }
finally { $sha.Dispose() }
if ($hash -ne 'D5ED0848A6267CC9DBE937964249F6AE120CABD29D02EA4664B1D75A1A401452') {
    throw 'Скрипт изменился — запуск остановлен'
}
& ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($bytes))) -Mode Launch
```

Return the new synthetic JSON, especially Node.edgeStderr, edgeStderrTruncated, profileLockWin32, stationLabel, desktopLabel and integritySid. Do not infer a fix from exit 21 alone. Diagnose before altering permissions. Failed preflight must still stop before the runtime-key prompt and main owner ACL writes.

After a demonstrated Edge fix, full actual guest preflight and private runtime acceptance are required. Owner APIs, whole-chat tool routes, services/SMB, per-logon persistence and retirement of the old interactive G2 entry remain open gates.

The [machine-readable evidence](G3_EDGE_STARTUP_DIAGNOSTIC_2026-10-14.json) preserves the user report and exact tested scope. Earlier 2CB5… and 0CF2… pins are historical.
