# Project Checker — development source, NOT a trusted Windows installation

Scope: full Windows checker and controlled external promotion per CPW-PC-20261025/v4 (A4). All current code is agent-writeable and development-only. User will later manually install independent verified app, rules, tools and targets outside agent-write routes.

## Implemented, source-only

- File/directory/mixed registration, check-only and target mappings, conservative path validation.
- Fail-closed source inventory, hardlink/reparse refusal, size/count bounds, SHA-256, source rehash/re-enumeration, extension-preserving snapshot.
- Mutable shared policy packs, clone/independent copy, content hashing and captured pack fingerprints.
- ESLint and Semgrep machine-readable report parsers. Missing files, findings, errors and skipped rules/files cannot become CLEAR. Even structurally clear report results in aggregate NOT_AUTHORIZED.
- Demo-only CLI launcher: fixed argv, no shell, no project configs, no inline ESLint disable, no autofix, Semgrep nosem/git/metrics safeguards and bounded timeout.
- 30 Python tests (optional live ESLint integration); actual synthetic ESLint 10.13.0: harmless code -> STRUCTURAL_CLEAR; eval -> FINDINGS. Semgrep only synthetic parser tests, NOT installed/run.

To run tests inside Repo:

    cd /workspace/repos/tunnel/runtime/userscript-updater
    PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v

Optional local Docker volume ESLint fixture installation:

    mkdir -p /workspace/repo/project-checker-devtools
    npm install --prefix /workspace/repo/project-checker-devtools --no-audit --no-fund --ignore-scripts --save-exact eslint@10.13.0

The actual demo config file, manually created in Docker internal volume and NOT a production config, contains:

    module.exports = [{ files: ["**/*.js"], rules: { "no-eval": "error", "no-implied-eval": "error" } }];

Store it as /workspace/repo/project-checker-devtools/eslint.config.cjs.
Set UPDATER_DEV_ESLINT=/workspace/repo/project-checker-devtools/node_modules/eslint/bin/eslint.js and UPDATER_DEV_ESLINT_CONFIG=/workspace/repo/project-checker-devtools/eslint.config.cjs before running the test command; without them the integration test is skipped.

## Critical remaining work

There is NO approved PASS, NO external promotion and NO trusted Windows app. Both directories in Repo/Docker are agent-writable. Main CLI byte pins do not protect transitive dependencies. Linux path pre-checks + O_NOFOLLOW where available are not proven Windows secure-handle/TOCTOU protection. No full coverage, real Semgrep, production rules, installed pack edit locking, source tree relative-import semantics, empty directory copying, preview/create/modify/delete/approval, target checks, backup/journal/rollback, GUI, Windows ACL/install/consumer acceptance. Unknown files cannot silently be ignored or deemed safe. The full A4 final scope is unchanged.

Never run this source as a trusted approving/installing tool or point it at real protected targets.
