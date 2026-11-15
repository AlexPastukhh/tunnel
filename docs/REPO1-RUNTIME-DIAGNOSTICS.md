# Repo1: visible runtime diagnostics and Session terminated

## Confirmed source difference

Script Center delegates Repo1 to `runtime/windows-repo/current/Repo1-Worker.ps1`, then `launchers/chatgpt-repo-mode/run-tunnel-quiet-logs.ps1`.
The previous runtime invocation used `*> $null`: Script Catalog captured startup banners but no runtime stdout/stderr. It already requested debug JSONL at `%USERPROFILE%\chatgpt-repo-mode\runtime-diag-<RunId>.jsonl`; absence of console output did not mean absence of file logging.
Repo2 invokes its independent runtime without that redirection, using the `repo-mode-plus2` profile and explicit profile directory. Repo1 uses `repo-mode` and its existing default profile resolution. Do not replace either profile or key based on this difference alone.

Both profiles use the same Direct Desktop Commander entry, shared Guard and quiet MCP notification preload. The preload suppresses `notifications/message`, not runtime console diagnostics. Removing it is not part of this change.

The updated Repo1 launcher removes the runtime output sink and prints `RuntimeLog=`. It explicitly clears the runtime file sink (`--log.file=`) and mirrors stdout/stderr to both Script Catalog and a new UTF-8 diagnostic file, flushing each line. This avoids depending on whether a runtime file sink also emits console events. It retains debug level and disables unsafe raw HTTP logging. A native stderr line can be plain text among JSON events. On runtime exit, its error includes exit code, RunId and log path. This changes observability, not the transport protocol or credentials.

## Evidence and limits (2026-11-15)

The owner screenshot's source inventory matches the pre-change manifest `AEF7D17084F951AEAB6F98CF91E7A39E1D6043A0DAC6BC123DBF99463887B0F9`.
A read-only Docker snapshot showed two Direct Desktop Commander processes and zero cgroup OOM kills or PID-limit hits. Without Windows runtime metadata, the two PIDs cannot be assigned to a profile or a particular MCP session.
Repo2 also experienced transient MCP timeouts during this investigation. This does not establish the cause of Repo1's reported `Session terminated`.
The exact Repo1 failure remains unconfirmed until its Windows runtime events are correlated with a failing call from the account that owns Repo1. Script Catalog's running PID is not an end-to-end MCP health check.

## Owner-local readback before another restart

Existing JSONL can be read now, without an update or restart. Prefer the exact RunId shown in Script Catalog; the following selects the most recently written file. Run in ordinary Windows PowerShell:

```powershell
$dir = Join-Path $env:USERPROFILE 'chatgpt-repo-mode'
$log = Get-ChildItem -LiteralPath $dir -Filter 'runtime-diag-*.jsonl' -File |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $log) { throw 'REPO1_RUNTIME_LOG_NOT_FOUND' }
$log | Select-Object FullName, Length, LastWriteTime
Get-Content -LiteralPath $log.FullName -Tail 120
```

Read these events locally. Do not commit or publish full logs, profiles, keys or payloads. For investigation share only redacted events around the failing call, preserving time, level, component, error code and request/session correlation identifiers. A process exit, MCP-child exit, control-plane timeout and stale remote session need different evidence; do not infer one from the generic client message.

For source delivery use the paired Tunnel/Script Center Windows update runbook linked from [Windows Repo source](../runtime/windows-repo/README.md). Merge Tunnel first, then its matching Script Center resolver. Windows update validates source but does not restart workers. Reconnect only Repo1 after current Guard Preview, keep Repo2 available and test a read-only call from Repo1's owning account. This Docker task does not read Windows logs, update Windows clones, reconnect either tunnel or restart the container.
