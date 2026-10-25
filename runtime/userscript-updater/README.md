# Project Checker — development source, not a trusted Windows installation

Current route: [personal V1 plan](../../docs/userscript-updater/PLAN.md), [current handoff](../../docs/userscript-updater/HANDOFF_CURRENT_V1_20261025.md), [implementation evidence](../../docs/userscript-updater/IMPLEMENTATION_LOG.md). Full A4 scope remains. Source/Docker checks never grant owner PASS or external update authority.

## Working development Check workflow

- Persisted schema-versioned JSON registry: Unicode, last selection, file/files/folder/mixed, explicit relative mappings and check-only. Atomic save, corrupt-file preservation and concurrent editor refusal.
- Tk registration editor/pickers and shared policy editor: create, direct edit, independent copy, link/unlink/rebind. Invalid effective configuration preserves the old pack. A successful shared edit invalidates every consumer report. Used packs must be unbound before deletion.
- Actual ESLint/Semgrep config validation: built-in/enabled rule IDs, real compile/load, safe fixtures, duplicate/conflicting/disabled/missing rules and language coverage failures.
- Explicit development-profile Check button: background snapshot -> captured effective policy -> real pinned CLI -> file/rule findings -> fresh source/policy/tool comparison -> local report. Target/state/policy/app/tool intersections are refused before Check starts, so evidence cannot alter a registered target tree. Default GUI has no enabled Check without a profile. **Update always remains disabled.**
- Progress, bounded job/analyzer timeout, cancel and child-tree cleanup; stale callbacks and double-starts refused. POSIX cleanup has actual child-process tests. Windows Job Object containment source has NOT been native-tested.
- File findings include original source names, rule IDs and line/column. File coverage distinguishes clean files, findings, missing engines and unsupported material. Loaded-rule lists are separate and do not pretend to prove every rule ran on every file.
- Raw CLI JSON/stderr, snapshot manifest, hashes and structured report are saved only in job-owned development state. They are historical evidence, not transferable authorization.
- Read-only target preview: full create/modify/delete/unchanged/preserve, text diff, binary sizes/hashes, bound project/registration/snapshot/policy/tool/target/managed set and job identity. The new promotion core requires a separately verified mutation backend; none is supplied to the GUI.
- Windows structural path preflight always requires separate native final-path/ACL/route verification.

V1-3 adds promotion.py/promotion_state.py: persistent managed ownership, exact one-shot confirmations, staged bytes/backups/write-ahead journal/readback/recovery and reviewed rollback. GUI preview/first-import stay read-only; no native mutation backend/issuer exists. [Contract and remaining scope](../../docs/userscript-updater/PROMOTION_CORE.md).

A separate synthetic transaction lab under devtools/fixture_transactions.py is **not imported by the app** and is never an installed updater.

Latest verification: **161/161 Python tests, zero skips**, with both actual CLIs; separate actual Tk widget workflow **10/10 PASS**. Native Windows GUI/Job Object/ACL tests NOT_RUN.

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

Baseline Docker Python still has no Tk. An isolated QA-only Debian Tk 8.6/Xvfb tree was extracted inside the internal volume to run devtools/gui_workflow_smoke.py. Ten actual widget scenarios passed, including real CLI jobs and save/restart. File chooser results/message boxes are injected; native Windows dialogs and visual appearance remain untested. No system Tk/Windows installation was performed.

## Remaining release gates

No owner PASS or native production promotion, protected Windows app, full pinned dependency closure or accepted production policy exists. Main entry-point/config/Node hashes do not pin transitive modules. Current validation fixtures cover ESLint JS/CJS/MJS and Semgrep JS/Python; unsupported required material is explicitly non-clear. Config validity is not semantic policy sufficiency.

Linux path checks/O_NOFOLLOW and Windows Job Object source do not prove native secure handles, reparse/races, ACL/alternate write-route isolation, process/environment compatibility or crash durability. Portable managed-scope and staged-byte transaction/recovery now exist. Native source/state/target handles/issuer, empty-folder/delete-only/resource/data/dependency contracts, confirmation/recovery UI and Windows GUI/consumer acceptance remain V1-3/V1-4 work. [Windows trust boundary](../../docs/userscript-updater/WINDOWS_TRUST_BOUNDARY.md).

The external Update button is disabled for every status. Neither scanner exit0, VALIDATED_DEVELOPMENT, NOT_AUTHORIZED, JSON evidence, metadata freshness nor test fixture results can enable it. Cheap metadata checks only prevent late presentation of changed tool inputs; a future promotion must independently rehash and validate the entire protected chain.
