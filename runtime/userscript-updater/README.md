# Project Checker — development source, not a trusted Windows installation

Current route: [personal V1 plan](../../docs/userscript-updater/PLAN.md), [current handoff](../../docs/userscript-updater/HANDOFF_CURRENT_V1_20261025.md), [implementation evidence](../../docs/userscript-updater/IMPLEMENTATION_LOG.md). Full A4 scope remains. Source/Docker checks never grant owner PASS or external update authority.

## Working development Check workflow

- Persisted schema-versioned JSON registry: Unicode, last selection, file/files/folder/mixed, explicit relative mappings and check-only. Atomic save, corrupt-file preservation and concurrent editor refusal.
- Tk registration editor/pickers and shared policy editor: create, direct edit, independent copy, link/unlink/rebind. Invalid effective configuration preserves the old pack. A successful shared edit invalidates every consumer report. Used packs must be unbound before deletion.
- Actual ESLint/Semgrep config validation: built-in/enabled rule IDs, real compile/load, safe fixtures, duplicate/conflicting/disabled/missing rules and language coverage failures.
- Explicit development-profile Check button: background snapshot -> captured effective policy -> real pinned CLI -> file/rule findings -> fresh source/policy/tool comparison -> local report. Target/state/policy/app/tool intersections are refused before Check starts, so evidence cannot alter a registered target tree. Default GUI has no enabled Check without a profile. **Development profiles cannot enable Update.**
- Progress, bounded job/analyzer timeout, cancel and child-tree cleanup; stale callbacks and double-starts refused. POSIX cleanup has actual child-process tests. Windows Job Object containment source has NOT been native-tested.
- File findings include original source names, rule IDs and line/column. File coverage distinguishes clean files, findings, missing engines and unsupported material. Loaded-rule lists are separate and do not pretend to prove every rule ran on every file.
- Raw CLI JSON/stderr, snapshot manifest, hashes and structured report are saved only in job-owned development state. They are historical evidence, not transferable authorization.
- Read-only target preview: full create/modify/delete/unchanged/preserve, text diff, binary sizes/hashes, bound project/registration/snapshot/policy/tool/target/managed set and job identity. Confirmation/apply/result/history/inverse-preview/recovery run through background workers.
  Only an independently accepted installed Windows context supplies a native writer.
- Windows structural path preflight always requires separate native final-path/ACL/route verification.

V1-3 includes managed ownership, staged checked bytes, journal/readback, exact
one-shot consent and reviewed rollback/conflict recovery.
[Promotion contract](../../docs/userscript-updater/PROMOTION_CORE.md).

Selections declare code/dependency/resource/data and exact directory-relative
exclusions. Empty source directories are inventoried and created; missing selected
files/folders become visible deletion candidates only for prior managed paths.
Unavailable source roots and access errors remain errors. Resource bytes are
hashed but never reported as analyzed code; unsupported code blocks updating.

WindowsIO/InstalledAuthority/WindowsTarget are **source candidates, WINDOWS_NOT_RUN**.
The development GUI has no native authority. Offline package contents, side-by-side
installer, native probes, owner-operated GUI fixture and elevated acceptance/rollback
are in [release/WINDOWS_ACCEPTANCE.md](release/WINDOWS_ACCEPTANCE.md). The normal
launcher uses isolated Python/explicit ._pth, protected complete closure/receipts,
normal owner identity, native ACL/final-path checks and approved roots.

Exact executed tests, failures/fixes and package receipt belong only to the
[implementation log](../../docs/userscript-updater/IMPLEMENTATION_LOG.md).
Neither Docker tests nor ZIP hashes are Windows acceptance. The old devtools
transaction lab is not imported or installed as a writer.

## Run in the authorized Docker environment

Python 3.11 + pinned PyYAML 6.0.3 from requirements.txt. Existing tools: ESLint 10.13.0 and Semgrep CE 1.182.1 under /workspace/repo/project-checker-devtools. Use the existing venv Python, which includes PyYAML:

```bash
cd /workspace/repos/tunnel/runtime/userscript-updater
export UPDATER_DEV_ESLINT=/workspace/repo/project-checker-devtools/node_modules/eslint/bin/eslint.js
export UPDATER_DEV_ESLINT_CONFIG=/workspace/repo/project-checker-devtools/eslint.config.cjs
export UPDATER_DEV_SEMGREP=/workspace/repo/project-checker-devtools/semgrep-venv/bin/semgrep
export UPDATER_DEV_SEMGREP_CONFIG=/workspace/repo/project-checker-devtools/semgrep-rules.yaml
PYTHONDONTWRITEBYTECODE=1 /workspace/repo/project-checker-devtools/semgrep-venv/bin/python -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python3 -m checker.gui --model-smoke
```

[Development profile format and UI workflow](../../docs/userscript-updater/DEVELOPMENT_CHECK_WORKFLOW.md). With Tk and an appropriate test display:

```bash
python -m checker.gui --registry /absolute/path/projects.json --development-settings /absolute/path/development.json
```

Omitting --registry uses an explicitly labelled in-memory session. Omitting --development-settings disables scanner and policy-edit actions. A corrupt registry/profile is reported, not silently replaced. An interrupted-save .lock requires review.

Baseline Docker Python still has no Tk. The existing isolated QA-only Debian
Tk/Xvfb tree runs devtools/gui_workflow_smoke.py with real CLIs and widgets.
Chooser/message-box results are injected; Windows dialogs/rendering and native
writes require the separate owner-run probes. No system/Windows installation
was performed by the agent.

## Build the offline candidate inside Docker

release/build_bundle.py requires the complete pinned Windows wheelhouse,
download receipts for the official Python installer and Node archive, plus
the installed ESLint npm closure/package-lock. It verifies wheel pins/internal
RECORDs, exact lock completeness, archive paths and binary hashes. It copies
checker into the application import path; QA fixture writers remain separate.
See the implementation log for the current local bundle/summary paths.

The owner manually installs a reviewed candidate outside all agent write routes
and executes the prepared native/GUI/marker probes before accepting it.
[Windows boundary](../../docs/userscript-updater/WINDOWS_TRUST_BOUNDARY.md).
Current capability/scale/metadata/root limitations are explicit in the release
procedure; no silent skip or global atomicity claim is made.
