# G3 — диагностика отдельных сессий и исторические прототипы

## Текущий статус методов

Каталог содержит исторические diagnostic/private-station prototypes, не current launcher.
E43 принял ordinary guest login и bounded own GUI/clipboard + owner boundary.
Private station условна, старые owner-session Launch/ACL не выполнять по этому README.
[E42](../../../docs/G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md),
[итог](../../../docs/ISOLATION_GUIDE.md).

## Датированная история (сохранена без удаления)

Текущая точка 2026-10-16: [E21–E24 и следующие шаги](../../../docs/G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md). Own guest GUI/clipboard и browser PASS(scope); fresh-open owner boundary и existing-handle/source review частичные. G3 BLOCKED. E23/E24 не требуют полного Native audit без конкретного пути обхода. Разделы ниже сохраняют датированные методы и старые прототипы; их PENDING не отменяет позднейшие scoped результаты.

**Статус каталога: подготовленный diagnostic и датированные прототипы; не принятый guest-session launcher.**

Текущий порядок — [план G2](../../../docs/G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md); выбор session-based Candidate —
[session decision](../../../docs/G3_SESSION_BOUNDARY_OUTCOME_DECISION_2026-10-15.md).
Собственные guest GUI/clipboard разрешены, owner GUI/clipboard защищаются.
Отдельная private station — fallback по потребности, ручной guest login принят.
Не запускать старый owner-session Launch и не применять owner WinSta0/Default ACL по этому README.

### Подготовленный сценарий 15 октября

[Test-G3SessionGuiBoundary.ps1](Test-G3SessionGuiBoundary.ps1) — source-only diagnostic: ordinary owner metadata witness,
затем ordinary guest GUI/clipboard positive, Native self/missing/owner open-close controls и selected owner-process probes.
[Назначение, ограничения, SHA-256, проверенные результаты Repo и точные user-local команды](../../../docs/G3_SESSION_GUI_BOUNDARY_DIAGNOSTIC_2026-10-15.md).
Первый Windows OwnerWitness предыдущего pin скомпилировался и дал metadata, но guard отверг сырое desktop name `\Default`.
В исправленном source — station-bound relative desktop lookup и witness schema 2. Windows OwnerWitness получен
2026-10-15 21:51:41 Asia/Bangkok (SID1001, Session1). GuestProbe остановился на HoldProcess / QUERY_LIMITED_INFORMATION.
В диагностической инструкции подготовлен автономный guest recovery block без прежних переменных; Windows outcome / Native capability controls PENDING.
Подготовка не является GUI/clipboard acceptance или установленным launcher.
Existing final-chain handles и clipboard bridges этим сценарием не проверены.

### Review необходимости метода

[Findings и Candidate Proposal P01](../../../docs/G3_GUI_BOUNDARY_METHOD_REVIEW_2026-10-15.md) сопоставляют Windows guarantees
и remaining local acceptance. Ручной recovery/Native цикл пока на паузе; source pins/evidence сохранены.
Изменения runtime/ACL или новый transport этим review не применены.

### Исторические процедуры 13–14 октября

Далее сохранены проверенные прототипы, последующие попытки и их pins.
Current/live/latest в этих записях означают момент соответствующего среза;
позднее прежний G2 был остановлен, а runtime новой guest session ещё не принят.
[Старое вступление](../../../docs/G2_G3_SUPERSEDED_GUIDANCE_2026-10-15.md#window_readme_prelude) сохранено отдельно.

### Verified
Actual non-admin SID 1009 created an unnamed, noninteractive station with an explicit private DACL.
A fresh PowerShell child was started with lpDesktop=private-station\default, handle inheritance false and a kill-on-close Job.
Node and another ordinary PowerShell descendant stayed in that station.
Own Workspace RW, shared runtime read/mutation DENY, secret-related env names=0 passed.
Installed Edge headless with a fresh profile, own HTTP server and loopback CDP passed a synthetic localStorage/DOM test with the default browser sandbox.
Nine fresh opens of own test station/desktop after deny returned Win32 5. Original test DACLs were restored through retained controller handles, then objects were closed.
No clipboard/screen content was read. No owner station/desktop DACL was changed.
The helper is test infrastructure, not a production isolation launcher or ACL manager.

### Local read-only preflight
Preview-G2WindowBoundary.ps1 only supports Preview. It compiles captured, SHA256-pinned component bytes.
It reads owner WinSta0/default descriptors, builds prospective SID 1009 deny in memory, and checks that owner WRITE_DAC remains allowed.
It inventories G2 processes in the current owner session; fallback queries TOKEN_USER only.
An elevated Preview temporarily enables SeDebugPrivilege for metadata, then disables it. It writes no ACL and stops no process.
Current non-elevated owner MCP cannot identify five processes with system component names; these are reported UNKNOWN, not assumed safe.
Run the pinned Preview from a fresh local PowerShell as alexa, elevated, and return only its JSON.
Do not close G2/HOST/Repo for Preview. No password or runtime key is requested.

### Transition requirements (pending)
Resolve complete privileged inventory; verify all old SID 1009 processes holding WinSta0 handles are gone.
Prepare an owner-controlled private launcher with explicit lpDesktop and no inherited owner station/desktop/console handles.
Credential/key entry must stay local and masked; no new plaintext key file, task or service is authorized by this prototype.
Before a live deny: owner-only original DACL backup, owner-rights forecast and compare-and-swap rollback.
Protect WinSta0 and default desktop from SID 1009 reopen/WRITE_DAC/WRITE_OWNER, not only clipboard; private station alone is insufficient.
Apply for each new owner logon session; user-object ACLs do not persist across session recreation. Retire the interactive G2 entry path in the final design.
Verify actual new G2 token, denied owner object opens, no retained owner handles, native MCP/Edge/workspace/runtime and unchanged owner processes.
Owner local APIs, wider chat tool routes, services/SMB and G4 acceptance remain separate open gates.


### Current staging — 2026-10-13 22:35 Asia/Bangkok

The earlier prototype-only requirements above are now implemented as staged sources; live acceptance remains pending.
[Current evidence, full plan, exact pinned local command and rollback procedure](../../../docs/G3_PRIVATE_LAUNCHER_STAGING_2026-10-13.md).
Start-G2PrivateWindow.ps1 defaults to Preview; Launch/Rollback require fresh elevated owner alexa in Session 1, captured component pins and zero old G2/UNKNOWN inventory.
The user elevated Preview was complete and original owner window ACL hashes still match. Combined compile/AST/captured Preview, synthetic backup/CAS/environment/job and same-account pipe/PID-binding API tests passed.
Masked credentialed StartUser and an admin-owned named station require local preflight: actual SID1009 CLI/Edge selftest happens before main owner ACL writes and runtime-key prompt.
A protected CTools bootstrap plus authenticated named pipe avoids elevated reading/removal of a guest-writable result file. No plaintext key file, service/task or owner runtime restart is introduced.
Owner-only backup and compare-and-swap Apply/Rollback preserve later ACL changes; failure leaves protection if safe rollback cannot be verified.
Current live G2 still uses WinSta0; no clipboard/screen protection is yet accepted. Actual post-launch native MCP/station/owner-handle deny/CLI/Edge/workspace/runtime/UI/owner health acceptance remains required.
This is per-logon-session window isolation; owner APIs/chat routes/services/SMB and retirement of the old interactive launch path remain open. G3 OPEN, G4 NOT ACCEPTED.


### Attach correction — 2026-10-13 23:00 Asia/Bangkok

[Current pins, local retry and evidence](../../../docs/G3_PRIVATE_LAUNCHER_ATTACH_FIX_2026-10-13.md) supersede the 22:35 operator/supervisor SHA pair.
First local credentialed attempt failed in Attach before key prompt/main owner ACL writes. New caller-only SeDebugPrivilege scope captures/restores PreviousState before child Resume; target privileges are unchanged. Native token/job/resume errors name their stage.
Windows combined compile/AST/captured Preview and non-admin missing-privilege fail-closed/restoration test passed. Actual admin-enabled/credentialed branch remains gated by local preflight in a fresh elevated owner console; no private runtime acceptance or live window ACL Apply claimed.


### Query-only validator — 2026-10-13 23:19 Asia/Bangkok

[Current exact pins/evidence/local retry](../../../docs/G3_PRIVATE_LAUNCHER_QUERY_ONLY_2026-10-13.md) supersede 23:00 source pins.
User retry failed precisely Attach/OpenProcessToken with access 10 after caller privilege scope. Access is now TOKEN_QUERY=8; native SID/groups/elevation/type/session checks require no target token duplication/impersonation. Administrators membership including deny-only rejects target. Child identity/session/job/suspended guards remain.
Windows compile/AST/Preview and actual current query-only token tests (SID/primary/session, duplicate DENY, wrong SID/filtered admin membership rejection) PASS. Actual SID1009 token open and credentialed CLI/Edge/private runtime acceptance remain PENDING local before owner ACL Apply. No owner runtime/ACL changes or publication; G3/G4 not accepted.


### Early transport — 2026-10-13 23:43 Asia/Bangkok

[Current operator 0CF2… pins/plan/local retry](../../../docs/G3_PRIVATE_LAUNCHER_PREFLIGHT_TRANSPORT_2026-10-13.md) supersede the 6DD2… operator.
User retry passed query-only Attach/job/resume, then old late pipe timeout. Protected harness now connects first, frames progress/error/result and uses process-only Bypass; native child-exit polling is prompt. Supervisor F619… and IPC/OS grants unchanged.
Same-account Windows Restricted -File block, Bypass result/PID binding, structured stage failure and early exit tests plus captured Preview PASS. Actual credentialed guest pipeline/window gate still pending local; old guest policy inference is not proof. No main ACL/runtime applied/accepted; G3/G4 open.


Дополнение 2026-10-13 23:57 Asia/Bangkok: limited client GW fixture denied connect (exit94), GRGW fixture result/PID binding PASS. Production pipe guest grant changed only GW→GRGW on random diagnostic channel; no key/password data, filesystem/window scope unchanged. Final operator 0CF2… pinned Preview PASS; actual guest transport/runtime/window ACL acceptance pending.


### Detailed verdict — 2026-10-14 00:10 Asia/Bangkok

[Current operator 2CB5…/diagnostic command](../../../docs/G3_PRIVATE_PREFLIGHT_VERDICT_2026-10-14.md). Actual guest final predicate failed after all progress stages. New source only prints synthetic SID/station/exit/Node/Edge/cleanup report before existing checks; no permission expansion or bypass. Exact failure condition pending local report; Supervisor F619… unchanged, main ACL/private runtime not accepted.


### Edge startup diagnostic — 2026-10-14 00:46 Asia/Bangkok

[Current exact pins/evidence/local retry](../../../docs/G3_EDGE_STARTUP_DIAGNOSTIC_2026-10-14.md). User report isolates failure to Edge exit21 before CDP; guest SID1009/private station/CLI descendant/Workspace/runtime protection/cleanup pass in that synthetic scope. New D5ED… operator pins diagnostic Node 4A58…: own fresh-profile Edge stderr max4096, early exit, native profile-lock test and LABEL-only station/desktop plus own token integrity metadata. Default sandbox, Supervisor F619… and all permissions/guards unchanged.
Windows syntax/AST/metadata compile/owner synthetic lock test/pinned Preview PASS; main owner DACL hashes unchanged. Actual G2 diagnosis still requires fresh elevated local owner retry and masked credential, before runtime-key/main ACL stage. Owner HOST/Repo left running. Do not claim exit21 cause, live clipboard protection or accepted private runtime. G3/G4 remain open.


### Private object compatibility — 2026-10-14 01:11 Asia/Bangkok

[Current exact pins/evidence/local launch](../../../docs/G3_PRIVATE_OBJECT_COMPATIBILITY_2026-10-14.md): operator 05B6…, supervisor E63C…, Node BE06… supersede D5ED…/F619…/4A58…. Actual report: ProcessSingleton failure, lock probe0, guest Medium; installed Edge cause still not proven. Staged guest private object masks restored to full 0xf037f/0xf01ff only inside new noninteractive private environment, correcting Chromium desktop-ACL clone compatibility and matching prior successful prototype. Guest can mutate these private object ACLs; main owner deny/CAS/job/identity/session guards and Edge sandbox unchanged.
Windows combined compile/AST/Node/Preview + memory ACL matrix PASS; main DACL hashes unchanged. Node now reports read-only existing startup-mutex open, own random mutex create and own private message-window Win32 errors. Main-station message-window guard tested=-1; no owner GUI/clipboard/screen or existing mutex modification.
Actual local credentialed G2 Edge preflight, main Apply and private runtime acceptance still pending; fresh elevated owner console required. Owner HOST/Repo preserved; no service/task/common runtime restart/publication/commit/push. G3 OPEN/G4 NOT_ACCEPTED.


### Handoff / latest named-mutex blocker — 2026-10-14 01:30 Asia/Bangkok

[Latest actual verdict and continuation](../../../docs/G3_NAMED_MUTEX_BLOCKER_2026-10-14.md). 05B6… / E63C… / BE06… pins still current. Private message window0 and lock0; new own Local mutex5, startup mutex5, Edge21. Full private rights did not resolve blocker; exact namespace/token cause unproved. Main owner DACL still original in fresh Preview, no main Apply or private runtime acceptance. UI hiding already separate/completed; screen/clipboard false fields are no-read, not DENY.
Next: read-only named-object/token diagnosis and bounded demonstrated remedy before credentialed retry; keep owner HOST/Repo. Continue remaining G3 then G4–G6. No source, ACL, runtime, service/task, Docker/Site changes, restart, publication, commit or push for this handoff.
