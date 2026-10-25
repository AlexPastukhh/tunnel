# Project Checker — development source, NOT a trusted Windows installation

**Current execution plan:** [docs/userscript-updater/PLAN.md](../../docs/userscript-updater/PLAN.md). Personal V1 remains a full local Windows app, not a demo; work proceeds as bug fixes → working Check UI/persistence/shared rules → reviewed promotion and recovery → owner-run trusted Windows acceptance. V1-1 fixes are source/DOCKER_TESTED; V1-2 Check workflow is next.

Scope: full Windows checker and controlled external promotion per CPW-PC-20261025/v4 (A4). All current code is agent-writeable and development-only. User will later manually install independent verified app, rules, tools and targets outside agent-write routes.

## Implemented, source-only

- File/directory/mixed registration, check-only and target mappings, conservative path validation.
- Fail-closed source inventory, hardlink/reparse refusal, size/count bounds, SHA-256, source rehash/re-enumeration, extension-preserving snapshot.
- Mutable shared policy packs, clone/independent copy, content hashing and captured pack fingerprints. Separate actual effective-config validator compiles real ESLint/Semgrep rules on safe fixtures, checks loaded/enabled required IDs, rejects invalid/disabled/missing/conflicting configurations before development scan. Validation is not semantic policy acceptance.
- Immutable ReviewBinding binds presenter callbacks to project, registration, snapshot manifest, captured policy, tools/config/Node references, target and managed set plus unique job; edit/cancel/new job invalidates it. UI shows binary old/new byte sizes, hashes and text diffs.
- ESLint and Semgrep machine-readable report parsers. Missing files, findings, errors and skipped rules/files cannot become CLEAR. Even structurally clear report results in aggregate NOT_AUTHORIZED.
- Demo-only CLI launcher: fixed argv, no shell, no project configs, no inline ESLint disable, no autofix, Semgrep nosem/git/metrics safeguards and bounded timeout.
- Per-file coverage matrix: required scanners, actual scanned files, unsupported extensions and missing reports. Rule-to-language applicability still requires trusted-policy validation.
- Read-only target preview builder (synthetic trees only): create/modify/delete/unchanged, UTF-8 text diffs, binary hashes/sizes, preserved unmanaged files/empty directories, target inventory fingerprint AND previously-managed-scope fingerprint, collision refusal.
- A SEPARATE TEST-ONLY LAB under devtools/fixture_transactions.py (NOT the checker installable package). It requires a temporary canary-marked fixture directory and simulates reviewed-plan fingerprint matching, fresh source/pack/target checks, exact checked-byte staging, backups, durable JSON journal, idempotent status, injected failure/crash, selective rollback, manual recovery, and explicit residual-drift status when unrelated owner files changed. This is a synthetic, nonsecure model, not an approving/updating Windows API.
- Windows structural deployment preflight (checker/windows_layout.py): checks for obvious trusted-root/agent-write/source overlap, rejects ambiguous string paths, and ALWAYS returns NEEDS_NATIVE_WINDOWS_VERIFICATION even with separated paths. It never claims OS ACL/alias verification.
- Presentation state (checker/ui_model.py) and Tkinter Windows desktop prototype (checker/gui.py) with project registration JSON import, project/rule listings, report and preview views, file-level diff details, preserved external data and installation-layout diagnostics. **Both Check and Update are disabled** pending independent trusted Windows backend. GUI has not been visually run on Windows; Docker Python lacks Tkinter.
- 115 Python tests including actual ESLint 10.13.0 and Semgrep CE 1.182.1 integration against isolated synthetic JS/Python. Clean inputs -> STRUCTURAL_CLEAR; eval examples -> FINDINGS. Aggregate clean status is always NOT_AUTHORIZED.

Dependency: PyYAML==6.0.3 (requirements.txt), installed in the existing Docker Semgrep venv. No Windows dependency install has been done.

To run tests inside Repo:

    cd /workspace/repos/tunnel/runtime/userscript-updater
    PYTHONDONTWRITEBYTECODE=1 /workspace/repo/project-checker-devtools/semgrep-venv/bin/python -m unittest discover -s tests -v

Optional local Docker volume ESLint fixture installation:

    mkdir -p /workspace/repo/project-checker-devtools
    npm install --prefix /workspace/repo/project-checker-devtools --no-audit --no-fund --ignore-scripts --save-exact eslint@10.13.0

Demo configs are tracked under policies/demo/eslint.config.cjs and policies/demo/semgrep-rules.yaml. They are development-only, NOT production trusted policies. Their Docker-volume copies were verified byte-identical via SHA-256.

ESLint 10.13.0 was installed with npm --ignore-scripts. Semgrep CE 1.182.1 was installed with uv 0.13.5 and Python 3.11 in the Docker internal volume. The uv wheel was downloaded from PyPI and verified against the PyPI SHA-256 value fa8d26e08e34c29c0c4e820cf3181757086d547240b4f4d31ff1d8bd810ca946. Installation commands (Docker only; never run on Windows):

    UV=/workspace/repo/project-checker-devtools/uv-wheel/uv
    DEV=/workspace/repo/project-checker-devtools
    "$UV" venv --python /usr/bin/python3 "$DEV/semgrep-venv"
    UV_CACHE_DIR="$DEV/.cache-uv" TMPDIR="$DEV/.tmp-uv" "$UV" pip install --python "$DEV/semgrep-venv/bin/python" --no-build-isolation 'semgrep==1.182.1'

Copy the two development demo configs from policies/demo/ to $DEV/eslint.config.cjs and $DEV/semgrep-rules.yaml and verify hashes. Both copies are already present and checked in the active Docker volume.

To run all 115 tests, configure the installed Docker CLI paths (unset env vars result in explicit integration-test skips):

    export UPDATER_DEV_ESLINT=/workspace/repo/project-checker-devtools/node_modules/eslint/bin/eslint.js
    export UPDATER_DEV_ESLINT_CONFIG=/workspace/repo/project-checker-devtools/eslint.config.cjs
    export UPDATER_DEV_SEMGREP=/workspace/repo/project-checker-devtools/semgrep-venv/bin/semgrep
    export UPDATER_DEV_SEMGREP_CONFIG=/workspace/repo/project-checker-devtools/semgrep-rules.yaml
    PYTHONDONTWRITEBYTECODE=1 /workspace/repo/project-checker-devtools/semgrep-venv/bin/python -m unittest discover -s tests -v

## Critical remaining work

There is NO approved PASS, NO external promotion and NO trusted Windows app. Both directories in Repo/Docker are agent-writable. Main CLI byte pins do not protect transitive dependencies. Linux path pre-checks + O_NOFOLLOW where available are not proven Windows secure-handle/TOCTOU protection. Config validation is tested for ESLint JS/CJS/MJS and Semgrep JS/Python fixtures; full independent semantic rule/project coverage remains incomplete. No pinned full analyzer dependency closure, production rules, installed pack edit locking, source tree relative-import semantics, empty directory copying, trusted external target observation and owner approval, actual promotion (create/modify/delete), target-lock checks, backup/journal/rollback, fully functional GUI (current view-only source), Windows ACL/install/consumer acceptance. Unknown files cannot silently be ignored or deemed safe. The full A4 final scope is unchanged.

The preview and devtools/fixture_transactions.py are **strictly for SYNTHETIC destination trees**. The test-only fingerprint is NOT user authentication/permission, there is NO trusted scan PASS or installed authorization gate, no protected previous-managed inventory, no real Windows ACL/reparse protection, no service or UI, and NO authorization to promote any Repo bytes outside synthetic fixtures. The test transaction deliberately refuses nonfixture destinations; it is kept OUTSIDE checker/ to reduce accidental production inclusion. Synthetic OS replace, fsync, backups and journals do not prove Windows crash-atomicity or prevent concurrent writes by AI/other processes. Do not run any of this as a trusted approving/installing Windows tool. Real use requires separate independent implementation, manual installation, external authorization and negative owner-side acceptance.

## Desktop UI source-only smoke

The pure presentation smoke can run inside Fortis Repo Docker without Tkinter:

    PYTHONDONTWRITEBYTECODE=1 python3 -m checker.gui --model-smoke

On a future controlled native Windows test environment with Tkinter, checker.gui is intended to render five tabs and show imported registration JSON as **data**. That Windows visual test is NOT RUN. The two action buttons are intentionally disabled; no source code scanning or external promotion is available in this view-only GUI.

Trust boundary design and manual-acceptance gates: docs/userscript-updater/WINDOWS_TRUST_BOUNDARY.md. The synthetic transaction lab under devtools is NEVER an installed service or backend for this GUI.
