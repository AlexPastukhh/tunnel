# G3 — Session 3 API exposure and unattended lifecycle gates (source review, 2026-10-15)

**Роль страницы: датированный source review/evidence, не текущий runbook.** Актуальные критерии и очередь — [план G2](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md), подтверждённое состояние — [CURRENT_STATE](CURRENT_STATE.md). Unattended startup отменён как обязательное условие; safe diagnostic GET не запрещается только по имени /api. Эта правка не добавляет native evidence.

**STATUS: USER-LOCAL OWNER LISTENER INVENTORY AND GUEST HTTP GET REAL TEST COMPLETE; ADMIN GET ROUTE STILL EXPOSED, G3 BLOCKED.** No Windows changes are authorized by this document.

Историческая постановка этого source review требовала unattended startup. Пользователь позднее принял ежедневный ручной вход; текущие условия и scope — в актуальном плане. Фактические наблюдения ниже сохраняют свои даты, более ранние PENDING строки не отменяют последующие actual results.

## Confirmed findings from repository evidence

1. **Owner-local loopback admin API (`127.0.0.1`) was reachable by G2 in the 2026-10-13 snapshot.** `docs/G3_POST_ACL_VERIFICATION_2026-10-13.md` records unauthenticated SID1009 `GET /api/log-level` returned HTTP 200 from owner HOST 8080, Repo 58122 and own G2 65069; `OPTIONS` returned 405 with `Allow: GET, PUT`. *No PUT/POST to owner tunnels was sent.* Source review suggested a write handler but does not prove exploitable access. **These are historical ports and may have changed:** do not assume the service is currently listening or changed state.
2. **GUI boundary evidence:** owner logged on in Windows client Session 2; non-admin SID1009 in separate Session 3, current station `WinSta0` visible=true. These two `WinSta0` objects are session-scoped, not the same window station. Guest's unique `Local\\` mutex and fresh-profile Edge CDP port-file tests passed. There is NO live negative owner-screen/clipboard/window-open verdict.
3. **Existing launcher is not reusable for Session3.** `G2WindowSupervisor.StartUser` uses `CreateProcessWithLogonW` from the owner session; `Attach` enforces `TokenSessionId == owner SessionId`; private window station is created in owner's session. `Start-G2PrivateWindow.ps1` has owner WinSta0/Default DACL hash pins and an ACL-changing `Launch` branch. **Do not run or patch Launch to bypass these gates.**
4. **Runtime profile trade-offs:** repository `docs/G3_LOCAL_API_RUNTIME_2026-10-13.md` reports a side-by-side tunnel-client **runtime-only** flavor v0.0.15 with synthetic isolated MCP and health checks; twenty tested UI/admin/Codex/Harpoon paths returned 404. No live swap of owner HOST/Repo profiles was accepted; changing them requires independent change control, zero loss of existing chats and verified rollback. `--harpoon.additional-transport=` disabled extra transport in that synthetic scope, not all local networking.
5. **G2 environment wrapper is not an OS sandbox.** `runtime/host-g2/g2-stdio-gate.py` explicitly states minimal environment propagation is *not* a hard boundary against other code running under the same SID. Never treat removal of `CONTROL_PLANE_API_KEY` from Node child as proof the arbitrary SID1009 shell cannot reach other G2-owned processes, files or network endpoints.
6. **Routes are independent.** `docs/ARCHITECTURE.md` shows native Windows HOST, Docker Repo, hosted HOST Site and Repo Site are separate authorization routes. A ChatGPT conversation that can invoke both HOST and G2 tools remains a product/tool-routing concern; creating a guest Windows client session by itself does not isolate a whole conversation.
7. **Other open gates:** `docs/G3_POST_ACL_VERIFICATION_2026-10-13.md` reports unproven SMB and service control rights; `G4_ACCESS_POLICY_PROPOSAL_2026-10-13.md` is *DRAFT* and covers separate credentials, file RO/RW/DENY, backups and browser profiles, not currently enforced everywhere.
## Updated actual owner API exposure — 2026-10-15

Guest non-admin SID1009 in Windows Session3 returned `HTTP 200` from `GET /api/log-level` on both owner listener ports `127.0.0.1:52632` and `127.0.0.1:8080`, **without credentials or response body reads**. No PUT/POST tested. The current guest GET gate **fails** for this path despite session GUI separation; no assumptions about other routes or authorization. Source JSON and candidate runtime-only owner migration Preview: `G3_LIVE_OWNER_LISTENERS_2026-10-15.md` and `G3_OWNER_RUNTIME_ONLY_PREVIEW_2026-10-15.md`. The old line 'current state unknown' below was historical staging and is superseded by this new result. Do not change actual owner tunnels until reviewed and explicitly authorized.

## Историческая таблица до уточнения условий

| Path | Status today | Acceptance gate; do not infer from Session 3 alone |
| --- | --- | --- |
| Guest to owner `WinSta0`, input, clipboard | Session boundary promising; no live negative test | Test denied cross-session object access using **synthetic capability/metadata**, never contents of real owner clipboard/screen. Confirm no inherited owner station/desktop/GUI handles; user switching does not disclose owner data. |
| Guest to owner HOST/Repo loopback admin HTTP | Historical GET 200; current state unknown | Inventory actual listeners and exact executables **read-only** under owner at an approved time. Prefer supported runtime-only profiles with absent admin routes; separately test owner health and guest refusal. Authenticated admin endpoint alternative only if runtime-only incompatible. No blanket firewall rule, no owner tunnel restart without approval. |
| Guest to owner named pipes, localhost MCP, debug ports | Unassessed for current listeners | Restrict by Windows identity/DACL **and** authenticated request scope where supported. Any cross-session controller must not proxy arbitrary owner shell/files. No G2 inherited owner key/token. |
| Guest G2 tunnel runtime key/profile | Existing G2 dedicated profile/key and SID guard, password prompted manually | Only dedicated least-privileged G2 identity/key. If unattended needed, evaluate OS-protected per-user credential storage with clear rotation/revoke and non-disclosure. No plaintext key file in shared Public/Repo. Same-SID code can generally access its own credentials: this is a scope boundary, not secrecy from G2. |
| Browser and CLI compatibility | Guest own mutex and Edge CDP startup PASS | Test full CDP DOM/localStorage, Node/Python/Git/PowerShell, workspace RW/RO/DENY, sandbox on, own profile cleanup and child-process job. No owner browser cookies/profiles. |
| Owner service/task/SMB/direct ChatGPT routes | Earlier gates open | Permission matrix and negative tests on safe synthetic targets only. Keep native HOST/Repo unchanged and independent; enforce relevant tool route where possible. |
| Logout/reboot and daily usability | Manual Fast User Switching only | Starting G2 must not require interactive guest desktop switching after each boot. Must fail closed if expected guest token/session absent; bounded restart and supervised cleanup; avoid visible guest windows and owner focus changes. |
## Необязательные startup варианты — не приняты и сейчас не требуются

| Mechanism | Viability evidence | Decision |
| --- | --- | --- |
| Run a task with `TASK_LOGON_INTERACTIVE_TOKEN` | Microsoft: user must already be logged in; task runs in an existing interactive session | **Insufficient after a clean reboot** if FortisHostG1 has not signed in. Can be a cheap experimental supervisor only while guest Session3 is logged in; never claim unattended boot. |
| Run a task via `TASK_LOGON_S4U` | Microsoft: no password stored by the system, but **no network or encrypted file** access | Likely incompatible with a networked MCP tunnel and DPAPI-protected G2 key. Do not choose without controlled native proof; no new task created. |
| Run a task via `TASK_LOGON_PASSWORD` under SID1009, **non-admin** | Microsoft: password supplied at task registration, can support a logon separate from interactive-token prerequisite | **Candidate for source-level feasibility only.** Requires user approval for credential registration/task, owner-only protected task definition, recovery policy; noninteractive station/SessionId and Edge/MCP/network compatibility are unproven. Never assert it generates interactive Session3, enables G2 network, or keeps credentials risk-free. |

Rejected shortcuts: `CreateProcessWithLogonW` from owner Session2 (observed BaseNamedObjects failure); silently bypass current SessionId check; adding SID1009 CREATE to owner BaseNamedObjects; enabling RDP/autologon; SYSTEM/SeTcb user token broker; disabling Kaspersky or Edge sandbox; permanent plaintext guest password/key; launching current owner `-Mode Launch`.

**Key architectural question:** Is there a supported *noninteractive, non-admin SID1009 logon* via the native Task Scheduler that gives the same named-object/Edge functionality while operating independently of an owner GUI and keeping network/control-plane connectivity? The answer is **not in repo evidence**; this needs an explicit, isolated test with user review before task registration. If absent, Session3-only cannot yet meet unattended UX and another design is necessary.
## Исторический listener preview — уже выполнен

Source: `runtime/host-g2/Preview-G3TunnelListeners.ps1`
SHA256: `900196F0B19A83968F00DF91A9180DAB5F668433011799E0ED5DD690F223C0BE`.

It requires **owner SID1001 / nonzero Windows session**. It enumerates process metadata only for `tunnel-client.exe` and `tunnel-client-runtime.exe`, uses `GetOwnerSid` to classify `OWNER/GUEST/OTHER/UNVERIFIED`, and filters **listening TCP socket metadata** by these process PIDs. No process command line, path, environment, key, clipboard, real HTTP request, or network payload is read. No process is started/stopped or system change made. `ProcessCount=0`, `OwnerLookup=FAILED`, or unknown identity must be treated as incomplete, not PASS. Because existing listeners may have changed since 2026-10-13, **do not hardcode historical ports or call admin `PUT`**.

Under **ordinary local owner PowerShell** (not Fortis Windows remote MCP), use only:

```powershell
$p='C:\Users\alexa\Repos\tunnel\runtime\host-g2\Preview-G3TunnelListeners.ps1'
$expected='900196F0B19A83968F00DF91A9180DAB5F668433011799E0ED5DD690F223C0BE'
if((Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash -ne $expected){throw 'G3 listener preview source hash mismatch'}
& ([scriptblock]::Create([Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes($p))))
```

Result is a synthetic JSON with process names, PID/SessionId/owner classification and local address/port only. Do not provide private process command lines or credential values. The read-only listener inventory cannot determine whether an HTTP endpoint requires authentication; route validation remains a separately reviewed step. Static structural/source check PASS; actual Windows PowerShell parser and live owner run PENDING. Stop on Kaspersky warning; do not disable protection.

## Actual owner tunnel listener inventory, 2026-10-15

The user executed the pinned owner-local `Preview-G3TunnelListeners.ps1`: two owner `tunnel-client.exe` processes in Session2 listen on `127.0.0.1:52632` (PID31064) and `127.0.0.1:8080` (PID28376). No tunnel-client under SID1009 observed within this specific process filter; cannot establish absence of other guest processes. Profile mapping HOST vs Repo is unverified. No HTTP requests were made. Source of truth for complete synthetic JSON and an optional later guest-only GET/status-only test is `G3_LIVE_OWNER_LISTENERS_2026-10-15.md`. Historical ports are superseded by this user-local socket snapshot, but may change again. Guest GET currently PENDING; do not treat TCP listening as confirmed guest HTTP access.

## Актуальная следующая работа

[План](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) заменяет прежнюю очередь scheduler/lifecycle исследований.
Ручной ежедневный вход принят. Не повторять уже выполненный listener preview/GET200 по этой странице.
Теоретический Task Scheduler trial не является обязательным следующим шагом.
[Прежний next-work блок](G2_G3_SUPERSEDED_GUIDANCE_2026-10-15.md#lifecycle_next) сохранён как история.

Official references:
- [Microsoft TASK_LOGON_TYPE](https://learn.microsoft.com/en-us/windows/win32/api/taskschd/ne-taskschd-task_logon_type)
- [Microsoft TaskFolder.RegisterTaskDefinition](https://learn.microsoft.com/en-us/windows/win32/taskschd/taskfolder-registertaskdefinition)
- [Microsoft Window Stations](https://learn.microsoft.com/en-us/windows/win32/winstation/window-stations)
- [Microsoft Process Connection to a Window Station](https://learn.microsoft.com/en-us/windows/win32/winstation/process-connection-to-a-window-station)
- [Microsoft Window Station and Desktop Creation](https://learn.microsoft.com/en-us/windows/win32/winstation/window-station-and-desktop-creation)

**Scope:** repo documentation/source review only, no Windows local/remote execution, ACL/network/service/task/AV change, credentials input, commit/push, or HOST/Repo/G2 runtime restart.
