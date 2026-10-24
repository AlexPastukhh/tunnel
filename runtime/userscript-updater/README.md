# Project Checker — development source, NOT a trusted Windows installation

Scope: full Windows checker and controlled external promotion per CPW-PC-20261025/v4 (A4). All current code is agent-writeable and development-only. User will later manually install independent verified app, rules, tools and targets outside agent-write routes.

## Implemented, source-only

- File/directory/mixed registration, check-only and target mappings, conservative path validation.
- Fail-closed source inventory, hardlink/reparse refusal, size/count bounds, SHA-256, source rehash/re-enumeration, extension-preserving snapshot.
- Mutable shared policy packs, clone/independent copy, content hashing and captured pack fingerprints.
- ESLint and Semgrep machine-readable report parsers. Missing files, findings, errors and skipped rules/files cannot become CLEAR. Even structurally clear report results in aggregate NOT_AUTHORIZED.
- Demo-only CLI launcher: fixed argv, no shell, no project configs, no inline ESLint disable, no autofix, Semgrep nosem/git/metrics safeguards and bounded timeout.
- Per-file coverage matrix: required scanners, actual scanned files, unsupported extensions and missing reports. Rule-to-language applicability still requires trusted-policy validation.
- 40 Python tests including actual ESLint 10.13.0 and Semgrep CE 1.182.1 integration against isolated synthetic JS/Python. Clean inputs -> STRUCTURAL_CLEAR; eval examples -> FINDINGS. Aggregate clean status is always NOT_AUTHORIZED.

To run tests inside Repo:

    cd /workspace/repos/tunnel/runtime/userscript-updater
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v

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

To run all 40 tests, configure the installed Docker CLI paths (unset env vars result in explicit integration-test skips):

    export UPDATER_DEV_ESLINT=/workspace/repo/project-checker-devtools/node_modules/eslint/bin/eslint.js
    export UPDATER_DEV_ESLINT_CONFIG=/workspace/repo/project-checker-devtools/eslint.config.cjs
    export UPDATER_DEV_SEMGREP=/workspace/repo/project-checker-devtools/semgrep-venv/bin/semgrep
    export UPDATER_DEV_SEMGREP_CONFIG=/workspace/repo/project-checker-devtools/semgrep-rules.yaml
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v

## Critical remaining work

There is NO approved PASS, NO external promotion and NO trusted Windows app. Both directories in Repo/Docker are agent-writable. Main CLI byte pins do not protect transitive dependencies. Linux path pre-checks + O_NOFOLLOW where available are not proven Windows secure-handle/TOCTOU protection. No independently validated language/rule coverage, pinned full analyzer dependency closure, production rules, installed pack edit locking, source tree relative-import semantics, empty directory copying, preview/create/modify/delete/approval, target checks, backup/journal/rollback, GUI, Windows ACL/install/consumer acceptance. Unknown files cannot silently be ignored or deemed safe. The full A4 final scope is unchanged.

Never run this source as a trusted approving/installing tool or point it at real protected targets.
