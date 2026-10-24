# Project Checker — implementation log and evidence

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
