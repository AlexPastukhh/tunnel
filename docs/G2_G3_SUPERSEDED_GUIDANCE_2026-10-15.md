# G2/G3 — архив прежних указаний, 2026-10-15

**Исторический материал.** Актуальные условия и следующая работа: [план G2](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md);
последнее подтверждённое состояние: [CURRENT_STATE](CURRENT_STATE.md).
Старые CURRENT/NEXT/PENDING, pins и commands внутри блоков ниже относятся к времени записи.
Они не разрешают новые Windows операции и не отменяют позднее принятые условия.
Блоки перенесены из активных страниц при согласовании документации; их текст сохранён.
Raw JSON evidence и executable source этой документационной работой не менялись.

## CURRENT_STATE

CURRENT_STATE

````markdown
**2026-10-15 — уточнены границы разрешений и достаточность тестов:** [G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) явно разрешает собственные guest GUI/clipboard, процессы, рабочий browser profile, credentials и нужную сеть; защищается основная сессия alexa и её protected data/control. Новый supervisor/Job/broker, полный повтор HTTP route×method матрицы и успех конкретного SMB diagnostic API не являются самостоятельными gates. Контролируемый тест конечной chain отделён от production acceptance; уже доказанное сохраняется. Новых Windows тестов/изменений runtime/ACL/сети при уточнении нет; G3 BLOCKED. Уточнение API gate: исторический guest GET200 сохраняется как reachability evidence и FAIL прежнего blanket admin-GET-DENY теста; итоговая цель — защита опасных owner функций/чувствительных данных. Безопасный GET может быть разрешён при доказанном составе и соответствии версии, без live body/write проб.

**2026-10-15 — план перепроверен по подпунктам:** [G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) теперь содержит статусы DONE/PASS(scope)/PARTIAL/FAIL/PENDING, evidence E01–E17 и только оставшуюся работу. Прежние восемь пунктов не являются восемью непроверенными задачами: runtime installation/fixtures, старый native G2 MCP, file/runtime ACL, часть service/task/IPC прав и stop/restore уже доказаны в своих scopes. Незакрытый остаток отделён от regression новой guest session. Windows проверки и runtime changes при пересмотре не выполнялись; G3 BLOCKED.

**2026-10-15 — следующий Candidate Plan и принятое удобство:** [G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) связывает каждый шаг с угрозой, необходимостью, критериями и затратами. Пользователь явно допускает ежедневный ручной guest login/start/switch-back; фактическая длительность не измерена. Прежнее обязательное требование cold-boot запуска без входа заменено этим решением. Security gates сохраняются; G3 BLOCKED. Изменена документация, Windows/runtime/ACL не менялись.

**2026-10-15 — source-only owner HTTP API review:** [G3_OWNER_HTTP_API_SOURCE_REVIEW_2026-10-15.md](G3_OWNER_HTTP_API_SOURCE_REVIEW_2026-10-15.md) сопоставляет реальные admin routes, loopback/CSRF guards и config/wiring на commit a390c168ff1b2d14e73a95991c186c6aba3ff5a0. Штатного full-client local-admin-only disable/auth flag в просмотренном коде не найдено; --admin-key относится к удалённому control plane. Health details/metrics требуют отдельной оценки; runtime-only — Candidate для isolated compatibility, не одобренный owner rollout. Новых Windows проверок, live HTTP вызовов, restart, ACL/network/task изменений, commit/push/deployment нет. G3 BLOCKED.

**2026-10-15 ACTUAL owner migration Preview PASS (no changes):** user ran pinned `switch-launchers.ps1 -Mode Preview`, SHA256 `0D68581ADD6F0126D1E8A0F6DF993C92D52096F7E13028CA9A79D3F602BC2612`; all three live launcher paths (`HOST`, `Repo run-tunnel`, `Repo control`) returned `State=BEFORE`, with `Preview only. No files, processes, ACL or profiles changed.` This validates expected live file hashes, candidate pins and installed runtime SHA at preview time; **not** production compatibility or a mitigation of the actual SID1009 Session3 cross-session admin GET 200. Old `-Mode Apply` replaces all three launcher files, so **do not use for single-route rollout**. Next source-only design is precise one-route backup/change/revert with independent approval and owner routing check; live HOST/Repo remain unchanged. Details: `G3_OWNER_RUNTIME_ONLY_PREVIEW_2026-10-15.md`. G3 BLOCKED.

**2026-10-15 ACTUAL guest Session3 owner-local admin GET exposure CONFIRMED:** non-admin SID1009 sent status-only GET `/api/log-level` with no credentials and read no body; both OWNER SID1001 Session2 tunnel-client listeners `127.0.0.1:52632` (PID31064) and `127.0.0.1:8080` (PID28376) returned HTTP 200. This is G3 FAIL for admin-route isolation on that path; does NOT prove admin PUT/write or identify which PID is HOST vs Repo. No mutating methods will be attempted. Details `G3_LIVE_OWNER_LISTENERS_2026-10-15.md`. Candidate simpler remedy: tested-in-synthetic official `tunnel-client-runtime.exe` with absent admin routes; **not applied** to live HOST/Repo. Existing pinned `switch-launchers.ps1` SHA256 `0D68581ADD6F0126D1E8A0F6DF993C92D52096F7E13028CA9A79D3F602BC2612` and three migration candidate source hashes pass repo static validation. Owner-only read-only `-Mode Preview` staged in `G3_OWNER_RUNTIME_ONLY_PREVIEW_2026-10-15.md`; Windows preview still PENDING. Never run `Apply`, restart HOST/Repo or change launchers/ACL/AV without owner approval. G3 BLOCKED.

**2026-10-15 owner-local tunnel listener inventory ACTUAL PASS:** user ran pinned `Preview-G3TunnelListeners.ps1` SHA256 `900196F0B19A83968F00DF91A9180DAB5F668433011799E0ED5DD690F223C0BE`; snapshot UTC 2026-10-14T20:04:59.9309689Z: `tunnel-client.exe` PID 31064 OWNER SID1001 Session2 listening `127.0.0.1:52632`, and PID 28376 OWNER SID1001 Session2 listening `127.0.0.1:8080`. No SID1009 tunnel-client process observed within that specific name-filtered inventory, not proof no guest processes of other kinds. Which PID maps to HOST versus Repo is still UNVERIFIED. No HTTP requests or writes. Next proposed guest-only nonadmin SID1009 Session3 **GET /api/log-level response-code-only** on exactly those two current ports, no authorization/default credentials/response body/redirects, staged in `G3_LIVE_OWNER_LISTENERS_2026-10-15.md`; guest run PENDING. Prior 2026-10-13 guest GET HTTP200 remains historical only. G3 BLOCKED; no Windows changes.

**2026-10-15 G3 source-level owner API/lifecycle gate:** `G3_SESSION3_API_LIFECYCLE_GATES_2026-10-15.md` audited actual repo source and prior local API evidence. In a 2026-10-13 snapshot, non-admin SID1009 got unauthenticated HTTP 200 from HOST/Repo/G2 `GET /api/log-level` and OPTIONS advertised GET/PUT, **but no modifying API call was made**; actual 2026-10-15 listener/runtime state UNVERIFIED. Separate Windows Session3 only protects session-bound GUI objects, **not** localhost admin endpoints, file ACL, IPC or cross-plugin owner access. Unattended startup requires a separate feasibility review: Task Scheduler INTERACTIVE_TOKEN needs existing guest login, S4U lacks network/encrypted-files access, PASSWORD registration requires credential review and guest noninteractive Edge/MCP compatibility testing. **Read-only owner-local listener inventory staged**, `runtime/host-g2/Preview-G3TunnelListeners.ps1` SHA256 `900196F0B19A83968F00DF91A9180DAB5F668433011799E0ED5DD690F223C0BE`; static audit PASS, Windows run PENDING. No Windows mutation/task/service/restart. G3 BLOCKED.

**2026-10-15 outcome-based G3 architecture preference (user):** prioritize proved requirements + reliable/easy daily operation over a separately named private Window Station as an implementation detail. **Conditionally prefer dedicated non-admin SID1009 Windows client session** as owner-GUI/clipboard OS boundary, subject to actual synthetic negative capability checks and a startup/recovery design that does **not** need manual daily Fast User Switching or stored plaintext password. Passing Session3 mutex, Edge CDP startup and station metadata is **not** G3 acceptance. No launch/service/task/ACL/user/session changes authorized by this design statement. All route/IPC/owner API/filesystem/CDP and production operations gates remain. Details and requirement matrix in `G3_SESSION_BOUNDARY_OUTCOME_DECISION_2026-10-15.md`.

**2026-10-15 actual guest Session 3 station enumeration PASS:** user ran pinned local metadata `Inspect-G3GuestStations.ps1` SHA256 `941FED61BEB08A9370AEDFF8D4E05511AC4A896B9BCAD293312F2C7792BEB4E4` as non-admin SID1009 Session3. Returned current `WinSta0`, `CurrentStationVisible=true`, `EnumerationAllowed=true`, Win32=0, names `WinSta0` and `Service-0x0-218d7932$`, no ACL writes/desktop reads/owner-session touches. Windows Session3 `WinSta0` is **distinct** from owner Session2 `WinSta0`; enumerated Service-like name has unproven identity, ownership, DACL and is **not** approved for G2. New distinct private station create still failed Win32 183 with CWF_CREATE_ONLY. Next review: assess keeping G2 in dedicated guest Session3 as an OS GUI boundary **versus** original separate noninteractive station requirement; do not silently relax the user-accepted G3 criterion. Document `G3_SESSION3_STATIONS_READONLY_2026-10-15.md`. G3 BLOCKED, no Windows ACL/service/AV/runtime changes.

**2026-10-15 Actual guest private station CWF_CREATE_ONLY result:** pinned revised `Test-G3GuestPrivateStation.ps1` SHA256 `9F82E0E35D47CE32411AB52139DCDF4C41AFBB42F549562539955C916DC843F6` was locally executed as non-admin SID1009 / Windows Session3 and returned `Create private window station failed (Win32 183)` (`ERROR_ALREADY_EXISTS`). For `CreateWindowStation(null, CWF_CREATE_ONLY=1, ...)`, Windows derives the station name from the **logon session** and refuses creation when it already exists (Microsoft docs). This is **not** Win32 5 / namespace mutex denial; do not unset create-only or treat the preexisting station as isolated. No station/desktop was created in this attempt. Next guest-local READ-ONLY metadata source `Inspect-G3GuestStations.ps1` SHA256 `941FED61BEB08A9370AEDFF8D4E05511AC4A896B9BCAD293312F2C7792BEB4E4` static audit PASS, actual guest run PENDING. Runbook `G3_GUEST_STATION_EXISTING_OBJECT_2026-10-15.md`. No owner ACL changes, no persistent G2 runtime; G3 BLOCKED.

**2026-10-15 G3 private-station correction after actual guest failure:** user-local non-admin SID1009/Session3 test reached `CreateWindowStation` but explicit name `FortisG3-{GUID}` was rejected (outer PowerShell error did not include Win32 code). Microsoft `CreateWindowStationW` documentation allows only Administrators to specify station names. **Corrected source-only** `Test-G3GuestPrivateStation.ps1` to `CreateWindowStation(null, CWF_CREATE_ONLY=1,...)` so the system derives the name and existing stations cannot be reused; error reporting now includes Win32 number. SHA256 `9F82E0E35D47CE32411AB52139DCDF4C41AFBB42F549562539955C916DC843F6`, old `717D...` source superseded; local copy uses `FortisG3Station-9F82E0E3.ps1`. Static guards PASS, Windows native re-test PENDING. No Windows remote commands, ACL writes, service/AV changes or G2 runtime. Details: `G3_GUEST_PRIVATE_STATION_SMOKE_2026-10-15.md`.

**2026-10-15 actual SID1009 Session 3 Edge startup/CDP PASS:** user-provided guest JSON had `EdgeStartup=true`, `JobStopped=true`, `ProfileRemoved=true`, `Result=PASS`, non-admin SID1009/Session3, test Job assigned, Edge was alive before job cleanup. This supersedes prior staged-only status for `Test-G3GuestSessionEdge.ps1` SHA256 `2A9B2FF45E234E69F7461F8C00421DED0C34BA19C420C17739641CC42B933527`. Own `about:blank` CDP port file only; no DOM/CDP protocol, owner GUI denial, private station or runtime acceptance. **Next source-only gate staged:** `Test-G3GuestPrivateStation.ps1` SHA256 `717D0F1105B80795859204656CD4BC6D6C6B8945B1175EFE5B97ADB1B24162E6`, user-local nonadmin SID1009 Session3 creating and closing own named noninteractive station + desktop; Windows execution PENDING. See `G3_GUEST_PRIVATE_STATION_SMOKE_2026-10-15.md`. G3 BLOCKED.

**2026-10-15 G3 guest Session 3 Edge smoke test STAGED, NOT RUN:** `runtime/host-g2/window-isolation/Test-G3GuestSessionEdge.ps1` SHA256 `2A9B2FF45E234E69F7461F8C00421DED0C34BA19C420C17739641CC42B933527`. Fail-closed SID1009/Session3/non-admin; Edge suspended then attached to kill-on-close job, headless own `about:blank` / new guest temp profile, loopback ephemeral CDP, 20s timeout, no owner ACL/clipboard/screen/Edge profile access. Static source audit PASS, actual Windows compile and guest execution PENDING. Manual owner-to-Public script copy with hash, then local guest hash/run; abort on Kaspersky alerts. Details `G3_GUEST_EDGE_SESSION3_SMOKE_2026-10-15.md`; G3 BLOCKED.

**G3 next gate staged (2026-10-15):** guest SID1009 / Session 3 interactive Edge `--headless=new --dump-dom` synthetic data: URI, fresh guest scratch profile, default sandbox, 25s wait, taskkill only own spawned Edge process tree on timeout, guest-only profile cleanup and JSON result. Source `runtime/host-g2/window-isolation/Test-G3GuestEdgeSession3.ps1`, SHA256 `1DD2FAD0175C9AB23A85577ED80B2954F736C0700306BD76F75BCD73C4B15136`; design `docs/G3_GUEST_SESSION_EDGE_SMOKE_2026-10-15.md`. **Not yet executed on Windows.** User must paste full script into guest non-admin Session 3; owner repo path may not be guest-readable. No changes to OS/ACL/AV/HOST/Repo or old Session 2 launcher, no CDP/private station/runtime acceptance yet.

**Actual guest Session 3 named mutex PASS (2026-10-15):** locally under non-admin SID1009, a new unique `Local\\FortisG3GuestCheck-{GUID}` mutex was created successfully (`NamedMutexCreated=true`; reported no ACL writes/owner-object access), unlike SID1009 in owner's Session 2. An afterward standalone `finally {...}` paste produced a PowerShell parsing error; it does not invalidate the mutex result, but cleanup should be confirmed with a local `$mutex.Dispose()` or closing that console. This does not validate Edge, private station, IPC or G2 runtime. Details: `G3_GUEST_SESSION_MUTEX_TEST_2026-10-15.md`.

**2026-10-15 manual Fast User Switching evidence:** owner `quser` now lists `alexa` active Session 2 and `fortishostg1` disconnected Session 3. This confirms a separate guest client session without terminating owner session. The next bounded local test, documented in `G3_GUEST_SESSION_MUTEX_TEST_2026-10-15.md`, is under non-admin SID1009 *in Session 3*, creating a single uniquely named guest `Local\` mutex and immediately closing its handle. Result PENDING; owner-session DACL and present owner-created launcher stay unchanged; no session-switch automation/owner-object grants.

**G3 separate-session inventory result:** user ran read-only `quser.exe` in ordinary owner session. It showed only `alexa`, `console`, Session `2` Active (14.10.2026 15:04 login); no guest FortisHostG1 session observed. The next potential live step, **only after user approval**, is manual Windows Fast User Switching to FortisHostG1 and back, keeping owner logged in. No Windows switch, login, token setup, ACL, service, task, browser test or runtime operation performed by assistant. See `G3_SEPARATE_SESSION_FEASIBILITY_2026-10-14.md`.

**Next G3 decision (2026-10-14, source-reviewed design only):** `CreateProcessWithLogonW` in existing launcher creates SID1009 in the owner's Windows client Session 2; `Attach` requires matching SessionId. Private Window Station is not an independent Terminal Services session or `Local\\` object namespace. Design comparison and security gates are saved in [G3_SEPARATE_SESSION_FEASIBILITY_2026-10-14.md](G3_SEPARATE_SESSION_FEASIBILITY_2026-10-14.md). Next **read-only** step: owner-local `quser.exe` inventory to see whether SID1009 has a genuinely separate session. No session/service/task/ACL created; G3 remains BLOCKED.

**2026-10-14 22:35 Asia/Bangkok — confirmed native owner DACL audit:** SID1001 elevated Session 2 read `\Sessions\2\BaseNamedObjects` DACL with `NtQueryStatus=0`, zero ACL writes. Its ACEs grant owner/SYSTEM/current owner-logon SID directory create access, but neither direct guest SID1009 nor Everyone gets `DIRECTORY_CREATE_OBJECT=0x4` / `READ_CONTROL`; actual SID1009 guest previously returned `STATUS_ACCESS_DENIED` to both. No global/shared namespace rights extended. Preferred next design study: isolated guest Windows session; no native tests or launch authorized yet. See `G3_NAMED_MUTEX_BLOCKER_2026-10-14.md`.

**2026-10-14 22:10 Asia/Bangkok actual SID1009 Namespace:** Session 2 guest returned `0xC0000022` for both DIRECTORY_CREATE_OBJECT and READ_CONTROL on `\\Sessions\\2\\BaseNamedObjects`; SID1009 nonadmin/private station/descendant match; Node/child exit 0. This is positive diagnostic evidence of an access block, not successful guest namespace access. Staged owner-only metadata script `runtime/host-g2/window-isolation/Inspect-G2SessionNamespace.ps1` pin `029687DFEF5C02959D39FA5F07CBBB89DFE51F6C867FFF8A8363B54DE8C55E08` reads current-session BaseNamedObjects DACL via NtQuerySecurityObject with no writes/credentials/guest/Edge/mutex; static source safety check PASS, native Windows execution PENDING. Do not approve broad session ACL grant or Launch. See `G3_NAMED_MUTEX_BLOCKER_2026-10-14.md`.

**2026-10-14 22:05:57 Asia/Bangkok (actual user elevated Preview after reboot):** owner logon session=2; new original station hash `93B35141041AE5B136C01445B2690B28D60BC7D5399F0624354D35636761F215`, desktop hash `EE050A0084220C8D222FA1B1FAA056F567CC3044A681561301E700305F77752C`; G2/UNKNOWN process list empty; Owner WRITE_DAC ALLOW/ALLOW; ACL writes 0, Applied false. Session SID changes account for observed SDDL differences from Session 1; no new Launch baseline approved. Namespace-mode guest test remains pending. Detail: `G3_NAMED_MUTEX_BLOCKER_2026-10-14.md`.

**2026-10-14, after user reboot:** user received `Owner ACL changed; obtain a fresh reviewed Preview before Launch` while attempting `-Mode Namespace`. The launcher had an unconditional historical ACL hash gate before its diagnostic early return; repaired so historical `approved` hashes are checked **only** for `-Mode Launch`. `Preview` continues to compute metadata and `Namespace` does not apply window ACL or start permanent G2. Original Launch approval hashes were NOT updated, bypassed for Launch or assumed to be safe after reboot. New operator SHA256 `FBF238E84E31C426938D2619B497A9F5D8C27341982CD27FFCE00D92EA85DB8F`, Node unchanged `8B2C8FB84EA94F7226BE4A43F28E6483720F2C7F7A26866C20624DBBC6DAE2D1`. Repo Node syntax and static branch/pin checks passed; Windows AST / post-reboot elevated Preview / SID1009 Namespace **PENDING**. Stop on any Kaspersky detection; no exceptions/owner ACL writes. Detailed evidence: `G3_NAMED_MUTEX_BLOCKER_2026-10-14.md`.

**Newest staged G3 test, 2026-10-14:** `-Mode Namespace` in operator `FC61301317568A77CCAEB7F2510AF93336276F8DFED1B71E18C7A5464CDB6616`, Node `8B2C8FB84EA94F7226BE4A43F28E6483720F2C7F7A26866C20624DBBC6DAE2D1`. This runs local authenticated SID1009 *read-only* `NtOpenDirectoryObject` for session `BaseNamedObjects` (create right 4 / READ_CONTROL), with no mutex/Edge invocation in this branch, no runtime key, no main window ACL writes and private child/job cleanup. Repo static syntax/branch/pin tests PASS; actual Windows/guest result PENDING. Kaspersky exceptions not added; avoid remote Windows diagnostic shell. See `G3_NAMED_MUTEX_BLOCKER_2026-10-14.md`.

**2026-10-14 02:21 SID1009 result:** unnamed mutex PASS(0), unique unprefixed and unique `Local\\` mutex DENY(5); Edge exit21 ProcessSingleton. Owner session object-directory control open PASS, but guest directory check not yet run. Latest read-only guest directory NTSTATUS probe staged in Node `7B67C2865559946A9428E6C0DC8E71207ACB0C9438BA754323C892C51DD78A43` and operator `3346B6FA450F5E6BFB60A0FBB92FD53E82EB5FFB44C5FAF63FBB4BF9E52FC900`. Node syntax and Windows operator AST pass; independent C# compile attempt blocked by tool (`spawn EPERM`), do not claim guest execution. No ACL, key or runtime changes. Details in `G3_NAMED_MUTEX_BLOCKER_2026-10-14.md`.

**2026-10-14 newest staged diagnostics:** operator `AE94E0F59527192D2B84DBEC18C8953A3C594BC163CE7B3A99A5DA695FC176F8` now offers separate elevated `-Mode Diagnose`: local Windows credential, SID1009 preflight, synthetic result and cleanup only. It returns before runtime-key prompt, owner ACL backup/apply and permanent runtime. Node pin `A512DC3B631E938C215134A9DA3A4CAD7B88B0E4A77028BD2A768AEF4DD0AC9C`. AST/Node syntax pass; post-change Preview execution blocked; actual credentialed Diagnose remains untested. Older operator SHA 9068 and 05B6 superseded. Details in `G3_NAMED_MUTEX_BLOCKER_2026-10-14.md`.

**2026-10-14 current G3 operator stage:** newly pinned diagnostic operator `9068A613987AD32B0A49EB126FFD33C521CBC26F0B2607CCC19BB201CB694D50` includes unnamed/unprefixed/Local mutex checks in Node `A512DC3B631E938C215134A9DA3A4CAD7B88B0E4A77028BD2A768AEF4DD0AC9C`. Windows AST and read-only Preview pass; live SID1009/Edge not retested. Prior 05B6 operator is superseded; do not use its hash for new diagnostic. See `G3_NAMED_MUTEX_BLOCKER_2026-10-14.md`.

**2026-10-14, staged diagnosis only:** `private-station-node-probe.js` has new unnamed/unprefixed unique mutex probes; Node syntax PASS via Repo. No SID1009 execution or updated launcher pins; live G3 state unchanged. See `G3_NAMED_MUTEX_BLOCKER_2026-10-14.md`.

**Только исторически проверенные факты, не live-dashboard и не конфигурация.** Куда обратиться по задаче — [навигация](README.md); модель маршрутов — [ARCHITECTURE](ARCHITECTURE.md); аудит и будущая блокировка — [AUDIT](AUDIT.md).

## G3 — Local named mutex blocker, срез 2026-10-14 01:30 Asia/Bangkok

Latest actual guest report (01:18): profileLockWin32=0, messageWindowWin32=0, own unique Local mutex create=5, startup mutex open=5; Edge exit21/ProcessSingleton. Private full-rights change did not fix failure. Guest/private station/CLI/workspace/runtime guards/cleanup pass in this scope. Exact namespace/token cause remains unproved.
Fresh owner read-only Preview at 01:30 confirms WinSta0/default original DACL hashes, Applied=false/AclWrites=0. Main clipboard/screen deny and private runtime acceptance remain pending. UI cards already hidden separately; false clipboardRead/screenRead is no read, not access DENY.
[Current pins, exact report and continuation](G3_NAMED_MUTEX_BLOCKER_2026-10-14.md). Next is read-only Local named-object/token diagnosis, not another unchanged Launch or broad ACL expansion. Preserve owner HOST/Repo; G3 OPEN, G4–G6 not accepted.

## G3 — private object compatibility, срез 2026-10-14 01:11 Asia/Bangkok

User diagnostic isolates installed Edge exit21 to ProcessSingleton; fresh-profile native lock test=0, guest Medium and no explicit High label. CLI/workspace/runtime/private station/cleanup still pass. Exact internal Edge cause not established.
Confirmed compatibility omission: staged guest private ACL lacked WRITE_DAC/WRITE_OWNER needed when Chromium clones desktop ACL for sandbox. Restored SID1009 full access only to new private station/default, matching prior successful prototype. Main owner deny/pins/guards and default Edge sandbox unchanged. Added own native mutex/message-only-window diagnostics; no owner UI or existing mutex modification.
Windows compile/AST/Node/Preview and memory ACL matrix PASS (old Chromium request DENY/new ALLOW, main deny still DENY); owner main DACL hashes unchanged. Owner-only tests are not actual G2 acceptance; main Apply/private runtime still pending local.
[Current 05B6… operator / E63C… supervisor / BE06… Node pins and local launch](G3_PRIVATE_OBJECT_COMPATIBILITY_2026-10-14.md). Fresh elevated owner PowerShell, password/key masked locally; owner HOST/Repo left running. G3 OPEN/G4 NOT_ACCEPTED.

## G3 — Edge startup isolated, срез 2026-10-14 00:46 Asia/Bangkok

Actual SID1009 report confirms private named station, non-admin/invisible child, CLI descendant station match, Workspace RW, runtime read/mutation deny and cleanup. Only installed headless Edge fails: exit21 before CDP, stderr322 bytes discarded. Cause not established; main owner window ACL stage not reached, private runtime not accepted.
New diagnostic Node saves own fresh-profile Edge stderr (max4096), reports native profile lock-file test and own integrity/station/desktop LABEL metadata; detects early exit. Sandbox, Supervisor and permissions unchanged. Windows syntax/AST/metadata compile/synthetic lock test/pinned Preview PASS; original main DACL hashes unchanged. Owner-only tests do not substitute actual G2 measurements; non-elevated inventory UNKNOWN remains expected.
[Current D5ED… operator / 4A58… Node pins and local retry](G3_EDGE_STARTUP_DIAGNOSTIC_2026-10-14.md). Fresh elevated owner PowerShell required; owner HOST/Repo remain running. Await exact Edge stderr, then targeted fix and private runtime acceptance. G3 OPEN/G4 NOT_ACCEPTED.

## G3 — detailed preflight verdict, срез 2026-10-14 00:10 Asia/Bangkok

Actual guest progress Connected → WindowMetadata → NodeCliEdge now reached, but final predicate failed. Prior 0CF2… operator hid report; exact failed field remains unknown. New diagnostic-only 2CB5… operator prints expected/actual SID/station, admin/visible, child/Node exit and synthetic Node/Edge/cleanup fields before unchanged predicate. Supervisor/permissions/guards unchanged.
Windows pinned compile/AST/Preview PASS; owner station/default hashes unchanged, ACL writes=0. [Current diagnostic command/evidence](G3_PRIVATE_PREFLIGHT_VERDICT_2026-10-14.md). Fresh elevated local owner console needed for report; no key/main ACL stage reached, actual private runtime not accepted. G3 OPEN/G4 NOT_ACCEPTED.

## G3 — early preflight transport, срез 2026-10-13 23:43 Asia/Bangkok

User retry 6DD2… passed Attach/token/job/Resume and hit late pipe timeout before key/main ACL writes. Test powershell now uses process-only Bypass; early PID-bound progress/error channel and native child-exit polling replace opaque late-result wait. No persistent policy or OS scope changes; Supervisor F619… unchanged.
Windows compile/AST/pinned Preview and same-account Restricted/BYPASS success/structured error/early exit fixtures PASS. Exact G2 old policy/startup failure not conclusively known; actual guest CLI/Edge/station/transport pending local retry. Owner station/default hashes unchanged; HOST 5580 / Repo 23904 CreationDate and health/ready 200/200 preserved.
[Current operator 0CF2… pins, evidence/local retry](G3_PRIVATE_LAUNCHER_PREFLIGHT_TRANSPORT_2026-10-13.md). Fresh elevated owner PowerShell only; owner HOST/Repo left. Main window ACL/runtime acceptance still pending; G3 OPEN, G4 NOT_ACCEPTED.

## G3 — query-only token verification, срез 2026-10-13 23:19 Asia/Bangkok

Retry после SeDebug fix отказал именно Attach/OpenProcessToken (Win32 5), при requested TOKEN_QUERY|TOKEN_DUPLICATE. Key prompt и main window ACL Apply не достигнуты. Validator теперь запрашивает TOKEN_QUERY only, native SID/groups/elevation/primary/session before Resume; target duplication/WindowsPrincipal removed. Administrators membership, включая deny-only, отклоняется; G2 non-admin boundary сохранена/усилена.
Windows compile/AST/pinned Preview и actual current-token query-only SID/primary/session, duplicate DENY, wrong SID and filtered admin membership rejection PASS. Owner window hashes unchanged; HOST 5580 / Repo 23904 CreationDate and health/ready 200/200 preserved.
[Current pins, evidence и exact local retry](G3_PRIVATE_LAUNCHER_QUERY_ONLY_2026-10-13.md): fresh elevated owner PowerShell. Actual SID1009 token open/credentialed preflight/private runtime и live window gate ещё PENDING local. Operator 6DD2… / supervisor F619… заменяют исторические 3A30…/1A7D… pins. G3 OPEN, G4 NOT_ACCEPTED.

## G3 — Attach privilege correction, срез 2026-10-13 23:00 Asia/Bangkok

Local credentialed preflight failed Win32 5 at Attach after process creation; key prompt/main window ACL Apply not reached. Missing caller SeDebugPrivilege scope for cross-account token inspection fixed; previous state restored before child resume, G2 remains non-admin and existing identity/session/job/handle guards preserved. Native errors now name exact stages.
New source/component pins, Windows compile/AST/captured Preview and non-admin ABSENT→1300→ABSENT scope test PASS. Admin enabled branch / credentialed retry remain local PENDING. Owner station/desktop hashes unchanged, WRITE_DAC forecast ALLOW; HOST 5580 / Repo 23904 CreationDate and health/ready 200/200 preserved.
[New pins and local retry command](G3_PRIVATE_LAUNCHER_ATTACH_FIX_2026-10-13.md). Previous 22:35 operator/supervisor pins are superseded; fresh elevated owner PowerShell required because old C# type was already loaded. No live window ACL applied/restart/publication. G3 OPEN, G4 NOT_ACCEPTED.

## G3 — private launcher staged, срез 2026-10-13 22:35 Asia/Bangkok

**STAGED_TESTED / LIVE_NOT_APPLIED; G3 OPEN, G4 не принят.** Пользовательский elevated Preview дал полный inventory (UNKNOWN=0), owner WRITE_DAC before/after ALLOW. Новый owner-controlled private launcher с captured SHA pins, local masked credentials/key, protected bootstrap, PID-bound pipe, owner-only backup и CAS rollback подготовлен; compile/AST/Preview и synthetic CAS/env/job/pipe PASS.
Credentialed admin-created named station и StartUser ещё не запущены: их локальный CLI/Edge selftest идёт до owner ACL writes. Current G2 28148 остаётся на WinSta0. В 22:35 owner window ACL original hashes неизменны, HOST 5580 / Repo 23904 / G2 28148 сохранили CreationDate и health/ready 200/200.
[Evidence, полный текущий план и точная локальная команда](G3_PRIVATE_LAUNCHER_STAGING_2026-10-13.md). Следующий шаг: закрыть только старое G2 окно; fresh elevated owner запускает pinned script, локально вводит Windows password FortisHostG1 и separate G2 key. Затем actual private runtime acceptance. Owner APIs/chat routes/services/SMB и retirement interactive entry остаются open gates. Предыдущие «launcher не реализован / elevated Preview pending» ниже — исторические точки, заменённые этой staging записью; live protection пока не принята.

## G3 — window isolation prototype, срез 2026-10-13 21:13 Asia/Bangkok

**SYNTHETIC PASS / LIVE NOT APPLIED; G3 OPEN, G4 не принят.** Actual non-admin G2 проверил private noninteractive station: fresh PS child / Node / ordinary PS descendant сохраняют station; Workspace RW и runtime mutation DENY. Installed Edge headless + own temporary profile/HTTP/CDP/localStorage/DOM PASS со стандартным sandbox; cleanup PASS. Nine fresh opens после synthetic station/desktop deny — Win32 5; prospective owner DACL actual G2 AccessCheck — DENY, owner WRITE_DAC сохраняется.
Owner WinSta0/default SDDL не изменились; HOST 5580, Repo 23904, G2 28148 сохранили CreationDate и health/ready 200. Действующий G2 всё ещё на WinSta0: live clipboard/screen gate не закрыт. Owner-controlled private runtime launcher и live backup/CAS rollback ещё не реализованы/не приняты.
[Прототип / evidence / локальный следующий шаг](G3_WINDOW_ISOLATION_PROTOTYPE_2026-10-13.md). Проверенный Preview-only скрипт подготовлен; non-elevated owner inventory оставляет пять process owners UNKNOWN. Требуется fresh local elevated owner Preview (без закрытия G2 и без ключей), затем безопасный G2-only переход. Owner APIs/chat routes/services/SMB остаются открытыми gates.

## G3 — baseline и совместимость, срез 2026-10-13 20:18 Asia/Bangkok

G2 file guard применён: Workspace RW + три существующих OS-protected runtime дерева C:\Tools\tunnel-client, C:\Tools\desktop-commander-runtime, C:\Tools\desktop-commander (effective RO через Windows ACL). Actual guard readback, Workspace write/readback, public LICENSE read и synthetic outside-guard DENY PASS. Новых project/owner ACL grants, command/network blocks и рестартов нет.
История: 1 847 сохранённых owner Tunnel calls за 11–13 октября, анализ без экспорта raw args/output. Windows CLI/диагностика и установленный Edge headless с новым временным профилем сохраняются; synthetic Edge/localStorage/DOM PASS. Обычная разработка остаётся Fortis Repo, Windows project scope открывать адресно для конкретной задачи.
**G3 OPEN: G2 и owner используют Session 1 / WinSta0; actual G2 AccessCheck разрешает clipboard, screen и WRITE_DAC.** Clipboard/screen не читались, station ACL не меняли. Отдельный пользователь/profile и file guard не закрывают эту поверхность. Также открыты owner local API / whole-chat routes / services / SMB остаток. G4 production не принят.
На 20:18 HOST 5580, Repo 23904, G2 28148 сохранили CreationDate и health/ready 200/200. Старые owner чаты оставлены. [Аудит истории, матрица совместимости и следующая точка](G3_BASELINE_HISTORY_AUDIT_2026-10-13.md); [policy snapshot](../runtime/host-g2/baseline-policy.json) не является универсальным ACL Apply/Rollback менеджером.

## G3 — G2 переключён и проверен, срез 2026-10-13 18:32 Asia/Bangkok

**G2-only runtime acceptance PASS; общий G3 OPEN, G4 не принят.** Пользователь локально запустил pinned runtime v0.0.15: PID 28148 → Python 19376 → Node 21812, SID 1009, non-admin. Actual native MCP и PowerShell/Python RW/RO/DENY PASS; UI flag сохранён, secret-related env names=0, diagnostic discovery 26 tools / 0 UI metadata / 0 resources. Health/ready/metrics 200, 17 выбранных UI/admin/Codex/Harpoon/MCP/SSE requests 404.
14 runtime объектов: 76 mutation handles DENY 5; read/execute ALLOW. Probes удалены, marker size/mtime сохранены. HOST 5580 и Repo 23904 сохранили CreationDate, health/ready 200 и launcher hashes. Общий helper не применялся; owner launchers/profiles/keys/ACL/Docker/services/Sites не менялись.
[G2 runtime acceptance и ограничения](G3_G2_RUNTIME_ACCEPTANCE_2026-10-13.md). Owner localhost API, whole-chat routes, service handlers и SMB/network остаются OPEN. Следующее — G3 изоляция без остановки существующих owner чатов; production RO/RW и итоговая приёмка остаются G4.

## G3 — только G2, срез 2026-10-13 18:06 Asia/Bangkok

Пользователь выбрал G2-only и сохранение работающих owner HOST/Repo. G2 рассматривается как основа будущего итогового HOST; G4 пока не принят. Repo Docker live metadata: uid/gid 1000:1000, RO rootfs, drop ALL, no-new-privileges, RW Repos/Workfiles mounts; Windows transport остаётся SID 1001.
G2 launcher подготовлен в Public RW с SHA256 A0680EB311B1BE2C0F7C3B1F9A0362DAC9F69C59A01C0AC293C3F08626ECF8F4. Исправлен duplicate guard: фактический owner SID вместо зависимости от argv order; restricted preflight PASS до key prompt. [G2-only evidence и локальный запуск](G3_G2_ONLY_SWITCH_2026-10-13.md).
**Новый G2 ещё не запущен: требуется локальный ввод separate key в консоли FortisHostG1.** Все три старых PID/CreationDate сохранены, healthz/readyz 200. Общий helper трёх owner launchers не применялся. G3 owner-local API / whole-chat isolation / services / SMB OPEN.


## G3 — runtime без admin API, срез 2026-10-13 16:06 Asia/Bangkok

Официальный runtime v0.0.15 скачан с проверкой release/manifest SHA256 и установлен side-by-side внутри защищённого tunnel-client дерева. Два изолированных Windows stdio MCP теста PASS; G2 подтвердил diagnostics 200 и admin/Harpoon 404, включая inherited transport override. Новые шесть объектов имеют read/execute ALLOW, mutation DENY под SID 1009.
Три live-лаунчера остаются исходными; новые кандидаты и default Preview/backup/rollback helper подготовлены, production Apply/rollback не выполнялись. HOST 5580, Repo 23904 и G2 8452 сохранили CreationDate и healthz/readyz 200. Оба synthetic экземпляра остановлены, их listener-порты закрыты; markers неизменны.
**Production-переход PENDING; localhost gate действующих туннелей ещё OPEN.** Общий G3 и whole-chat route isolation OPEN. [Evidence и точный план](G3_LOCAL_API_RUNTIME_2026-10-13.md), [JSON](G3_LOCAL_API_RUNTIME_2026-10-13.json). Перезапуск общего HOST требует отдельного согласия; G2 key вводит пользователь локально.


## G3 — после ACL, срез 2026-10-13 14:43 Asia/Bangkok

Пользователь согласовал и вручную применил четыре DACL для SID 1009 в 14:12. Root DACL совпали с backup After. Реальный G2 теперь получает Win32 5 на mutation handles, сохраняя read/execute. AccessCheck всех 22 758 объектов трёх runtime деревьев: 0 writable, 0 ошибок, 0 потерянного read/execute.
Synthetic junction, extended paths и localhost C$ сохранили DENY marker отказ; RW/RO чтение разрешено, RO запись запрещена. Probe objects удалены, original marker metadata не изменились.
Runtime ACL gate PASS; **G3 в целом OPEN**: localhost admin API старых туннелей доступен G2 (GET 200; Allow GET/PUT), C$ имеет INTERACTIVE Allow Full; service user-defined handlers и session isolation ещё не закрыты. Изменяющие API calls не отправлялись.
HOST PID 5580, Repo PID 23904 и G2 PID 8452 сохранили CreationDate, healthz/readyz HTTP 200. UI cards отключены. Backup сохранён; live rollback не выполнялся.
[Post-ACL evidence](G3_POST_ACL_VERIFICATION_2026-10-13.md), [scope/backup](G3_RUNTIME_ACL_PROPOSAL_2026-10-13.md). Следующее: поддерживаемая защита localhost administrative API и разделение ChatGPT routes. Owner profiles, services и shares на этом этапе не менялись.


## G3 — историческое обнаружение до ACL, 2026-10-13 13:58 Asia/Bangkok

Пользователь снова запустил G2: PID 8452 → Python 5152 → Node 23140, SID 1009, non-admin, UI disabled.
G3 **FAIL / STOP**: реальные write/append/delete handles доступны на общий Desktop Commander index.js; C:\Tools/runtime каталоги writable. Наследуемая AU ACE подтверждена ACL и AccessCheck под actual G2 token. Старый HOST Node под alexa использует тот же JS; фактическую подмену не выполняли.
Tasks ACL четырёх выбранных заданий и два Docker pipe дали DENY. SERVICE_USER_DEFINED_CONTROL у двух выбранных служб ALLOW и остаётся OPEN; остальные проверки G3 не завершены.
На срезе HOST PID 5580, Repo PID 23904 и G2 PID 8452 сохраняют CreationDate и healthz/readyz HTTP 200. G2 остаётся запущенным, активные тесты остановлены.
[Evidence](G3_READONLY_EVIDENCE_2026-10-13.md), [ACL proposal](G3_RUNTIME_ACL_PROPOSAL_2026-10-13.md). Remediation script подготовлен, syntax/Preview PASS; ACL не применены, требуется отдельное решение владельца. Session isolation и production acceptance остаются OPEN.


## G2 — ограниченный native HOST, срез 2026-10-13

G2 проверен под FortisHostG1 (SID 1009), non-admin; UI-настройка сохранена, после G2-G тестовый процесс остановлен. Новые PowerShell/.NET и Python MCP-тесты RW/RO/DENY PASS, RW readback совпал, свои probe-файлы удалены; original marker metadata не изменились.
G2-F: в этой сессии реально доступны также owner HOST под alexa и native Repo с RW Repos/Workfiles mounts. Session isolation не доказана. Repo Site остаётся diagnostic-only.
После G2-G HOST PID 5580 и Repo PID 23904 сохранили CreationDate и healthz/readyz HTTP 200. G2 PID 27324 / Python 16160 / Node 14112 остановлены, порт 60267 не слушает. Это датированная проверка, не live dashboard.
G2-G stop и rollback wrapper на временной копии PASS: [evidence](G2_G_EVIDENCE_2026-10-13.md). Production acceptance отсутствует. Подробное evidence и происхождение тестов: [G2-E/F](G2_E_F_EVIDENCE_2026-10-13.md).

````

## INSTRUCTIONS

INSTRUCTIONS_PREFIX

````markdown
**2026-10-15 — действующая граница G2:** применять уточнённый [Candidate Plan](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md). Guest own GUI/screen/clipboard и согласованные own apps/profile/cache/credentials/network разрешены; owner GUI/screen/clipboard/private data/control защищаются. UI metadata disabled не запрещает OS GUI. Проверять guest positive + owner negative; не запрещать все same-SID handles или полезные localhost endpoints. Reuse pinned runtime/source/fixtures; дополнительные HTTP cases только по Evidence Gap/новому решению. Минимальный ручной entry/stop допустим; новая automation/broker инфраструктура не prerequisite. Windows execution не выполнялось, consequential owner changes остаются отдельно согласуемыми. API приёмка защищает опасные действия и чувствительные данные; не требовать blanket 404/403 для каждого owner GET. GET /api/log-level в reviewed source — Candidate safe diagnostic при подтверждённой версии, PUT и sensitive/control routes оцениваются отдельно. Исторический GET200 не доказывает RCE.

**2026-10-15 — выполнять только остаток подпунктов Candidate Plan:** [G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md). Сохранять закрытые PASS в указанном scope; не скачивать/устанавливать narrow runtime, не повторять G1/G2/полный ACL scan, Session3 mutex/port-file smoke или старые fixtures без drift/нового Evidence Gap. Новая session требует адресной regression, не обнуления доказательств. Actual owner API remediation, session-specific GUI negative и final native MCP остаются открытыми; старый broad Apply/owner-session Launch не разрешены. Пересмотр документа не изменил Windows, launchers, ACL, сеть и публикацию.

**2026-10-15 — актуальный Candidate Execution / Verification Plan:** [G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md). Ежедневный ручной вход принят пользователем; Task Scheduler/autologon/SYSTEM broker и unattended cold boot сейчас необязательны. Для каждого шага указаны угроза, польза, достаточная приёмка и условия/затраты. План не разрешает consequential Windows changes: owner route migration/restart, ACL/mount/network/task изменения требуют отдельного конкретного решения. Документация сохранена; runtime не установлен/не перезапущен, commit/push/deployment нет.

**2026-10-15 — source-only owner HTTP API review:** [G3_OWNER_HTTP_API_SOURCE_REVIEW_2026-10-15.md](G3_OWNER_HTTP_API_SOURCE_REVIEW_2026-10-15.md) сопоставляет реальные admin routes, loopback/CSRF guards и config/wiring на commit a390c168ff1b2d14e73a95991c186c6aba3ff5a0. Штатного full-client local-admin-only disable/auth flag в просмотренном коде не найдено; --admin-key относится к удалённому control plane. Health details/metrics требуют отдельной оценки; runtime-only — Candidate для isolated compatibility, не одобренный owner rollout. Новых Windows проверок, live HTTP вызовов, restart, ACL/network/task изменений, commit/push/deployment нет. G3 BLOCKED.

**2026-10-15 ACTUAL owner migration Preview PASS (no changes):** user ran pinned `switch-launchers.ps1 -Mode Preview`, SHA256 `0D68581ADD6F0126D1E8A0F6DF993C92D52096F7E13028CA9A79D3F602BC2612`; all three live launcher paths (`HOST`, `Repo run-tunnel`, `Repo control`) returned `State=BEFORE`, with `Preview only. No files, processes, ACL or profiles changed.` This validates expected live file hashes, candidate pins and installed runtime SHA at preview time; **not** production compatibility or a mitigation of the actual SID1009 Session3 cross-session admin GET 200. Old `-Mode Apply` replaces all three launcher files, so **do not use for single-route rollout**. Next source-only design is precise one-route backup/change/revert with independent approval and owner routing check; live HOST/Repo remain unchanged. Details: `G3_OWNER_RUNTIME_ONLY_PREVIEW_2026-10-15.md`. G3 BLOCKED.

**2026-10-15 ACTUAL guest Session3 owner-local admin GET exposure CONFIRMED:** non-admin SID1009 sent status-only GET `/api/log-level` with no credentials and read no body; both OWNER SID1001 Session2 tunnel-client listeners `127.0.0.1:52632` (PID31064) and `127.0.0.1:8080` (PID28376) returned HTTP 200. This is G3 FAIL for admin-route isolation on that path; does NOT prove admin PUT/write or identify which PID is HOST vs Repo. No mutating methods will be attempted. Details `G3_LIVE_OWNER_LISTENERS_2026-10-15.md`. Candidate simpler remedy: tested-in-synthetic official `tunnel-client-runtime.exe` with absent admin routes; **not applied** to live HOST/Repo. Existing pinned `switch-launchers.ps1` SHA256 `0D68581ADD6F0126D1E8A0F6DF993C92D52096F7E13028CA9A79D3F602BC2612` and three migration candidate source hashes pass repo static validation. Owner-only read-only `-Mode Preview` staged in `G3_OWNER_RUNTIME_ONLY_PREVIEW_2026-10-15.md`; Windows preview still PENDING. Never run `Apply`, restart HOST/Repo or change launchers/ACL/AV without owner approval. G3 BLOCKED.

**2026-10-15 owner-local tunnel listener inventory ACTUAL PASS:** user ran pinned `Preview-G3TunnelListeners.ps1` SHA256 `900196F0B19A83968F00DF91A9180DAB5F668433011799E0ED5DD690F223C0BE`; snapshot UTC 2026-10-14T20:04:59.9309689Z: `tunnel-client.exe` PID 31064 OWNER SID1001 Session2 listening `127.0.0.1:52632`, and PID 28376 OWNER SID1001 Session2 listening `127.0.0.1:8080`. No SID1009 tunnel-client process observed within that specific name-filtered inventory, not proof no guest processes of other kinds. Which PID maps to HOST versus Repo is still UNVERIFIED. No HTTP requests or writes. Next proposed guest-only nonadmin SID1009 Session3 **GET /api/log-level response-code-only** on exactly those two current ports, no authorization/default credentials/response body/redirects, staged in `G3_LIVE_OWNER_LISTENERS_2026-10-15.md`; guest run PENDING. Prior 2026-10-13 guest GET HTTP200 remains historical only. G3 BLOCKED; no Windows changes.

**2026-10-15 G3 source-level owner API/lifecycle gate:** `G3_SESSION3_API_LIFECYCLE_GATES_2026-10-15.md` audited actual repo source and prior local API evidence. In a 2026-10-13 snapshot, non-admin SID1009 got unauthenticated HTTP 200 from HOST/Repo/G2 `GET /api/log-level` and OPTIONS advertised GET/PUT, **but no modifying API call was made**; actual 2026-10-15 listener/runtime state UNVERIFIED. Separate Windows Session3 only protects session-bound GUI objects, **not** localhost admin endpoints, file ACL, IPC or cross-plugin owner access. Unattended startup requires a separate feasibility review: Task Scheduler INTERACTIVE_TOKEN needs existing guest login, S4U lacks network/encrypted-files access, PASSWORD registration requires credential review and guest noninteractive Edge/MCP compatibility testing. **Read-only owner-local listener inventory staged**, `runtime/host-g2/Preview-G3TunnelListeners.ps1` SHA256 `900196F0B19A83968F00DF91A9180DAB5F668433011799E0ED5DD690F223C0BE`; static audit PASS, Windows run PENDING. No Windows mutation/task/service/restart. G3 BLOCKED.

**2026-10-15 outcome-based G3 architecture preference (user):** prioritize proved requirements + reliable/easy daily operation over a separately named private Window Station as an implementation detail. **Conditionally prefer dedicated non-admin SID1009 Windows client session** as owner-GUI/clipboard OS boundary, subject to actual synthetic negative capability checks and a startup/recovery design that does **not** need manual daily Fast User Switching or stored plaintext password. Passing Session3 mutex, Edge CDP startup and station metadata is **not** G3 acceptance. No launch/service/task/ACL/user/session changes authorized by this design statement. All route/IPC/owner API/filesystem/CDP and production operations gates remain. Details and requirement matrix in `G3_SESSION_BOUNDARY_OUTCOME_DECISION_2026-10-15.md`.

**2026-10-15 actual guest Session 3 station enumeration PASS:** user ran pinned local metadata `Inspect-G3GuestStations.ps1` SHA256 `941FED61BEB08A9370AEDFF8D4E05511AC4A896B9BCAD293312F2C7792BEB4E4` as non-admin SID1009 Session3. Returned current `WinSta0`, `CurrentStationVisible=true`, `EnumerationAllowed=true`, Win32=0, names `WinSta0` and `Service-0x0-218d7932$`, no ACL writes/desktop reads/owner-session touches. Windows Session3 `WinSta0` is **distinct** from owner Session2 `WinSta0`; enumerated Service-like name has unproven identity, ownership, DACL and is **not** approved for G2. New distinct private station create still failed Win32 183 with CWF_CREATE_ONLY. Next review: assess keeping G2 in dedicated guest Session3 as an OS GUI boundary **versus** original separate noninteractive station requirement; do not silently relax the user-accepted G3 criterion. Document `G3_SESSION3_STATIONS_READONLY_2026-10-15.md`. G3 BLOCKED, no Windows ACL/service/AV/runtime changes.

**2026-10-15 Actual guest private station CWF_CREATE_ONLY result:** pinned revised `Test-G3GuestPrivateStation.ps1` SHA256 `9F82E0E35D47CE32411AB52139DCDF4C41AFBB42F549562539955C916DC843F6` was locally executed as non-admin SID1009 / Windows Session3 and returned `Create private window station failed (Win32 183)` (`ERROR_ALREADY_EXISTS`). For `CreateWindowStation(null, CWF_CREATE_ONLY=1, ...)`, Windows derives the station name from the **logon session** and refuses creation when it already exists (Microsoft docs). This is **not** Win32 5 / namespace mutex denial; do not unset create-only or treat the preexisting station as isolated. No station/desktop was created in this attempt. Next guest-local READ-ONLY metadata source `Inspect-G3GuestStations.ps1` SHA256 `941FED61BEB08A9370AEDFF8D4E05511AC4A896B9BCAD293312F2C7792BEB4E4` static audit PASS, actual guest run PENDING. Runbook `G3_GUEST_STATION_EXISTING_OBJECT_2026-10-15.md`. No owner ACL changes, no persistent G2 runtime; G3 BLOCKED.

**2026-10-15 G3 private-station correction after actual guest failure:** user-local non-admin SID1009/Session3 test reached `CreateWindowStation` but explicit name `FortisG3-{GUID}` was rejected (outer PowerShell error did not include Win32 code). Microsoft `CreateWindowStationW` documentation allows only Administrators to specify station names. **Corrected source-only** `Test-G3GuestPrivateStation.ps1` to `CreateWindowStation(null, CWF_CREATE_ONLY=1,...)` so the system derives the name and existing stations cannot be reused; error reporting now includes Win32 number. SHA256 `9F82E0E35D47CE32411AB52139DCDF4C41AFBB42F549562539955C916DC843F6`, old `717D...` source superseded; local copy uses `FortisG3Station-9F82E0E3.ps1`. Static guards PASS, Windows native re-test PENDING. No Windows remote commands, ACL writes, service/AV changes or G2 runtime. Details: `G3_GUEST_PRIVATE_STATION_SMOKE_2026-10-15.md`.

**2026-10-15 actual SID1009 Session 3 Edge startup/CDP PASS:** user-provided guest JSON had `EdgeStartup=true`, `JobStopped=true`, `ProfileRemoved=true`, `Result=PASS`, non-admin SID1009/Session3, test Job assigned, Edge was alive before job cleanup. This supersedes prior staged-only status for `Test-G3GuestSessionEdge.ps1` SHA256 `2A9B2FF45E234E69F7461F8C00421DED0C34BA19C420C17739641CC42B933527`. Own `about:blank` CDP port file only; no DOM/CDP protocol, owner GUI denial, private station or runtime acceptance. **Next source-only gate staged:** `Test-G3GuestPrivateStation.ps1` SHA256 `717D0F1105B80795859204656CD4BC6D6C6B8945B1175EFE5B97ADB1B24162E6`, user-local nonadmin SID1009 Session3 creating and closing own named noninteractive station + desktop; Windows execution PENDING. See `G3_GUEST_PRIVATE_STATION_SMOKE_2026-10-15.md`. G3 BLOCKED.

**2026-10-15 G3 guest Session 3 Edge smoke test STAGED, NOT RUN:** `runtime/host-g2/window-isolation/Test-G3GuestSessionEdge.ps1` SHA256 `2A9B2FF45E234E69F7461F8C00421DED0C34BA19C420C17739641CC42B933527`. Fail-closed SID1009/Session3/non-admin; Edge suspended then attached to kill-on-close job, headless own `about:blank` / new guest temp profile, loopback ephemeral CDP, 20s timeout, no owner ACL/clipboard/screen/Edge profile access. Static source audit PASS, actual Windows compile and guest execution PENDING. Manual owner-to-Public script copy with hash, then local guest hash/run; abort on Kaspersky alerts. Details `G3_GUEST_EDGE_SESSION3_SMOKE_2026-10-15.md`; G3 BLOCKED.

**G3 next gate staged (2026-10-15):** guest SID1009 / Session 3 interactive Edge `--headless=new --dump-dom` synthetic data: URI, fresh guest scratch profile, default sandbox, 25s wait, taskkill only own spawned Edge process tree on timeout, guest-only profile cleanup and JSON result. Source `runtime/host-g2/window-isolation/Test-G3GuestEdgeSession3.ps1`, SHA256 `1DD2FAD0175C9AB23A85577ED80B2954F736C0700306BD76F75BCD73C4B15136`; design `docs/G3_GUEST_SESSION_EDGE_SMOKE_2026-10-15.md`. **Not yet executed on Windows.** User must paste full script into guest non-admin Session 3; owner repo path may not be guest-readable. No changes to OS/ACL/AV/HOST/Repo or old Session 2 launcher, no CDP/private station/runtime acceptance yet.

**Actual guest Session 3 named mutex PASS (2026-10-15):** locally under non-admin SID1009, a new unique `Local\\FortisG3GuestCheck-{GUID}` mutex was created successfully (`NamedMutexCreated=true`; reported no ACL writes/owner-object access), unlike SID1009 in owner's Session 2. An afterward standalone `finally {...}` paste produced a PowerShell parsing error; it does not invalidate the mutex result, but cleanup should be confirmed with a local `$mutex.Dispose()` or closing that console. This does not validate Edge, private station, IPC or G2 runtime. Details: `G3_GUEST_SESSION_MUTEX_TEST_2026-10-15.md`.

**2026-10-15 manual Fast User Switching evidence:** owner `quser` now lists `alexa` active Session 2 and `fortishostg1` disconnected Session 3. This confirms a separate guest client session without terminating owner session. The next bounded local test, documented in `G3_GUEST_SESSION_MUTEX_TEST_2026-10-15.md`, is under non-admin SID1009 *in Session 3*, creating a single uniquely named guest `Local\` mutex and immediately closing its handle. Result PENDING; owner-session DACL and present owner-created launcher stay unchanged; no session-switch automation/owner-object grants.

**G3 separate-session inventory result:** user ran read-only `quser.exe` in ordinary owner session. It showed only `alexa`, `console`, Session `2` Active (14.10.2026 15:04 login); no guest FortisHostG1 session observed. The next potential live step, **only after user approval**, is manual Windows Fast User Switching to FortisHostG1 and back, keeping owner logged in. No Windows switch, login, token setup, ACL, service, task, browser test or runtime operation performed by assistant. See `G3_SEPARATE_SESSION_FEASIBILITY_2026-10-14.md`.

**G3 separate-session feasibility (2026-10-14):** design investigation only, documented at [G3_SEPARATE_SESSION_FEASIBILITY_2026-10-14.md](G3_SEPARATE_SESSION_FEASIBILITY_2026-10-14.md). Launcher currently pins guest to owner SessionId via `CreateProcessWithLogonW` and supervisor `Attach`; changing desktop or SessionId equality is not an isolation fix. Next allowed observation is owner-local read-only `quser.exe` session inventory. No Windows native commands executed via remote transport; no ACL/service/task/antivirus change and no runtime/Git publish.

**2026-10-14 22:35 Asia/Bangkok — confirmed native owner DACL audit:** SID1001 elevated Session 2 read `\Sessions\2\BaseNamedObjects` DACL with `NtQueryStatus=0`, zero ACL writes. Its ACEs grant owner/SYSTEM/current owner-logon SID directory create access, but neither direct guest SID1009 nor Everyone gets `DIRECTORY_CREATE_OBJECT=0x4` / `READ_CONTROL`; actual SID1009 guest previously returned `STATUS_ACCESS_DENIED` to both. No global/shared namespace rights extended. Preferred next design study: isolated guest Windows session; no native tests or launch authorized yet. See `G3_NAMED_MUTEX_BLOCKER_2026-10-14.md`.

**2026-10-14 22:10 Asia/Bangkok actual SID1009 Namespace:** Session 2 guest returned `0xC0000022` for both DIRECTORY_CREATE_OBJECT and READ_CONTROL on `\\Sessions\\2\\BaseNamedObjects`; SID1009 nonadmin/private station/descendant match; Node/child exit 0. This is positive diagnostic evidence of an access block, not successful guest namespace access. Staged owner-only metadata script `runtime/host-g2/window-isolation/Inspect-G2SessionNamespace.ps1` pin `029687DFEF5C02959D39FA5F07CBBB89DFE51F6C867FFF8A8363B54DE8C55E08` reads current-session BaseNamedObjects DACL via NtQuerySecurityObject with no writes/credentials/guest/Edge/mutex; static source safety check PASS, native Windows execution PENDING. Do not approve broad session ACL grant or Launch. See `G3_NAMED_MUTEX_BLOCKER_2026-10-14.md`.

**2026-10-14, after user reboot:** user received `Owner ACL changed; obtain a fresh reviewed Preview before Launch` while attempting `-Mode Namespace`. The launcher had an unconditional historical ACL hash gate before its diagnostic early return; repaired so historical `approved` hashes are checked **only** for `-Mode Launch`. `Preview` continues to compute metadata and `Namespace` does not apply window ACL or start permanent G2. Original Launch approval hashes were NOT updated, bypassed for Launch or assumed to be safe after reboot. New operator SHA256 `FBF238E84E31C426938D2619B497A9F5D8C27341982CD27FFCE00D92EA85DB8F`, Node unchanged `8B2C8FB84EA94F7226BE4A43F28E6483720F2C7F7A26866C20624DBBC6DAE2D1`. Repo Node syntax and static branch/pin checks passed; Windows AST / post-reboot elevated Preview / SID1009 Namespace **PENDING**. Stop on any Kaspersky detection; no exceptions/owner ACL writes. Detailed evidence: `G3_NAMED_MUTEX_BLOCKER_2026-10-14.md`.

**Newest staged G3 test, 2026-10-14:** `-Mode Namespace` in operator `FC61301317568A77CCAEB7F2510AF93336276F8DFED1B71E18C7A5464CDB6616`, Node `8B2C8FB84EA94F7226BE4A43F28E6483720F2C7F7A26866C20624DBBC6DAE2D1`. This runs local authenticated SID1009 *read-only* `NtOpenDirectoryObject` for session `BaseNamedObjects` (create right 4 / READ_CONTROL), with no mutex/Edge invocation in this branch, no runtime key, no main window ACL writes and private child/job cleanup. Repo static syntax/branch/pin tests PASS; actual Windows/guest result PENDING. Kaspersky exceptions not added; avoid remote Windows diagnostic shell. See `G3_NAMED_MUTEX_BLOCKER_2026-10-14.md`.

**2026-10-14 02:21 SID1009 result:** unnamed mutex PASS(0), unique unprefixed and unique `Local\\` mutex DENY(5); Edge exit21 ProcessSingleton. Owner session object-directory control open PASS, but guest directory check not yet run. Latest read-only guest directory NTSTATUS probe staged in Node `7B67C2865559946A9428E6C0DC8E71207ACB0C9438BA754323C892C51DD78A43` and operator `3346B6FA450F5E6BFB60A0FBB92FD53E82EB5FFB44C5FAF63FBB4BF9E52FC900`. Node syntax and Windows operator AST pass; independent C# compile attempt blocked by tool (`spawn EPERM`), do not claim guest execution. No ACL, key or runtime changes. Details in `G3_NAMED_MUTEX_BLOCKER_2026-10-14.md`.

**2026-10-14 newest staged diagnostics:** operator `AE94E0F59527192D2B84DBEC18C8953A3C594BC163CE7B3A99A5DA695FC176F8` now offers separate elevated `-Mode Diagnose`: local Windows credential, SID1009 preflight, synthetic result and cleanup only. It returns before runtime-key prompt, owner ACL backup/apply and permanent runtime. Node pin `A512DC3B631E938C215134A9DA3A4CAD7B88B0E4A77028BD2A768AEF4DD0AC9C`. AST/Node syntax pass; post-change Preview execution blocked; actual credentialed Diagnose remains untested. Older operator SHA 9068 and 05B6 superseded. Details in `G3_NAMED_MUTEX_BLOCKER_2026-10-14.md`.

**2026-10-14 current G3 operator stage:** newly pinned diagnostic operator `9068A613987AD32B0A49EB126FFD33C521CBC26F0B2607CCC19BB201CB694D50` includes unnamed/unprefixed/Local mutex checks in Node `A512DC3B631E938C215134A9DA3A4CAD7B88B0E4A77028BD2A768AEF4DD0AC9C`. Windows AST and read-only Preview pass; live SID1009/Edge not retested. Prior 05B6 operator is superseded; do not use its hash for new diagnostic. See `G3_NAMED_MUTEX_BLOCKER_2026-10-14.md`.

**2026-10-14, diagnostic source only:** `runtime/host-g2/window-isolation/private-station-node-probe.js` adds own unnamed and unprefixed mutex checks. Repo Node syntax PASS, SHA256 `a512dc3b631e938c215134a9da3a4cad7b88b0e4a77028bd2a768aef4dd0ac9c`. Not deployed to protected bootstrap and not in launcher capture pins. Credentialed SID1009 tests and Edge compatibility still OPEN. Do not update pins or execute Launch as though acceptance were proven; see `G3_NAMED_MUTEX_BLOCKER_2026-10-14.md`.

````

INSTRUCTIONS_HISTORY

````markdown
## Подготовленный G3 runtime-переход, 2026-10-13 16:06 Asia/Bangkok

[План и evidence](G3_LOCAL_API_RUNTIME_2026-10-13.md). Новый binary installed side-by-side; три live-лаунчера не изменены. Кандидаты находятся в runtime/host-g2/runtime-api-migration, default helper Preview PASS. Они отключают local admin UI/API и дополнительный Harpoon HTTP transport, сохраняя doctor на full client и health/metrics.
Production Apply/restart/rollback не выполнялись; Sites не публиковались. Не считать source bundle автодеплоем или доказательством chat isolation.

## G2-only scope, 2026-10-13 18:06 Asia/Bangkok

Пользователь выбрал переключать только G2. Не применять общий switch-launchers.ps1 на этой точке. Новый G2 standalone launcher проверен и помещён в Public RW; actual switch ждёт локальный separate key. Duplicate guard исправлен на фактический owner SID. [Evidence/команда](G3_G2_ONLY_SWITCH_2026-10-13.md). HOST/Repo live launchers и processes не менялись; G4 не принят.

## G2 runtime действительно запущен, 2026-10-13 18:32 Asia/Bangkok

Пользователь выполнил локальный G2-only запуск standalone launcher с отдельным ключом. Actual runtime/MCP/ACL/UI/API приёмка PASS в указанном scope: [evidence](G3_G2_RUNTIME_ACCEPTANCE_2026-10-13.md). Owner HOST/Repo runtime/launchers не переключались; общий switch helper не применять в этой операции. G3 OPEN, G4 не принят; это не production acceptance и не публикация Site/plugin.


## G2 baseline / история, 2026-10-13 20:18 Asia/Bangkok

Live changed only G2 Desktop Commander allowedDirectories: Workspace + three previously OS-protected runtime roots; hot readback PASS, no restart/publication. Windows ACL provide effective RO on runtime; source baseline-policy.json is a documented snapshot, not automatic deployment/enforcement. Other G2 command/shell settings preserved; owner HOST/Repo continue unchanged.
[Evidence / compatibility / project extension procedure](G3_BASELINE_HISTORY_AUDIT_2026-10-13.md). G3 remains OPEN: shared WinSta0 grants G2 clipboard/screen/WRITE_DAC; no actual clipboard/screen read or station ACL mutation. Further project grants require exact Windows root/actions/dependencies, backup/rollback preview and actual-token acceptance; do not infer shell containment from allowedDirectories. Universal ACL manager is not implemented.


## G3 window isolation prototype, 2026-10-13 21:13 Asia/Bangkok

[Evidence/следующий local Preview](G3_WINDOW_ISOLATION_PROTOTYPE_2026-10-13.md); source runtime/host-g2/window-isolation. Private station/PS/Node/Edge-CDP/synthetic object deny PASS, owner DACL unchanged. Preview-only source hash and component CAS accepted via non-elevated HOST; elevated local owner inventory remains required. No runtime deployed/restarted or ACL applied; owner-controlled credentialed private launcher and live backup/CAS rollback are not yet implemented. Do not apply prospective deny with old G2 handles retained, and do not use test controller as a production supervisor. G3/G4 not accepted.


## G3 private launcher staging, 2026-10-13 22:35 Asia/Bangkok

[Evidence/local handoff](G3_PRIVATE_LAUNCHER_STAGING_2026-10-13.md). Elevated user Preview COMPLETE; staged Start-G2PrivateWindow.ps1 supports Preview/Launch/Rollback with component capture/pins, protected bootstrap and PID-bound pipe, owner-only backup and CAS. Parse/compile/Preview and synthetic policy/env/job/pipe PASS. Credentialed private launch remains local pending; CLI/Edge selftest precedes any owner station/desktop writes and runtime-key prompt.
No live ACL applied, no runtime restarted/published. Close only old G2 console for local transition; preserve HOST/Repo. Fresh elevated owner only; Windows password/key stay masked/local. Reject any remaining G2/UNKNOWN process and unexpected original ACL; backup rollback rejects foreign later changes. After local launch require actual-token/native MCP/station/open-DENY/compatibility/owner-preservation acceptance. Window-object ACL is per logon session; G3 OPEN, G4 not accepted.


## G3 Attach correction, 2026-10-13 23:00 Asia/Bangkok

[New pins/local retry/evidence](G3_PRIVATE_LAUNCHER_ATTACH_FIX_2026-10-13.md). First credentialed preflight failed Win32 5 at Attach before key/ACL writes. Scoped caller-only SeDebugPrivilege cross-account token check and explicit native-stage labels added. Previous caller privilege state restored before Resume; target SID1009 remains non-admin and job/session/identity checks remain. Windows compile/AST/Preview and non-admin missing-privilege rejection/restoration test PASS; actual admin/credentialed retry pending fresh local elevated owner console. HOST/Repo preserved, no live window ACL/restart/publication. Earlier E56E…/0A09… source pins are historical; use new 3A30…/1A7D… pair.


## G3 query-only token correction, 2026-10-13 23:19 Asia/Bangkok

[Current pins/evidence/local retry](G3_PRIVATE_LAUNCHER_QUERY_ONLY_2026-10-13.md). User retry isolated Attach/OpenProcessToken Win32 5 after scoped privilege enable, before key/ACL writes. Request reduced TOKEN_QUERY|TOKEN_DUPLICATE to TOKEN_QUERY; target SID/groups/elevation/primary/session are read natively, WindowsPrincipal duplication removed. Administrators membership incl. deny-only rejects target; suspended/job/session/identity guards remain.
Windows compile/AST/Preview plus real query-only handle SID/primary/session, duplicate DENY, wrong SID and filtered admin account rejection PASS. Actual G2 query-only credentialed preflight pending fresh elevated local owner console. HOST/Repo preserved, main window ACL unchanged. Use operator 6DD2… / supervisor F619…; prior pins historical. No restart/publication/commit/push; G3/G4 not accepted.


## G3 preflight transport, 2026-10-13 23:43 Asia/Bangkok

[Current operator 0CF2…/evidence/local retry](G3_PRIVATE_LAUNCHER_PREFLIGHT_TRANSPORT_2026-10-13.md). Query-only guest Attach returned; old late-result pipe timed out before key/ACL writes. Test PS receives process-only Bypass; early PID-bound progress/error frames and child-exit polling added. Persistent policy/OS scope/IPC ACL untouched; F619… Supervisor unchanged.
Windows compile/AST/Preview and actual same-account Restricted script block, Bypass success, structured exception and early-exit fixtures PASS. Guest private transport/CLI/Edge and window gate still pending local; exact old G2 execution policy inferred, not observed loaded. HOST/Repo preserved; main ACL/restart/publication/commit/push none. G3/G4 not accepted.


Дополнение 2026-10-13 23:57 Asia/Bangkok: limited client GW fixture denied connect (exit94), GRGW fixture result/PID binding PASS. Production pipe guest grant changed only GW→GRGW on random diagnostic channel; no key/password data, filesystem/window scope unchanged. Final operator 0CF2… pinned Preview PASS; actual guest transport/runtime/window ACL acceptance pending.


## Detailed preflight verdict, 2026-10-14 00:10 Asia/Bangkok

[Current operator 2CB5… diagnostic/evidence](G3_PRIVATE_PREFLIGHT_VERDICT_2026-10-14.md). Actual guest reached all progress stages then final preflight predicate failed. Only synthetic report printing added before unchanged checks; no permissions, policy, Supervisor, runtime/ACL guards changed. Windows compile/AST/pinned Preview PASS, original owner window hashes unchanged. Exact failed Node/Edge/exit/station field awaits local report; do not claim Edge/isolation fix. No main ACL/runtime acceptance; G3/G4 open.


## Edge startup diagnostic — 2026-10-14 00:46 Asia/Bangkok

[Current exact pins/evidence/local retry](G3_EDGE_STARTUP_DIAGNOSTIC_2026-10-14.md). User report isolates failure to Edge exit21 before CDP; guest SID1009/private station/CLI descendant/Workspace/runtime protection/cleanup pass in that synthetic scope. New D5ED… operator pins diagnostic Node 4A58…: own fresh-profile Edge stderr max4096, early exit, native profile-lock test and LABEL-only station/desktop plus own token integrity metadata. Default sandbox, Supervisor F619… and all permissions/guards unchanged.
Windows syntax/AST/metadata compile/owner synthetic lock test/pinned Preview PASS; main owner DACL hashes unchanged. Actual G2 diagnosis still requires fresh elevated local owner retry and masked credential, before runtime-key/main ACL stage. Owner HOST/Repo left running. Do not claim exit21 cause, live clipboard protection or accepted private runtime. G3/G4 remain open.


## Private object compatibility — 2026-10-14 01:11 Asia/Bangkok

[Current exact pins/evidence/local launch](G3_PRIVATE_OBJECT_COMPATIBILITY_2026-10-14.md): operator 05B6…, supervisor E63C…, Node BE06… supersede D5ED…/F619…/4A58…. Actual report: ProcessSingleton failure, lock probe0, guest Medium; installed Edge cause still not proven. Staged guest private object masks restored to full 0xf037f/0xf01ff only inside new noninteractive private environment, correcting Chromium desktop-ACL clone compatibility and matching prior successful prototype. Guest can mutate these private object ACLs; main owner deny/CAS/job/identity/session guards and Edge sandbox unchanged.
Windows combined compile/AST/Node/Preview + memory ACL matrix PASS; main DACL hashes unchanged. Node now reports read-only existing startup-mutex open, own random mutex create and own private message-window Win32 errors. Main-station message-window guard tested=-1; no owner GUI/clipboard/screen or existing mutex modification.
Actual local credentialed G2 Edge preflight, main Apply and private runtime acceptance still pending; fresh elevated owner console required. Owner HOST/Repo preserved; no service/task/common runtime restart/publication/commit/push. G3 OPEN/G4 NOT_ACCEPTED.


## Handoff / latest named-mutex blocker — 2026-10-14 01:30 Asia/Bangkok

[Latest actual verdict and continuation](G3_NAMED_MUTEX_BLOCKER_2026-10-14.md). 05B6… / E63C… / BE06… pins still current. Private message window0 and lock0; new own Local mutex5, startup mutex5, Edge21. Full private rights did not resolve blocker; exact namespace/token cause unproved. Main owner DACL still original in fresh Preview, no main Apply or private runtime acceptance. UI hiding already separate/completed; screen/clipboard false fields are no-read, not DENY.
Next: read-only named-object/token diagnosis and bounded demonstrated remedy before credentialed retry; keep owner HOST/Repo. Continue remaining G3 then G4–G6. No source, ACL, runtime, service/task, Docker/Site changes, restart, publication, commit or push for this handoff.
````

## SESSION_DECISION

SESSION_DECISION

````markdown
**Уточнение границы пользователем, 2026-10-15:** G2 разрешены собственные GUI/экран/clipboard гостевой Windows-сессии. Запрет относится к доступу из G2 к основной сессии alexa, включая обычные окна без elevation. Synthetic positive проверки guest GUI/clipboard допустимы; owner contents не читать. Свои guest процессы/handles, разрешённые приложения, рабочие browser profiles и нужная сеть не запрещаются автоматически. Headless/private station/supervisor/Job/IPC broker — варианты реализации, а не самостоятельные требования. Ручной ежедневный вход принят; полный новый порядок и критерии — [в актуальном Candidate Plan](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md). Старые архитектурные формулировки ниже не должны создавать более широкий запрет или отменять доказанные scoped PASS. Это уточнение документации, не native test или deployment. Owner API защищается по опасным действиям и чувствительным данным; safe diagnostics допустимы при доказанной семантике/версии. Исторический admin-GET-DENY FAIL остаётся evidence своего теста, а не автоматическим запретом всех GET.

**Актуальное решение пользователя в этом чате, 2026-10-15:** ежедневный ручной вход в FortisHostG1, запуск G2 и переключение обратно в alexa с открытой guest-сессией допустимы. Несколько минут в день приемлемы; фактическая длительность пока неизвестна. Это заменяет прежние требования ниже «HARD PRODUCT GATE» без ежедневного Fast User Switching и unattended cold boot. Безопасность GUI/clipboard/API/files и работа после переключения остаются обязательными. Task Scheduler, autologon, stored password и privileged broker не требуются ради прежнего UX gate. Актуальный [Candidate Plan](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) содержит порядок, угрозы и критерии приёмки. Старый текст ниже сохраняет историю решения; изменение документа не означает native PASS или production approval.

**Decision: CONDITIONALLY PREFER guest SID1009 in its own Windows client session over a second private Window Station. DESIGN ONLY; G3 BLOCKED / NO PRODUCTION LAUNCH APPROVAL.**

User priority, 2026-10-15: meet real requirements, preserve normal Windows and Fortis functionality, avoid noticeable operational inconvenience, and do not choose complex implementation when a simpler adequate boundary exists. This is an **architectural preference**, not permission to weaken security acceptance, create startup tasks/services, copy credentials, change ACLs, or start a persistent G2 runtime.

## Why session isolation is a reasonable candidate

Microsoft documents that each Windows client session has its own `WinSta0` and that a window station contains its own clipboard. The object name `WinSta0` repeated in two separate client sessions is **not** proof of access to the same GUI. Per-session `Local\\` namespaces also explain observed named mutex differences. However session boundaries are not a claim of isolation from **all** owner information: the guest may still reach permissive filesystem paths, named pipes, loopback TCP services, admin endpoints, inherited process handles, exported files or an explicitly configured clipboard bridge.

Actual user-local evidence:
- Owner `alexa` active Windows session 2; guest `FortisHostG1` (SID1009, non-admin) has separate session 3, remains logged on when disconnected after manual Fast User Switching.
- SID1009 in **owner Session 2**: `\\Sessions\\2\\BaseNamedObjects` create/read-control STATUS_ACCESS_DENIED; new named mutex Win32 5; Edge ProcessSingleton exit21. No main owner station ACL apply.
- SID1009 in its **own Session 3**: new `Local\\` mutex created, installed headless Edge fresh own profile + local DevTools port-file PASS; job stopped and temp profile removed.
- Native guest station metadata: current `WinSta0`, visible=true, enumeration `WinSta0`, `Service-0x0-218d7932$` **name only**; no ACL writes/desktop contents read. Never reuse the service-like station for G2.
- New separate noninteractive guest station is **not** achieved from that interactive logon: specified-name attempt failed as standard user, `CreateWindowStation(null,CWF_CREATE_ONLY=1)` returned Win32 183 (preexisting logon-derived object).

Basis: `G3_SESSION3_STATIONS_READONLY_2026-10-15.md`, `G3_GUEST_EDGE_SESSION3_SMOKE_2026-10-15.md`, `G3_NAMED_MUTEX_BLOCKER_2026-10-14.md`; `G4_ACCESS_POLICY_PROPOSAL_2026-10-13.md` states that a separate station/**session** may provide the clipboard boundary only after actual synthetic OS gate.
## Outcome-based G3 acceptance matrix

| Requirement | Evidence / decision |
| --- | --- |
| Separate non-admin Windows principal | **PASS in synthetic local tests** (SID1009, Session 3, Admin=false). Must verify for every launched G2 descendant. |
| No access to owner screen, clipboard, GUI/window objects | **PENDING**. Windows session-scoped station/clipboard is a promising design boundary, **not** an actual owner-object deny verdict. Need controlled negative capability checks without reading actual owner pixels, clipboard, windows or secrets. |
| No G2 UI or Windows input interference visible in owner session | **PENDING**. Guest `WinSta0` is interactive **in its own Session 3**; verify its disconnect/background behavior, no focus stealing/switching, no accidental guest UI shown to owner. |
| Browser, CLI, Node, PowerShell, Python, Git, CDP/DOM/storage | **PARTIAL**: unique mutex and Edge startup/CDP port-file PASS. Full CDP command, synthetic DOM+storage, CLI chain, child-job cleanup and filesystem gates PENDING. Browser default sandbox stays on; always fresh own profile. |
| Owner private files, credentials, runtime immutability | **PENDING**: OS session separation does not replace NTFS, process, user-profile and IPC policy. Real synthetic RO/RW/DENY and no inherited owner secrets/handles required. |
| Protect owner local APIs / network / named pipes / debug ports / Site and native chat routes | **PENDING**: Windows loopback `127.0.0.1` is not per-session authorization; audit listener bindings/authentication and reject owner-only routes from guest. Do not rely on native HOST/Repo UI or prompt policy for OS enforcement. |
| Start/stop and usable automation without daily manual Fast User Switching | **PENDING, HARD PRODUCT GATE.** Manual Session 3 login is acceptable **only as an experiment**. A production solution cannot require owner to repeatedly switch/log into guest after restart, display prompts for passwords in automation, change foreground focus or disrupt owner work. No new privileged service/task/autologon/saved password without separate approval and threat review. |
| Recovery and continuity | **PENDING**. Runtime must behave safely on reboot, logoff, unexpected child exit; owners retain HOST/Repo, antivirus, credentials and sessions. Session ID must be discovered each logon, never hard-coded as 3. |
| Replacing private noninteractive station mechanism | **CONDITIONAL DESIGN CHOICE ONLY**. Keep security outcomes above unchanged. Use Session 3 alone **only after** the owner-GUI/clipboard denial and practical lifecycle are accepted. Fall back to private station/stronger isolation if necessary. |

## Preferred minimal implementation path

1. **Source-only threat model now**: map all G2 launch/control routes, owner local API endpoints and any guest-accessible inherited handles; identify unavoidable privileges and potential clipboard redirection. No Windows mutations.
2. **Synthetic capability preflight** (later and separately approved): run only within the already-created guest Session 3, log SID/logon/session/station and owned child handles; verify local named-object/Edge/CLI and explicit OS negative capabilities. No owner screenshot/clipboard reads or changing actual clipboard contents.
3. **Operational feasibility before implementation**: design a guest-local supervisor and owner↔guest authenticated narrow IPC with job cleanup. Prove startup on owner login/reboot and guest session termination without stored plaintext password, interactive daily switch, local SYSTEM service, RDP listener or prompt-driven loop.
4. **Production acceptance**: verify normal owner HOST/Repo and other chats unaffected, Windows GUI owner protection, G2 user workflow and tools, full G3 gates. Only then consider retiring old owner-session G2 path, explicit owner approvals and rollback design.

**Fail closed:** If item (2) or (3) cannot be met cleanly on this Windows installation, the simple Session 3 approach is not accepted. Do not report G3 PASS, quietly enable auto-login, broaden ACLs, weaken Kaspersky/sandbox, reconfigure owner sessions, or run the old `Start-G2PrivateWindow.ps1 -Mode Launch`. Re-evaluate a dedicated isolated guest execution context with explicit owner approval.

Sources:
- Microsoft [Window Stations](https://learn.microsoft.com/en-us/windows/win32/winstation/window-stations), [Remote Desktop Sessions](https://learn.microsoft.com/en-us/windows/win32/termserv/terminal-services-sessions), [Kernel Object Namespaces](https://learn.microsoft.com/en-us/windows/win32/termserv/kernel-object-namespaces).
- Project [G4 proposed convenience/security matrix](G4_ACCESS_POLICY_PROPOSAL_2026-10-13.md), [G3 original prototype](G3_WINDOW_ISOLATION_PROTOTYPE_2026-10-13.md).

**Work this turn: documentation only.** No remote Windows process, owner/G2 station ACL, service/task/autologon/startup, policies, credentials, browser or runtime changed; no Git commit/push. G3 remains BLOCKED.
````

## DOCS_INDEX

DOCS_INDEX

````markdown
## Историческая точка до применения ACL, 2026-10-13

[G3 evidence](G3_READONLY_EVIDENCE_2026-10-13.md): G3 FAIL/STOP на writable shared runtime. [Точечное ACL предложение](G3_RUNTIME_ACL_PROPOSAL_2026-10-13.md), подготовленный script — Preview only до отдельного согласия владельца. G2 повторно запущен, старые HOST/Repo сохранены.

## G3 — после применения ACL, 2026-10-13

[Post-ACL verification](G3_POST_ACL_VERIFICATION_2026-10-13.md): четыре ACL применены пользователем, runtime gate PASS на 22 758 объектах; junction/namespace synthetic DENY сохранён. Общий G3 остаётся OPEN на localhost API, service user-defined controls и route isolation.

## G3 — localhost API: проверка и подготовленный переход, 2026-10-13 16:06 Asia/Bangkok

[Runtime evidence и порядок переключения](G3_LOCAL_API_RUNTIME_2026-10-13.md): два изолированных теста PASS, verified runtime installed side-by-side, candidates/Preview готовы. Действующие HOST/Repo/G2 ещё используют full client; production switch и whole-chat isolation PENDING/OPEN.

## Текущая точка: только G2, 2026-10-13 18:06 Asia/Bangkok

[G2-only staged launcher и local start](G3_G2_ONLY_SWITCH_2026-10-13.md). Owner HOST/Repo сохранены; общий rollout не согласован. G2 как основа итогового HOST требует завершить G3 и принять G4.

## Текущая точка: G2 runtime принят в тестовом scope, 2026-10-13 18:32 Asia/Bangkok

[G2 runtime acceptance](G3_G2_RUNTIME_ACCEPTANCE_2026-10-13.md): реальное переключение выполнено пользователем, native MCP/ACL/headless/API проверки PASS; HOST/Repo сохранены. G3 routes/services/network OPEN, G4 production PENDING.
````

## LIFECYCLE_NEXT

LIFECYCLE_NEXT

````markdown
## Ordered next work, without running Windows commands now

1. Inventory current owner HOST/Repo and G2 runtime profile features and actual localhost listener routes through **narrow read-only metadata** after security review. Do not send writes to owner APIs or inspect owner keys. Treat old 8080/58122/65069 ports as historical.
2. Draft a *single* isolated **guest-only noninteractive startup compatibility** acceptance test for a future user-approved Task Scheduler trial (no G2 runtime key). It must verify exact SID1009/non-admin, actual Windows SessionId, WinStation name+visibility, unique Local mutex, own headless Edge startup/job cleanup and network reachability to a disposable synthetic endpoint. No automatic task creation yet.
3. If synthetic trial passes and the owner approves credential/cold-boot semantics, design least-privileged task registration with OS security review, supervised child lifecycle, separate G2 key management and automatic recovery. If not, reject task approach instead of relaxing GUI/security requirements.
4. Separately prove denied access to owner window/clipboard via *non-sensitive* synthetic handles plus owner API/IPC negative controls; test CLI and real G2 tools without changing owner HOST/Repo.
5. Approve and transition production only after all gates and a reversible one-service-at-a-time plan; preserve owner chats, services, repo mounts and antivirus. G3, G4–G6 remain open.

````

## STATION_GUIDANCE

STATION_GUIDANCE

````markdown
## Safe architecture choices (review only)

**A. Guest Session 3 as the OS GUI boundary.** Prefer assessment of guest-local G2 processes under SID1009 / Session3 (headless Edge, CLI, Node) while owner remains Session2. Existing guest `WinSta0` is interactive **within guest Session3**, but is not owner `WinSta0`. Ensure no owner-origin inherited station/desktop/clipboard/process handles; no guest UI reaches owner Session2; run a separate synthetic metadata/negative access acceptance without reading real owner GUI or clipboard. This may meet the owner-protection goal, but relaxes the original *separate private noninteractive G2 station* architecture requirement and thus **requires explicit review/approval**, not a silent reinterpretation of G3.

**B. Dedicated guest-owned noninteractive station as originally designed.** Regular non-admin guest may only request logon-derived station names; the current logon has existing such object (`CWF_CREATE_ONLY`=183). A new standard guest logon/execution context may allow creation of a fresh unnamed-by-caller station inside guest Session3, but this is unproven and introduces controller/token/session/bootstrap/cleanup/credential risks. Do not use `Service-0x0-218d7932$`, remove create-only, elevate guest, modify owner-session DACL, start new SYSTEM/RDP services/tasks or weaken Edge sandbox to simulate success.

Both options still need: a guest-owned supervisor/job with no owner handles, owner↔guest IPC with constrained authentication and local binding, an after-switch/logoff/reboot recovery plan, actual protected-filesystem and native CLI/Edge CDP/DOM/storage acceptance, negative owner-object capability checks without reading sensitive contents, owner HOST/Repo health, and no Kaspersky alerts.

## User's outcome/operations preference — design continuation

On 2026-10-15 user prioritized measurable security requirements and normal Fortis usability, avoiding unnecessary complexity. Session-based GUI protection is **conditionally preferred** only if actual owner-data isolation and unattended operational recovery pass; see `G3_SESSION_BOUNDARY_OUTCOME_DECISION_2026-10-15.md`. Original distinct private-station architecture remains a fallback, not a protection waived without equivalent evidence. Manual Fast User Switching is experimental, not accepted daily production UX. No Windows modifications from this decision.

## Immediate next development step

**Source-only threat-model / G3 acceptance matrix**: compare Option A (session-based GUI isolation) and Option B (separate private station) against user's original G3 criteria. Identify which checks can be satisfied by Windows documented session boundary and which need live negative tests. Do not stage another native creation attempt until the architecture decision is reviewed. No production G2 launch, owner ACL Apply, credential prompt, persisted task/service, Git commit or push in this step.

**State:** mutex PASS, guest interactive Session3 Edge CDP startup PASS, station metadata PASS, distinct private station FAIL / not accepted, G3 BLOCKED.
````

## WINDOW_README_PRELUDE

WINDOW_README_PRELUDE

````markdown
Status: SYNTHETIC_PASS / LIVE_NOT_APPLIED, 2026-10-13.
The current G2 still runs on owner WinSta0; do not claim the clipboard/screen gate is closed.
Owner HOST/Repo and the live G2 have not been restarted.

````

## API_REVIEW_VERIFICATION

API_REVIEW_VERIFICATION

````markdown
## Candidate Verification Plan

1. Source matrix выше становится основой отрицательной приёмки. Не ограничиваться
   прежними пробами /api/tunnels, /api/profiles, /api/config, /api/restart:
   они не зарегистрированы в просмотренном adminui и их 404 не проверяет реальные handlers.
2. Изолированный disposable fixture без настоящих profiles/credentials проверяет разрешённый
   MCP поток и все зарегистрированные admin route families. Mutating методы допустимы
   только в этом отдельном synthetic fixture с fake bridge/controller и доказанным scope.
   Проверить, что отказ случается до handler, не меняется synthetic controller и не запускается bridge.
3. Для runtime-only требовать отсутствия настоящих GET/admin и mutating routes;
   /harpoon/mcp проверять отдельно. Для auth gate требовать 401/403 до handler и разрешённый
   synthetic owner flow. 405, 400, 500/503 не доказывают авторизацию.
4. Перед возможной production заменой — user-local metadata: точные PID, owner SID,
   CreationDate, EXE hash/version, listener и route mapping, без secret argv/env/keys.
   Это будущая проверка, в этом этапе она не выполнялась.
5. После отдельно одобренного изменения каждого owner route — user-local guest SID1009,
   non-admin, фактическая отдельная session; ограниченные GET/status-only negative probes,
   без credentials, redirects, proxy и response body. Не вызывать export/stream и live write.
   Ожидается отказ только на доказанно живом правильном listener; connection failure —
   BLOCKED/неопределённость, а не DENY. Exact-path 404 проверяет только этот путь.
6. Отдельно подтвердить owner MCP и требуемые health/monitor функции.
   Live отсутствие mutating paths обосновывать reviewed artifact + isolated tests,
   не отправкой опасных POST/PUT к owner. Все consequential изменения требуют
   точного one-route Preview/backup/rollback и отдельного решения владельца.

Следующий независимый G2 этап остаётся guest-only synthetic CLI/CDP/DOM/storage + cleanup,
затем реальный MCP chain и отрицательные GUI/clipboard capabilities без чтения owner contents.
Скрипт этого этапа здесь не создан и Windows не запускался. Ручная Session3 не решает cold boot.
G4–G6 этим HTTP review не приняты.

````
