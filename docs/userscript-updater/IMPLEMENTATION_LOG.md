# Project Checker — implementation log and evidence

## 25 October 2026 — personal V1 source candidate, complete GUI and offline Windows package

User asked to finish the developer's part, then resumed after a disconnected
session. Completed source scope: empty directories; explicit
code/dependency/resource/data/exclusions; resource-only and delete-only checks;
missing selected file/folder tombstones, while unavailable source roots/access
errors remain errors. Missing source never adopts/deletes unmanaged target
files; reappearance invalidates review. Old target directories stay explicitly
preserved; created empty dirs have identity-checked rollback.

GUI now provides exact confirmation/apply worker, result, transaction history,
inverse hashes/sizes/diff, reviewed rollback and interrupted recovery. Default
unknown/partial bytes block recovery. A separate conflict preview/consent binds
observed bytes and preserves them as an additional checked backup before restore.
Input/identity/metadata drift and consumed confirmations refuse. Analyzer
commands are bounded in UTF-16 batches for Windows command-line limits; all
expected/scanned files and late findings are merged, without weakening coverage.

Native source candidate: Windows pinned ancestors/final paths/file IDs,
single-link/reparse/ADS refusal, held-handle source/snapshot reads and target
CAS/write/delete, recoverable file security/timestamps/attributes, pinned state
parents. Existing writes preserve object identity and DACL; they are journaled
writes, not atomic file replacement. Native race/sharing/metadata and power-loss
behaviour are NOT established by Docker tests.

Installed context candidate verifies isolated interpreter/._pth, normal owner
SID, protected full application/tool/module closure, ACLs, immutable native/GUI
receipts, declared route/probe matrix, unchanged markers and approved roots.
Declared writable Windows system-dependency routes also refuse. This is owner
attestation of observed external routes, not discovery of omitted services.
Development JSON/exit0/report cannot construct the native writer. QA writers
remain outside checker/import path and private-fixture-only.

Prepared offline side-by-side install, owner native probes (handles,
junction/hardlink/ADS, sharing, metadata, real clean/violation analyzers, startup/
config canaries, transaction/interruption and Job Object cleanup), interactive
native GUI fixture with actual event receipt, elevated acceptance and installation
rollback. These scripts were NOT run on Windows. No installed receipt was issued.

Executed Docker evidence:
- Full suite: **184/184 PASS, zero skips**, actual ESLint 10.13.0 and Semgrep CE
  1.182.1 enabled; /workspace/repo/project-checker-devtools/v1-release-tests.log.
  Includes actual batched scans in both engines with the finding in the last
  batch, actual Semgrep console-entry clean/violation checks, mixed promotion/
  rollback and resource-only/delete-only continuation in private fixtures.
- Actual Linux Tk/Xvfb: **12/12 PASS**;
  /workspace/repo/project-checker-devtools/v1-release-gui.log. Real widgets/CLI,
  consent cancel/apply/readback/result/history/inverse-preview/rollback.
  Chooser/message boxes injected; Windows rendering/dialogs/native writer NOT_RUN.
- Both PowerShell scripts: PARSE PASS with official PowerShell 7.4.6 parser in
  isolated Docker directory; /workspace/repo/project-checker-devtools/v1-release-powershell.log.
  No script execution/Windows ACL/install is inferred from parse. Parser tarball
  matched upstream hashes.sha256; extraction handled old Python's missing filter,
  and invariant globalization avoided a missing ICU dependency. No OS install.
- Downloaded complete **68-wheel Windows CPython 3.13 closure**, Python 3.13.17
  x64 installer with Tk, Node 22.23.3 x64; uv hash lock, selected-artifact SHA-256,
  wheel internal RECORD and exact package-set validation. Node archive matched
  official SHASUMS256.txt. Python Authenticode verification is prepared for owner
  Windows install, not claimed executed here. ESLint npm closure/package-lock is
  included. Committed binary/npm locks now bind the exact artifacts. Fresh
  npm ci installed 77 packages with scripts/audit/fund disabled; a second empty
  directory successfully replayed the canonical tarballs offline
  (/workspace/repo/project-checker-devtools/v1-npm-closure.log). The installer
  repeats this integrity-checked offline replay, rather than copying a mutable
  expanded Docker tree. Separate empty user/global npm configs fixed the first
  helper's double-loading rejection.
- One parallel package attempt produced no completion receipt under Docker's
  1 GiB limit. Builder now streams wheel member hashes and ZIP contents.
  Serialized full validation passed, including all wheel RECORDs and the
  canonical npm cache; /workspace/repo/project-checker-devtools/v1-final-package-validation.log.
  That validation archive is not the final delivery: rebuild from the scoped
  source commit follows below.
- Final native-only refinements pin the Windows child's pywin32 DLL directory,
  sanitize/pin Tcl/Tk startup before GUI imports, verify the installed context
  before loading tkinter, and read back the restored security descriptor.
  These branches remain WINDOWS_NOT_RUN. Re-ran six release/console/batch
  regressions on Linux after the console bridge change: PASS.

### Frozen candidate delivery receipt

Source commit: **619266036a40a6d11f2c41ad5bba68af079da395**.
Final archive in the connected Repo:
**/workspace/repos/tunnel/runtime/userscript-updater/.artifacts/project-checker-v1-candidate-20261025.zip**.

SHA-256: **ecb89592bb8a6abad0f36383c838d7802d5b95edf4589404a87e05858720acad**.
Size: **147,549,114 bytes**. Sidecars in that same directory:
package-summary.json, verification-receipt.json and ZIP.sha256.

Verified the outer archive hash, exact member set, every manifest member's
hash/size, absence of Windows case collisions and own fixture-writer folders,
and exact bytes of all **43 packaged source files** against the source commit.
The bundle manifest accounts for **269 files**. Complete dependency inventory
and offline replay evidence are described above. No snapshots/test payloads or
devtools/test writer were put in the application import tree.

The final source also passed AST/doc-link checks and index/commit byte
comparison; git diff --check passed. Full regression evidence is the release
logs above; six focused release/console/batch regressions were rerun after
the final bridge change, log v1-release-focused.log, PASS. PowerShell parse is
syntax evidence, not Windows execution.

Developer source/Docker/packaging work for this candidate is ready for owner
manual acceptance. **WINDOWS_NOT_RUN / OWNER_ACCEPTANCE_PENDING** remains
explicit in the package. Copy the reviewed ZIP out of all agent write routes,
verify this SHA-256 and follow
[russian owner procedure](../../runtime/userscript-updater/release/WINDOWS_ACCEPTANCE.md).
Run the prepared probes; native FAIL returns to development. No need for the
owner to implement missing source features. No push or Windows deployment ran.

Observed failures kept in history: first expanded suite 167 tests had two old
empty-directory assertions; next 172 had incomplete fake-widget setup and an
obsolete source-label assertion; 178 had a doubly escaped binary fixture
expectation. Corrected tests/fixtures and strengthened behaviour checks. Actual
Semgrep wheel inspection found python -m semgrep exits 2; switched to its official
console entry point, then exercised it on safe real scans. Initial pip cache ran
out of its filesystem space; used existing authorized internal-volume cache.
No foreign files/processes were removed. Connection timeouts/session termination
were followed by read-back; the installer write had not landed and was then
performed once after reconnect.

Native/route/installed walkthrough/consumer acceptance remains pending. No real
Windows copy/ACL/mount/Loader/host runtime was changed, no Tunnel restart, no push.
Parallel documentation commits were preserved; current AGENTS/DRY protocol was
re-read. Procedure changed only in the existing INSTRUCTIONS pointer. Exact
milestones remain here, not replicated into common status pages.

---

## 25 October 2026 — V1-3 portable transaction core and actual-target preview

Implemented checker/promotion.py and promotion_state.py independently of the old devtools laboratory. Review binds an in-memory CheckResult to current registration/snapshot/source bytes, captured mutable packs, full tool/config/Node hashes, managed-state token, actual target inventory and exact full plan. Confirmations are one-shot and invalidated by new review/input drift. Default service has no mutation backend and refuses apply even with a valid acknowledgement; GUI Update/native_update_available remain disabled.

Managed entries are per project + target root; overlapping claims are refused, disjoint projects can share a root. First import explicitly adopts only mapped existing files, never pretends they were previous-managed deletion scope. Missing vs existing empty target root binds preview; case-only renames and hidden ancestor creation are refused. Staging uses snapshot bytes; every buffer is hash/size checked immediately before backend write. Backups/write-ahead intent/readback and final full tree/source/policy/tool checks precede managed commit/COMPLETED. No target write backend is shipped to the GUI.

Persistent recovery handles PREPARING/PREPARED/APPLYING gaps, exact pre/post-image comparison, backup/stage tampering, owner edits, scoped ownership restoration and repeat recovery. An explicit rollback review binds current journal/target/state. Unknown changed touched files block recovery; other files/projects survive. Known created empty directories require matching identity before removal, never recursive target cleanup. Interrupted mkdir with no durable ownership record can leave a preserved empty directory and honest external-drift status. Native Windows crash/ACL/metadata semantics are NOT proven by portable fsync/lock calls.

Evidence: final full suite **161/161 PASS, zero skips**, actual ESLint 10.13.0/Semgrep CE 1.182.1 enabled, log /workspace/repo/project-checker-devtools/v1-3-final-tests.log. Twenty transaction unit tests use explicitly synthetic scan receipts and tests/promotion_support.py, which is outside checker and limited to private TemporaryDirectory. A separate actual-CLI test performs folder+file/mixed Check -> exact review -> apply, second Check -> managed modify/delete -> reviewed rollback; owner binary data survives, aggregate stays NOT_AUTHORIZED and mutation scope is SYNTHETIC_TEST. Crash gap tests inject an interruption after replacement before journal completion; they are not a native OS power-loss proof.

GUI worker now builds full read-only preview/first-import from current cached Check, shows all effects/adoption/root creation, clears stale preview and preserves Update-disabled. Actual Tk/Xvfb workflow **10/10 PASS**, including two new real-widget preview/adoption flows with unchanged target bytes; log /workspace/repo/project-checker-devtools/v1-3-gui.log. File chooser/message-box results are injected; Windows dialogs/visual/native writer NOT_RUN. Existing isolated QA runtime reused, no new system/Windows installs. Temporary Xvfb process stopped by its runner.

During work Docker cgroup pids reached 256/256 due unrelated active processes; no other task/process was stopped and no limit/Tunnel was changed. Continued non-forking source/model work, then ran actual analyzer/GUI tests once capacity was free. Transient MCP read errors were retried without replaying unknown mutations.

V1-3 remains IN_PROGRESS: native source/snapshot/state/target backend + authority issuer, empty-source/source-empty-dir and explicit resource/exclusion/dependency/data contracts, confirmation/recovery UI and native locks/race/metadata/durability gates remain part of full A4. Next owner manual steps wait for a concrete reviewed Windows package, not required now. No real Windows target, ACL, Loader, application deployment or push; parallel agent-workflow changes excluded.

---

## 25 October 2026 — V1-2 functional development Check and shared-pack UI

Implemented jobs.py/settings.py/processes.py/process_gate.py, policy_service.py/policy_editor.py and GUI integration. An explicit development profile enables background static Check; default GUI stays disabled without tools/profile, Update always disabled. Worker captures immutable registration/packs, builds snapshot/generated configs, uses real validated ESLint/Semgrep with no project discovery/inline suppression/autofix, compares current source/policy/tool bytes, and saves local raw JSON/stderr plus structured report. UI presents original source paths, rule IDs/locations, per-file coverage, enabled loaded rules and snapshot/policy/tool references. Findings in one file no longer mark unrelated scanned files as finding-bearing. Missing/unsupported coverage remains non-clear (an unknown file can make aggregate INCOMPLETE with individual UNSUPPORTED).

Shared policy create/direct edit/copy validates before writing, including every affected composition; failure preserves old bytes. Link/unlink/rebind persist through registry; successful direct edit invalidates every consumer report. Used packs cannot be deleted until re-bound. Exclusive policy edit lock, duplicate JSON keys/size limits and linked-storage refusal are enforced in this development implementation. Cancel/retry/double-start/stale callback and changed registration/policy are handled without restoring prior reports; GUI close waits for child cleanup. Cheap tool metadata checks are used ONLY for late presentation invalidation; full hash checks run off the UI thread, and future promotion must independently rehash all inputs.

Process control uses bounded output/deadline and cancellation with actual POSIX process-group child cleanup. Windows Job Object/isolated-gate source is added, but native Windows compatibility, environment/tool closure and cleanup remain NOT_RUN. No trusted Windows PASS or target writer exists. Pack editors and scanner jobs are development-only until independent installation/route acceptance.

Observed regressions: target/state overlap was initially accepted; a failing regression now proves rejection before any background job/write, preserving the Check-does-not-change-target contract. App/tool/policy/state target overlaps are refused; Python child bytecode writes are disabled. A malformed development profile initially produced AttributeError; regression reproduced it, then strict profile validation converted it to ContractError/disabled Check. Actual CLI negative examples, findings locations, source edit after capture, common-pack edit mid-job, independent copy, conflicting consumer, missing engine, unknown file, deadline, cancellation and persisted-registry restart all tested. **Final full Python suite: 140/140 PASS, zero skips**, actual ESLint 10.13.0/Semgrep CE 1.182.1/PyYAML 6.0.3; log /workspace/repo/project-checker-devtools/v1-2-acceptance-tests.log. Source AST/model checks also pass.

Actual Tk widget QA: Debian Tk 8.6/Xvfb and dependencies downloaded with apt --download-only, extracted only under Docker internal QA volume. Base Python/system packages were not installed/upgraded. A separate QA Xvfb copy relocates its compiled xkbcomp path to /tmp/xqa; no system binary changed, the virtual server was stopped after the run. **8/8 actual widget scenarios PASS** via devtools/gui_workflow_smoke.py: validated pack creation, multiple/mixed source editor and picker Cancel, real async Check/heartbeat/detail tables, invalid/valid direct edit and invalidation, copy/rebind/delete unused, save→restart→restore→real Check, finding locations and GUI Cancel. File chooser results/message boxes injected; not native Windows dialog/visual/consumer acceptance. QA logs: /workspace/repo/project-checker-devtools/tk-qa/gui-smoke.log and xvfb.log.

V1-2 development source/user Check path is implemented and Docker/widget-tested; native Windows gate remains open. Next coding step V1-3 exact protected review/confirmation/promotion, preserving full A4 and later owner-run V1-4. No production promoter imported from the synthetic lab. Windows installs/ACL/Loader/actual external copies not changed; no push or shared Tunnel restart. Other agents' docs/agent-workflow work/commits were observed and preserved.

---

## 25 October 2026 — V1-2 started: persisted registrations and picker/editor source

After completing V1-1 in 30d18b5, implemented checker/registry.py and registration_editor.py and connected them to the desktop GUI. Registry schema_version=1 stores all registrations/mappings and last selection, preserving Unicode and check-only. New/edit controls use file-multiple/directory/target pickers and explicit per-selection relative mappings; picker/editor Cancel never saves partial data. Optional --registry absolute-path enables persistence; without it the UI clearly labels the in-memory session. Invalid/corrupt/version-mismatched JSON is reported and write actions are blocked, preserving the original file. Atomic temp+fsync+replace, optimistic content token and exclusive save lock reject stale concurrent editors; failed saves keep both prior disk and presentation state. An interrupted-save lock requires explicit review; no claim of Windows crash durability/ACL/secure handles.

Evidence: 123/123 Python tests PASS without skips with actual Docker ESLint 10.13.0 and Semgrep CE 1.182.1, including 8 new registry roundtrip/corrupt/conflict/disk-failure/cancel/mixed tests, plus checker AST and GUI-model smoke. Full log: /workspace/repo/project-checker-devtools/v1-2-registry-tests.log. Tkinter/native Windows visual picker QA NOT_RUN. The two main Check/Update buttons remain disabled; this is a completed source slice of V1-2, not its full gate.

Next V1-2 slice: shared pack editor/copy/bind UI with real validation and invalidation, followed by bounded asynchronous real Check worker, progress/cancel/stale protection, detailed file/rule findings/evidence. No more transaction-lab work before this user path. Full A4 scope retained; no Windows install/ACL/Loader/actual external target, other workstream or push changes.

---

## 25 October 2026 — V1-1 regression fixes (Docker only)

Baseline Git/index were clean at a44c31d; 95/95 tests passed with real ESLint 10.13.0 and Semgrep CE 1.182.1. Two newly added regressions failed before changes: same-target cross-project preview accepted and missing binary sizes. Fixed via immutable ReviewBinding (project/registration, snapshot+manifest, captured policy, tool/config/Node references, target and managed set, unique job ID). Presenter requires an active matching context, invalidates it on edit/cancel/restart, rejects stale callbacks and validates a combined callback before caching either result. Preview fingerprints include the binding. Binary old/new byte sizes are columns, with zero distinct from absent, alongside hashes/diff/preserved files.

Added separate actual effective-config validation. ESLint loads the pinned config via its real API, enumerates built-in IDs (including disabled unknown IDs) and checks effective enabled rules on JS/CJS/MJS safe fixtures. Semgrep CE compiles actual local YAML/JSON rules, verifies loaded rule IDs and fixture coverage; invalid YAML/patterns, duplicate keys/IDs, min-version skips, missing/disabled required rules and missing tools/timeouts are errors. Captured shared packs compose deterministically; conflicting rules fail before scanning. run_dev_engine now refuses invalid configs before scanning candidate bytes. PyYAML 6.0.3 installed ONLY in existing Docker development venv; requirements.txt records the dependency. Demo ESLint config now explicitly covers JS/CJS/MJS, matching supported extensions.

Evidence: 115/115 tests PASS without skips (95 baseline + 9 binding/size + 11 actual-policy cases), real clean/violation JS/Python with both CLIs, model smoke PROMOTION DISABLED. Full log: /workspace/repo/project-checker-devtools/v1-1-tests.log. Follow-up checks cover final error-message/column-width changes. No protected Windows app, native GUI/ACL/handles, full dependency closure or owner acceptance. VALIDATED_DEVELOPMENT means config compiled/loaded on fixtures; it does not prove semantic rule quality, all project coverage or authorization. The Semgrep validation fixture profile currently supports JS/Python; unsupported languages fail explicitly. ESLint builtinRules is a version-sensitive API and unsupported versions fail closed.

V1-1 is complete; continue V1-2 with persisted registrations and usable Check workflow, not further transaction-lab expansion. Full A4 scope remains. No push, Windows install, ACL/Loader/external copy or other workstream changes.

---

## 25 October 2026 — independent next-chat handoff verification (docs only)

Reviewed new personal V1 plan against source-state/AGENTS and original user-uploaded full A4/v4. Saved the original A4/v4 **reading-copy text** as CANDIDATE_PREWORK_V4_READING_COPY.md (648 lines, 126082 UTF-8 bytes), still explicitly not canonical/BASELINE COMMITTED. Added HANDOFF_CURRENT_V1_20261025.md with user decisions, authority, file map, exact tests, defects, next V1-1 step and safety limits; legacy HANDOFF and narrow PLAN are preserved as provenance. Reran actual Docker fixtures on the current source state: ESLint 10.13.0, Semgrep CE 1.182.1, 95/95 Python tests PASS no skips; GUI model reports PROMOTION DISABLED; Windows visual/native ACL tests NOT_RUN. This was **documentation and read-only verification only**, not coding/apply/install/ACL/Loader/external target update. Parallel agent-workflow changes observed in live Git and deliberately excluded. The current PLAN remains the governing execution order; V1-1 bug fixes have not been implemented here.

---

## 25 October 2026 — planning-only re-sequencing for personal V1

User requested to update the implementation plan while preserving the original direction. The current [PLAN.md](PLAN.md) now prioritizes a complete Check GUI and reproducible local personal workflow before further generic transaction/security framework expansion. Full A4 scope remains: shared mutable packs, file/files/folder/mixed, check-only, accurate scanner coverage, explicit all-effect preview, separate confirmation, exact bytes, recovery, and independently owner-installed Windows trust chain. The previous narrow userscript plan was preserved byte-for-byte as [PLAN_LEGACY_USERSCRIPTS_20261025.md](PLAN_LEGACY_USERSCRIPTS_20261025.md). Known review issues are scheduled V1-1, not silently marked corrected: cross-project preview can be displayed with same target; schema validation is not effective engine-rule validation; binary sizes not represented in GUI. No source/runtime code, Windows install, ACL/mount, Loader or external target was modified during this planning update. Previously observed 95/95 Docker tests are evidence of an older code state only; this plan does not add acceptance evidence.

---

## 25 October 2026: Windows path preflight and Tkinter view-only source (fifth slice)

**Source:** checker/windows_layout.py reviews Windows drive-path scheme for app/tools/policies/state/approved/source/agent-write roots. Literal agent-write/source intersections and unsupported ambiguous names are blockers. Even collision-free strings return NEEDS_NATIVE_WINDOWS_VERIFICATION because this is not a native OS final-path/reparse/ACL/route probe. checker/ui_model.py stores data-only registrations, scanner and preview views, invalidates cached results across shared policy consumers; checker/gui.py implements the tabbed Tkinter presentation of projects, rule links, scan results, effects and Windows path preflight. Update/Check buttons are disabled; no scanner or updater invoked.

**Observed tests:** 95/95 Python tests PASS with live Docker ESLint 10.13.0 and Semgrep CE 1.182.1 integrations enabled and zero skips, plus separate GUI model smoke and checker-source AST parse. Python tkinter is unavailable in Docker, so no visual GUI or native host interaction tested. No owner applications, external copies, mounts, ACL, Tampermonkey or Windows installs changed. See WINDOWS_TRUST_BOUNDARY.md for future manual gates.

**Next:** native Windows secure-handle and effective-agent-route probes, independently protected executable/rules/dependency closure, trusted policy editor and scanner pipeline, user approval, installed recovery, GUI walkthrough. Source-only UI must not be interpreted as an installed app.

---

## 25 October 2026: synthetic transaction and recovery laboratory (fourth slice)

**Scope:** User continued A4 development in Fortis Repo. Added devtools/fixture_transactions.py, deliberately **outside the production checker package**, guarded to a Python TemporaryDirectory with a special synthetic-only marker. No production write/update API was created. Neither the marker nor the fingerprint equals owner authentication or scanner acceptance.

**Observed implementation:** before any synthetic write, the experiment verifies an explicitly chosen preview fingerprint, fresh source hashes/full manifest, registration identity, shared mutable policy hash, source snapshot bytes and actual target inventory. Review fingerprint now also binds the explicitly managed prior set even if some paths no longer exist. Read-only preview includes external empty directories in target inventory; empty folders are preserved, file-at-directory path collisions refused.

An operation staged reviewed snapshot bytes and preimages, checked hashes, fsynced staging/journal, and recorded PREPARED before changing any fixture target. The apply step marks APPLYING, uses staged bytes only, read-back checks, and compares the complete final destination inventory (including unmanaged files and directories). Unit tests exercise create/replace/delete/unchanged, exact backups, double apply denial, destination drift, source/policy drift, missing approval, symlink/fixture escape and tampered backup rejection. Simulated I/O failure and abrupt interruption between replacement and journal checkpoint are recovered from saved backups. An unexpected touched-file modification returns RECOVERY_BLOCKED without clobbering third-party content; a completed managed rollback with unrelated external drift returns ROLLED_BACK_WITH_EXTERNAL_DRIFT rather than claiming exact target restoration. A PREPARED-only transaction does not revert independently applied owner content.

**Evidence:** Python 3.11, real Docker ESLint 10.13.0 and Semgrep CE 1.182.1 integration tests: 74/74 PASS, zero skips, including 25 new regression/transaction tests since prior 49. Git index and other current network work were not modified by this task. All writes in this stage targeted synthetic temporary paths or this project's source/docs; no actual external user-consumed Windows copy touched, no CLI run against real projects.

**Important unresolved security gaps:** Synthetic fixture lab is not a production authorization mechanism; it does not derive any valid scanner PASS (current aggregate is always NOT_AUTHORIZED), validate host trust boundaries, prevent path TOCTOU on Windows, protect policy/rules/tools with Windows ACL, prove dependency closure, resolve target lock semantics, preserve NTFS ACL metadata, or offer owner GUI confirmation. Journal crash durability/multi-volume and external third-party concurrent writes are not solved by a Linux fixture. Real managed-set state must be independently protected, including approval staleness checks. Full planned A4 Windows application remains incomplete.

**Next:** Implement actual Windows-safe trusted snapshot/target handle design and protected registration/policy/tool chain, plus view-only GUI; only after these can production promoter/approval and recovery be enabled with manual owner install and tests. Do not copy/run devtools/fixture_transactions.py as a Windows installer.

---

## 25 October 2026: read-only external effect preview (third slice)

Added a pure READ-ONLY target preview module; it takes previously captured source snapshot, an explicit previously-managed path set, and a synthetic destination root. No promotion/approval API exists. Previews specify file creates/modifications/deletions/unchanged, text unified diffs when bounded UTF-8 is available, binary hashes/sizes when not, and unmodified target-only paths. Previously managed paths removed from candidate are proposed for deletion and shown; target-only files are preserved. A new mapping colliding with existing unmanaged data is refused pending explicit first-import/adoption decision. It rejects target symlinks/hardlinks and file/directory collisions in this Linux prototype; actual Windows handle-based verification remains future work.

Preview output includes full target content inventory SHA-256 and plan fingerprint, both changing when actual target changes. Those tokens are for future approval binding and have **no authorization semantics** now. The source-snapshot/current-source comparison, installed policy/tool binding, owner-controlled approval, backup/journal/restore and actual file operations must be independently implemented and verified before any external update.

Verification: 49/49 unit and synthetic/CLI integration tests PASS (no skips with ESLint and Semgrep environment variables). Nine added negative and positive cases include unmanaged data preservation, source-deleted previously-managed file, changed target fingerprint, path collision and read-only behaviour. Windows owner targets, Loader, installed app and ACLs not modified.

---

## 25 October 2026: actual Semgrep and per-file coverage (second slice)

**Live Docker tools:** ESLint 10.13.0 and Semgrep Community Edition 1.182.1. Existing ESLint is under /workspace/repo/project-checker-devtools/node_modules, while Semgrep is in the isolated Python 3.11 environment /workspace/repo/project-checker-devtools/semgrep-venv. Neither is a trusted Windows installation.

**Installation evidence:** system Python lacks pip/ensurepip. Verified PyPI uv 0.13.5 wheel by published SHA-256 fa8d26e08e34c29c0c4e820cf3181757086d547240b4f4d31ff1d8bd810ca946; extracted only inside Docker. First Semgrep installation failed ENOSPC because uv used the 128 MiB /home/node tmpfs for extraction; retry used UV_CACHE_DIR and TMPDIR under internal Docker volume and installed Semgrep 1.182.1 plus dependencies. Confirmed semgrep --version output 1.182.1. No host/system Python changes.

**Implementation and evidence:** Semgrep ran real synthetic JavaScript and Python under two local demo rules and reported actual Python eval finding and scanned paths. Clean Python reported STRUCTURAL_CLEAR, and the aggregate remained NOT_AUTHORIZED. ESLint integration also rerun. Parser accepts optional paths.skipped per published output schema while treating actual skips/errors/invalid reports as non-clear; ESLint suppressed findings now fail closed. Added per-file matrix for required engines, actual scans, unsupported file types, missing/foreign results. Tracked demo policies under runtime/userscript-updater/policies/demo; their SHA-256 matches the dev-tool copies.

**Verification:** 40/40 Python tests PASS with both real CLI integration tests enabled, no skips. Scope is synthetic Linux Docker fixtures ONLY. No production policy for Notifier/Helper accepted; no complete analyzer dependency pinning; no trusted Windows installation, external target/approval, or consumer acceptance.

**Next gates:** independent trusted policy/rule language coverage; pinned full tools/dependencies; secure Windows source and snapshot path handling; actual external target preview, confirmation, backup and recovery; finished GUI. The broader A4 scope remains unchanged.

---

## 25 October 2026: first source slice and review

User permitted development, dependencies, builds and synthetic tests inside Fortis Repo Docker. Owner will separately install verified app/tools/policies/targets outside agent-write mounts. No agent Windows install, ACL/mount, browser Loader or production target changes.

Initial source commit 24b5234 introduced 8-test registration/inventory skeleton. Critical code review exposed silent os.walk errors, insufficient target collision checks, ambiguous Windows device names, suffix loss (.bin), source inventory changes during snapshot and lack of analyzer coverage truthfulness.

Remediation: walk errors and empty subdirectories now fail closed; source size/number bounds, explicit hardlink and link refusals; extension-preserving snapshot; pre/open/post file checks and second full manifest comparison; registration and policy fingerprint freshness; target ancestor collisions and Windows path component restrictions. Current Linux prototype is NOT race-free OS-level Windows validation.

Expanded E-01 source: shared mutable packs with copy and captured content hashes; parsers for ESLint/Semgrep JSON with coverage, skipped, findings, errors and exit codes; demo-only pinned-file CLI runner without shell/config lookup/inline suppressions/autofix. Parsed clear reports cannot grant approval; aggregate status remains NOT_AUTHORIZED.

Evidence: Python 3.11, 30/30 tests with optional real ESLint integration enabled; actual Docker-only ESLint v10.13.0 via npm install --ignore-scripts under /workspace/repo/project-checker-devtools, synthetic safe JS exit0 structural clear; eval snippet exit1 finding. Semgrep is not installed and its adapter is only synthetic JSON tested.

Open gates:
1. Actual Semgrep CLI fixture/versions and trustworthy file/rule/language coverage; pinned complete dependency closure and independent installed tool chain.
2. Handle-based Windows source/snapshot trust, no-follow/aliases/reparse paths, ACL, source/target isolation, import route tests.
3. Installed-protected rule pack persistence and concurrency, analyzer run ownership, snapshot/policy/tool/target binding.
4. Full preview of actual create/modify/delete/preserved extras, explicit approval, staging/readback/backup/journal/recovery.
5. Windows UI, manual installation, actual owner/consumer acceptance and safety/coverage limitations.

No protected external bytes were created/changed; no Windows or Tampermonkey operations; no release claim. Other agent-workflow, Notifier and Helper files were not part of this implementation.
