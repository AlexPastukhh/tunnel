# Fortis Windows launcher / Guard updates after Docker changes

Status: **transition 2026-11-01**. This document records the owner-requested workflow, not evidence that Windows Git-clone launchers have passed real reconnect acceptance.

## Source of truth

- Develop the Fortis Repo 1/2 Windows launcher source, shared Guard and Control Center UI in the existing Docker Git checkout `/workspace/repos/script-control-center`. The native Tunnel's infrastructure documentation belongs to `tunnel`, but the canonical Windows launchers are **not duplicated** here.
- Run source tests and review SHA-256 pins, then commit/push to `AlexPastukhh/script-control-center`. Windows uses a **separate Git clone**, at `%USERPROFILE%\Repos\script-control-center` (the canonical Windows mirror root is `%USERPROFILE%\Repos`, distinct from Docker `/workspace/repo/Repos`), and `git pull --ff-only origin main`; no shared writable mount between Docker and Windows.
- The Desktop `Fortis RDG Control Center` shortcut targets **`Start-ScriptCatalog.ps1`** inside that Windows Git clone. That is the standalone script catalog; `Start-ControlCenter.ps1` is the optional older four-card shell and **not** the desired Desktop entry point. Five registered worker adapters refer to their own clone's `launchers/` source. Registrations persist across `git pull`; neither registration nor pull automatically launches workers.
- Machine-local tunnel profiles, native Windows runtime, `runtime.key`, catalog runtime state, logs and personal credentials stay **out** of Git. The RDG updater is a separate external dependency; its separate promotion/deployment design remains to be completed.

## Mandatory check when changing Docker

**If the existing `fortis-repo-test` Docker image, container identity, memory, PIDs, CPU, tmpfs, mounts, network, user or security options change, review both Repo startup guards and their pins before terminating the last working MCP session.** An already running tunnel can keep working even though the next launch will fail. Container recreation may itself interrupt a tunnel: prepare recovery *before* any destructive change.

1. Read-only Docker `inspect` and map the actual differences to both Repo 1 and Repo 2 Guard/quiet-launcher assertions. Current selected contract is memory **4–8 GiB inclusive**, PIDs **256–1024 inclusive**; do not silently weaken other checks.
2. Modify the scripts in `script-control-center`, update any SHA-256 pin **only after verifying the exact new source bytes**; check the repo's `launchers/**/*.ps1 -text` Git attribute to avoid checkout hash drift.
3. Run `python3 -B test_static_catalog.py` and `python3 -B test_git_launcher_contract.py` inside Docker; review the scoped Git diff for secrets/unrelated changes, commit/push.
4. On Windows pull the reviewed revision. Run source-only WinForms compile checks and **read-only** `launchers/chatgpt-repo-mode/run-tunnel-quiet-logs.ps1 -Mode Preview` and `launchers/FortisRepoPlus2/Repo2DirectGuard.ps1 -Mode Preview` directly from the Windows clone. Verify source hashes and file paths. `Preview=PASS` is necessary but not proof that MCP transport can reconnect.
5. In an owner-controlled maintenance window, confirm a working reconnect/recovery path before deliberately stopping any existing Repo. Never stop a live tunnel or the shared container to test only the shortcut. Leave the old Windows shortcuts/installed files intact for rollback until acceptance.

## As-built gaps on 2026-11-01

- Repo 1's **installed** quiet launcher reported `Preview=PASS` and its MCP connection was verified from ChatGPT. This does **not** verify the **new Git-cloned** launcher.
- Repo 2's installed launcher rejected the modified Guard due to an outdated SHA-256 fingerprint. A corrected pinned pair has been committed to the source repository but still requires Windows clone read-only previews and a genuine reconnect test.
- The owner has now **verified the standalone catalog UI** launches from a Windows Git-clone shortcut at `Start-ScriptCatalog.ps1`; the five built-in registrations were re-pointed to the clone with backups. This does not verify a Repo 1/2 cold-start reconnect. The corrected `script-control-center/tools/Update-Windows-ControlCenter.ps1` also targets the standalone catalog after explicit `-Apply` and successful local preflight; it is **not needed for routine pulls** and does not start workers.
- The old install snapshot was captured before the latest five resource-check changes. The canonical candidate was reconstructed from source and owner-confirmed checksums; do not treat the snapshot as a current Windows installation.
- Additional legacy scripts and the RDG updater are not all migrated into this repository yet. Do not delete their installed copies until their owner/test/cutover is settled.

See `AlexPastukhh/script-control-center/docs/GIT-WINDOWS-SOURCE-OF-TRUTH.md` for the implementation checklist. This document is procedural guidance only; the actual running runtime and checks take precedence over Markdown.
