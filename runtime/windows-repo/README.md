# Repo1/Repo2 Windows Git-clone source mirror

**Status (2026-11-02): BYTE-EXACT SOURCE MIRROR + SCRIPT-CENTER DELEGATION PREPARED; WINDOWS PULL/CUTOVER AND LIVE RECONNECT NOT YET ACCEPTED.**
The `current/` directory mirrors the complete Repo1/Repo2 worker chain
from `script-control-center`, preserving its original relative layout and file
bytes. Script Center source adapters now call this exact sibling Windows tunnel
clone after validating the pinned manifest; the Windows clones have not yet
pulled this paired release and no live process has been restarted.

## Components
- `current/` — the **authoritative byte-exact mirror of the current working chain**: `Repo1-Worker.ps1`, `Repo2-Worker.ps1`, both quiet launchers, Repo1 `control.ps1`, Repo2 `Repo2DirectGuard.ps1`, and the Repo2 `Start-Fortis.ps1` / `Common.ps1` preparation chain. `current/source-manifest.json` pins all eight files.
- `Invoke-FortisRepo.ps1` — Windows Git-clone-only dispatcher. Default **Preview**; explicit `Start` requires clean `main` and typed owner confirmation, then calls the unchanged `current/Repo1-Worker.ps1` or `current/Repo2-Worker.ps1`.
- `repo1/`, `repo2/`, and root `release-manifest.json` — retained four-file direct-launcher candidate from the earlier staging attempt. **Not used by the current dispatcher and not the working chain.**
- `test_release_contract.py` — offline tests for both the retained candidate and the complete current worker mirror.
- `Preview-WindowsRepoInventory.ps1` — read-only comparison of the release hashes with known *candidate* legacy Windows file paths. It does not prove which Windows shortcut/process is currently active.
- [Defender exclusions and installed dependency inventory](DEFENDER-AND-INSTALLED-INVENTORY.md) — maps the owner's current exclusions to active Repo1/Repo2 dependencies and legacy G2 / synthetic G3 artifacts; includes the remaining Windows-only checks.

## Runtime placement: Windows host vs Docker

The tunnel has two execution sides; do not copy every Windows exclusion into Linux:

- **Windows host:** PowerShell launchers, `docker.exe`, and the Windows Tunnel Client. Repo1 and Repo2 both start the Windows `tunnel-client-runtime.exe` v0.0.15; Repo2 additionally calls `tunnel-client.exe doctor`. These EXEs are intentionally outside this Linux container and Git source. Keep their version, provenance and SHA in the dependency inventory; never treat them as Linux executables.
- **Docker/Linux:** `/usr/local/bin/node` and `/opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js`. The current container reports Node v22.23.3 and Desktop Commander 0.2.52. Both Repo launchers address these exact Linux paths through `docker exec`.
- **Windows-local state:** Repo1/Repo2 profiles, runtime keys, ACLs and logs remain on Windows. They are not missing Docker source files and must not be copied into Git or the container.
- G2 Windows Node/Desktop Commander and the two G3 synthetic fixture copies are not current Repo1/Repo2 dependencies.

The tracked Linux image recipe is `../repo-mode/Dockerfile`; its Node 22 + Desktop Commander 0.2.52 requirements match the current runtime versions. It has no npm lockfile, so a rebuild is not guaranteed to reproduce the same transitive dependency tree; the existing container/image pins remain separate runtime evidence.

The eight files under `current/` are copied **byte for byte** from the tracked
`script-control-center` worker/launcher source at revision
`001ddff9b0ece358e5cfa1b336a104c7d66bee68`; all eight SHA-256 values are
recorded in `source-manifest.json`, pinned by both the tunnel dispatcher and the
Script Center resolver, and checked offline. The Script Center root workers are
now thin adapters: they do not resolve local launcher copies. They require the
clean sibling Windows clone `%USERPROFILE%\Repos\tunnel` on `main`, verify the
manifest fingerprint and every file hash, and then call the corresponding
worker below. This preserves the actual chain:

- Repo1: `Repo1-Worker.ps1` → `run-tunnel-quiet-logs.ps1` → adjacent `control.ps1`.
- Repo2: `Repo2-Worker.ps1` → `Start-Fortis.ps1` → `Common.ps1` / Guard checks
  → `FortisRepo2-quiet-logs.ps1` → adjacent `Repo2DirectGuard.ps1`.

The earlier four-file direct-entry candidate under `repo1/` and `repo2/` is
not equivalent to that chain: it bypasses Repo2's `Start-Fortis.ps1` /
`Common.ps1` preparation and watcher checks. The current dispatcher therefore
starts only the unchanged workers under `current/`; it does not use that
four-file candidate for Start.

Source provenance is **not evidence that the currently installed Windows
scripts or shortcut targets are identical**. The Script Center adapter source
now delegates to this tunnel mirror, but the Windows Script Center clone must
pull the paired commit before that behavior is active. The old
`script-control-center\launchers` copies are retained for historical/contract
tests only and are not an execution fallback. Do not change the running Windows
chain during source preparation.

## What stays outside Git / Windows Git clone

- Installed Windows Tunnel Client/Runtime binaries (`C:\Tools\tunnel-client\...`); they are transport-side Windows prerequisites, not Docker Linux binaries. Runtime v0.0.15 has documented ZIP/EXE hashes; full Client has a historical local hash but its Authenticode status was `NotSigned` and Repo2 still needs a startup hash pin.
- Separate G2 Windows tools (`C:\Tools\desktop-commander-runtime\node.exe` and `C:\Tools\desktop-commander\...`) remain outside this Repo1/Repo2 bundle; G2 is retired and not used, per owner confirmation on 2026-11-02. See the Defender/dependency inventory.
- Repo1 config/profile/key and runtime logs under the existing Windows owner folders.
- Repo2 profile, **separate** key/identity and runtime logs under the existing Windows owner folders.
- Windows .lnk, task/scheduler registration, ACLs, Docker container image/volume/config.

Do not copy profiles, secrets, logs or runtime key into Git. Existing hardcoded
Windows owner/pins/container identity are current-machine assumptions, not
portable defaults. Preserve the existing worker behavior: Repo2 `Start-Fortis.ps1`
may start the already-existing pinned Docker container when it is stopped, run
its guarded repair when the Guard explicitly recognizes factory-reset state,
and ensure the CI watcher; it does not create or stop the container. Repo1 uses
its own existing guarded quiet launcher. Do not add a new Tunnel registration,
Bridge/probe fallback, firewall/Defender changes, or container recreation.

## Paired delivery and Windows acceptance

1. In Docker, test and commit only the intended `runtime/windows-repo/` files
   and `runtime/README.md` in `tunnel`, and the Script Center adapters/resolver,
   paired updater, tests and documentation in `script-control-center`. Push both
   reviewed `main` commits. Do not push unrelated worktree changes.
2. On Windows, ensure both clean clones exist under `%USERPROFILE%\Repos`. Pull
   `tunnel` first and `script-control-center` second with `git pull --ff-only
   origin main`. The Script Center tool
   `tools/Update-Windows-ControlCenter.ps1 -Apply` also performs this ordered
   pair pull, verifies the manifest and all eight hashes, parses PowerShell,
   compiles WinForms, runs read-only Repo1/Repo2 Previews from the tunnel clone,
   and repairs the existing Script Catalog shortcut. It does not start workers
   or stop/restart Docker.
3. Before declaring the Windows installation baseline, inspect the actual
   running process/shortcut paths and the nonsecret installed-file inventory.
   `Preview-WindowsRepoInventory.ps1` compares known legacy candidate paths; it
   does not prove which shortcut/process is active. Do not read or copy keys.
4. In a normal **non-admin** PowerShell session, the Script Center `Repo1` and
   `Repo2` entries now call the workers under
   `%USERPROFILE%\Repos\tunnel\runtime\windows-repo\current`. The standalone
   `Invoke-FortisRepo.ps1 -Repo Repo1/Repo2 -Action Preview` remains available
   for manual source/Guard preflight. A failed preflight is **STOP**, not a
   reason to disable a pin/guard.
5. **Separate owner-approved maintenance window:** keep the existing
   `fortis-repo-test` container running. Do not stop/recreate the Docker
   container as part of switching the Windows tunnel processes; both tunnels
   depend on its pinned image/mounts/resources. Keep one working tunnel and an
   independent recovery route available. Stop only Repo1's existing Windows
   worker/runtime in Script Center, confirm it stopped, then Run Repo1. Confirm
   real MCP reads and response delivery. If it fails, stop only that failed
   instance and use the independent Repo1 recovery path. Never start a duplicate.
6. Only after Repo1 is proven, stop only Repo2 and Run Repo2 while Repo1 stays
   healthy. This dispatches the exact `current/Repo2-Worker.ps1` chain, including
   its `Start-Fortis.ps1` / `Common.ps1` preparation and Repo2 Guard. Validate
   the independent profile/browser route and real MCP response. Keep old scripts
   and shortcut backups for rollback.
7. Cold reboot, arbitrary startup order and graceful fallback still require
   separate acceptance. Docker has historically used `RestartPolicy=no`; do
   not promise automatic container restart. No guaranteed zero downtime: each
   individual tunnel profile has a brief connection interruption.

The paired source release does not by itself prove Windows PowerShell execution,
installed shortcut state or live reconnect. The eight mirrored scripts retain
their original bytes and embedded SHA/container pins; dependency updates require
reviewing and re-pinning exact bytes with new tests, not bypassing Guards.

See `docs/OPERATIONS.md`, `docs/agent-workflow/STATE.md`,
`docs/agent-workflow/TUNNEL_SECURITY_ISOLATION.md`, and the separate
`script-control-center/docs/GIT-WINDOWS-SOURCE-OF-TRUTH.md`.