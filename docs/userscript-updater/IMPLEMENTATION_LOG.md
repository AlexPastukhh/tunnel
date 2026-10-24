# Project Checker — implementation log and evidence

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
