# Project Checker — implementation log and evidence

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
