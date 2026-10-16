# G3 — review of runtime-only mitigation (2026-10-15)

**ACTUAL OWNER LOCAL READ-ONLY PREVIEW PASS / ALL THREE LIVE LAUNCHERS BEFORE / PRODUCTION SWITCHOVER NOT AUTHORIZED. G3 BLOCKED.**

## Actual cross-session HTTP failure

Local non-admin SID1009 / Windows Session3 sent two status-only GET requests with no credentials or response body read. Both owner tunnel-client.exe ports returned HTTP 200 on /api/log-level:
- 127.0.0.1:52632 (owner PID 31064).
- 127.0.0.1:8080 (owner PID 28376).

This proves the owner local admin HTTP GET is reachable from the guest session. It does not demonstrate PUT, POST, response contents, or which of the two PIDs maps to HOST vs Repo. Full evidence: G3_LIVE_OWNER_LISTENERS_2026-10-15.md. Never send modifying requests to owner endpoints.

## Actual owner-local Preview — PASS, no mutation

The user ran `switch-launchers.ps1 -Mode Preview` as owner `alexa` after the earlier hash pin had been provided. Native PowerShell returned these three exact `State=BEFORE` entries:

```json
[{"Live":"C:\\Users\\alexa\\Documents\\prot\\Start-Desktop-Commander-Secure-Tunnel.ps1","Candidate":"C:\\Users\\alexa\\Repos\\tunnel\\runtime\\host-g2\\runtime-api-migration\\host-launcher.ps1","State":"BEFORE"},{"Live":"C:\\Users\\alexa\\chatgpt-repo-mode\\run-tunnel.ps1","Candidate":"C:\\Users\\alexa\\Repos\\tunnel\\runtime\\host-g2\\runtime-api-migration\\repo-run-tunnel.ps1","State":"BEFORE"},{"Live":"C:\\Users\\alexa\\chatgpt-repo-mode\\control.ps1","Candidate":"C:\\Users\\alexa\\Repos\\tunnel\\runtime\\host-g2\\runtime-api-migration\\repo-control.ps1","State":"BEFORE"}]
```

PowerShell also printed `Preview only. No files, processes, ACL or profiles changed.`

This confirms the three live **launcher file SHA256s match the BEFORE pins**, all three candidate hashes/plan digest passed the script gates, and the installed runtime-only EXE SHA256 matched the pinned value. It **does not** establish that production HOST/Repo will function with runtime-only; no service was restarted and both owner full-client tunnel processes remain unchanged.

**Important design limitation:** the existing `switch-launchers.ps1 -Mode Apply` is **all-or-nothing across all three launcher files**, and a subsequent restart of either profile would pick up new bytes unexpectedly. It does not restart processes itself, but it is **not** a scoped one-tunnel test. Do NOT invoke `-Mode Apply` or `-Mode Rollback` merely because this Preview was green.

**Decision for next work:** prepare a reviewable **single-route**, hash-and-file-identity-guarded staging/rollback plan first. Prefer an isolated synthetic comparison then one owner route at a time with explicit owner approval, safe backup and post-restart G2 negative HTTP checks. Keep the other owner route untouched, including its launcher and live process. Route mapping PID↔HOST/Repo, independent current health evidence, exact tools required, downtime tolerance and recovery from a failed restart must be confirmed before any live switch. No authorization for live Windows mutations was given by the user by sending this Preview JSON.

## Preferred low-complexity candidate, not yet applied

Previously isolated Windows synthetic tests documented in G3_LOCAL_API_RUNTIME_2026-10-13.md used installed official tunnel-client-runtime.exe (runtime-only v0.0.15) and got MCP calls working, 20 tested admin/UI/Codex/Harpoon endpoint responses 404, health/metrics 200. This is evidence for a *candidate*, not native owner HOST/Repo compatibility or total local API isolation.

The old bundle runtime/host-g2/runtime-api-migration/switch-launchers.ps1 supports explicit Preview/Apply/Rollback; current repository file SHA256 confirmed 0D68581ADD6F0126D1E8A0F6DF993C92D52096F7E13028CA9A79D3F602BC2612. Its migration-plan.json SHA256 confirmed 9EB03A985E71FDC32944DCDD8D327008C989C3091E0A0BB46B90EA4A8A0773D8. The three candidate owner launcher source hashes match their JSON pins. This does **not** prove installed Windows owner launcher or runtime hashes; the script Preview will read them.

### Only approved next action to request: ordinary owner PowerShell, Preview

```powershell
$p='C:\Users\alexa\Repos\tunnel\runtime\host-g2\runtime-api-migration\switch-launchers.ps1'
$expected='0D68581ADD6F0126D1E8A0F6DF993C92D52096F7E13028CA9A79D3F602BC2612'
if((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -ne $expected){throw 'Migration Preview source hash mismatch'}
& $p -Mode Preview
```

The Preview compares pinned candidate/live launcher source and installed runtime bytes. It does not modify files, start or stop tunnels, read key contents, or alter ACL/network/service state. If it fails with DRIFT, missing file or hash mismatch, stop and report only the error. Do NOT run Apply, Rollback, or rebaseline a hash.

## Before a future *explicitly approved* production transition

- Verify profile-to-process ownership and matching G2/HOST/Repo capabilities, owner tool availability, Docker Repo bridge, observatory compatibility and protected key paths. Source-only runtime candidate and a successful Preview are not enough.
- Only with owner approval, prepare narrowly scoped, sequential reversible transitions, preserving established owner chats and backups. Never switch both running owner tunnels together or automatically replace three launchers at once.
- After each *authorized* transition, require owner MCP function/health pass plus guest Session3 unauthenticated GET negative on approved endpoints, without PUT/POST, contents or authentication credentials. Ensure runtime-only does not simply move administration to another route.
- Complete outstanding G3 private owner GUI/clipboard denial, filesystem/SMB/services, cross-plugin route, and unattended guest process lifecycle gates separately.

**Only Fortis Repo documents reviewed/created this turn; no Windows remote shell/fixture, credentials, ACL, Kaspersky policy, service/task, owner tunnel process, Git commit/push touched.**
